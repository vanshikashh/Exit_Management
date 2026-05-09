from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings


class Department(models.Model):
    department_id = models.PositiveIntegerField(primary_key=True)
    department_name = models.CharField(max_length=255, default='Unknown Department')
    hod = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='headed_departments',
        verbose_name='Head of Department',
    )

    def __str__(self):
        return self.department_name

    class Meta:
        ordering = ['department_name']


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('HR', 'HR'),
        ('HOD', 'HOD'),
        ('Employee', 'Employee'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Employee')
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members',
    )
    groups = models.ManyToManyField(
        Group, verbose_name='groups', blank=True,
        related_name='custom_user_groups',
    )
    user_permissions = models.ManyToManyField(
        Permission, verbose_name='user permissions', blank=True,
        related_name='custom_user_permissions',
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_hr(self):
        return self.role == 'HR'

    @property
    def is_hod(self):
        return self.role == 'HOD'

    class Meta:
        app_label = 'tasks'
        permissions = [
            ("view_own_data", "Can view own data"),
            ("edit_own_data", "Can edit own data"),
            ("view_department_data", "Can view department data"),
            ("edit_department_data", "Can edit department data"),
            ("view_all_data", "Can view all data"),
            ("edit_all_data", "Can edit all data"),
            ("edit_own_credentials", "Can edit own credentials"),
            ("edit_own_formalities", "Can edit own formalities"),
        ]


class ExitProcess(models.Model):
    """
    Formally records that an employee has been initiated into the offboarding
    process by HR. Nothing else in the system is accessible to an employee
    until this record exists for them.

    This is the single source of truth for "is this person being offboarded?"
    """
    STATUS_CHOICES = [
        ('initiated',  'Initiated'),       # HR has started the process
        ('in_progress','In Progress'),     # employee has submitted interview
        ('pending_clearance', 'Pending Clearance'),  # tasks in progress
        ('cleared',    'Cleared'),         # all tasks + interview done
        ('closed',     'Closed'),          # fully offboarded
    ]

    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exit_process',
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='initiated_exits',
        verbose_name='Initiated by (HR)',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='initiated'
    )
    last_working_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exit Process'
        verbose_name_plural = 'Exit Processes'
        ordering = ['-initiated_at']

    def __str__(self):
        return f"{self.employee} — {self.get_status_display()}"

    def refresh_status(self):
        """
        Auto-compute status based on interview + task completion.
        Called whenever HR updates a checklist task.
        """
        has_interview = hasattr(self.employee, 'exit_interview')
        tasks = EmployeeTask.objects.filter(employee=self.employee)
        total = tasks.count()
        done = tasks.filter(status__in=['completed', 'waived']).count()
        all_tasks_done = (total > 0 and done == total)

        if has_interview and all_tasks_done:
            self.status = 'cleared'
        elif has_interview or done > 0:
            self.status = 'in_progress'
        else:
            self.status = 'initiated'
        self.save(update_fields=['status', 'updated_at'])


class Task(models.Model):
    """Reusable offboarding task template scoped to a department."""
    task_detail = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='tasks',
    )

    def __str__(self):
        return f"[{self.department}] {self.task_detail}"

    class Meta:
        ordering = ['department', 'pk']


class EmployeeTask(models.Model):
    """Tracks completion of one Task for one employee."""
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('waived',      'Waived'),
    ]
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='employee_assignments',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'task')
        ordering = ['task__department', 'task__pk']
        verbose_name = 'Employee Offboarding Task'
        verbose_name_plural = 'Employee Offboarding Tasks'

    def __str__(self):
        return f"{self.employee} — {self.task.task_detail} [{self.status}]"

    def mark_complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class ExitInterview(models.Model):
    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exit_interview',
    )
    supervisor_name = models.CharField(max_length=255)
    initial_employment_date = models.DateField()
    last_date_of_employment = models.DateField()
    current_position = models.CharField(max_length=255)

    DECISION_TIME_CHOICES = [
        ('6-9 months ago',   '6-9 months ago'),
        ('3-5 months ago',   '3-5 months ago'),
        ('1-2 months ago',   '1-2 months ago'),
        ('Less than a month','Less than a month'),
    ]
    decision_time = models.CharField(max_length=20, choices=DECISION_TIME_CHOICES)
    decision_time_comments = models.TextField(blank=True, null=True)

    REASON_CHOICES = [
        ('Salary', 'Salary'),
        ('Family Responsibilities', 'Family Responsibilities'),
        ('Job Advancement', 'Job Advancement'),
        ('Dissatisfied/Management', 'Dissatisfied/Management'),
        ('Personal', 'Personal'),
        ('Benefits', 'Benefits'),
        ('Return to last company', 'Return to last company'),
        ('Job Eliminated', 'Job Eliminated'),
        ('Relocation', 'Relocation'),
        ('Quality of work', 'Quality of work'),
        ('Health issue', 'Health issue'),
        ('Other', 'Other'),
    ]
    reasons = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_comments = models.TextField(blank=True, null=True)

    specific_event = models.BooleanField(default=False)
    event_issue_comments = models.TextField(blank=True, null=True)
    discuss_supervisor = models.BooleanField(default=False)
    discuss_supervisor_comments = models.TextField(blank=True, null=True)

    SCALE_CHOICES = [(i, str(i)) for i in range(1, 6)]

    training_quality = models.IntegerField(choices=SCALE_CHOICES, default=3)
    training_quality_comments = models.TextField(blank=True, null=True)
    supervisor_relationship = models.IntegerField(choices=SCALE_CHOICES, default=3)
    supervisor_relationship_comments = models.TextField(blank=True, null=True)
    employee_relationship = models.IntegerField(choices=SCALE_CHOICES, default=3)
    employee_relationship_comments = models.TextField(blank=True, null=True)
    salary = models.IntegerField(choices=SCALE_CHOICES, default=3)
    salary_comments = models.TextField(blank=True, null=True)
    workload = models.IntegerField(choices=SCALE_CHOICES, default=3)
    satisfaction = models.IntegerField(choices=SCALE_CHOICES, default=3)
    satisfaction_comments = models.TextField(blank=True, null=True)

    problems = models.BooleanField(default=False)
    problems_comments = models.TextField(blank=True, null=True)
    enjoy_most = models.TextField(blank=True, null=True)
    enjoy_least = models.TextField(blank=True, null=True)
    recommend = models.BooleanField(default=False)
    recommend_comments = models.TextField(blank=True, null=True)
    reapply = models.BooleanField(default=False)
    reapply_comments = models.TextField(blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)

    interviewer_name = models.CharField(max_length=255)
    interview_date_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exit Interview'
        verbose_name_plural = 'Exit Interviews'
        ordering = ['-interview_date_time']

    def __str__(self):
        name = self.employee.get_full_name() or self.employee.username
        return f"Exit Interview — {name} ({self.interview_date_time.date()})"

    @property
    def tenure_days(self):
        return (self.last_date_of_employment - self.initial_employment_date).days

    @property
    def avg_rating(self):
        fields = [
            self.training_quality, self.supervisor_relationship,
            self.employee_relationship, self.salary, self.satisfaction,
        ]
        return round(sum(fields) / len(fields), 1)
