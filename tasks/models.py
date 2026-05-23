from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings


class Department(models.Model):
    department_id   = models.PositiveIntegerField(primary_key=True)
    department_name = models.CharField(max_length=255)
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
        ('HR',       'HR'),
        ('HOD',      'HOD'),
        ('Employee', 'Employee'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Employee')
    # department = which dept this person BELONGS TO (for employees)
    # for HODs this is the dept they HEAD
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


class Task(models.Model):
    """
    Offboarding task template.

    TASK_TYPE governs who owns it and who can update it:

      'standard'     — applies to every exiting employee regardless of their dept.
                       Examples: submit exit form, return company ID card.
                       Managed by HR.

      'departmental' — scoped to a specific department.
                       Every exiting employee gets this task, but it is the
                       responsibility of THAT DEPARTMENT's HOD to mark it done.
                       Examples:
                         Finance dept  → clear dues, submit expense report
                         IT dept       → return laptop, revoke email/system access
                         HR dept       → collect ID card, complete exit interview
                         Legal dept    → sign NDA termination, return documents
    """
    TYPE_CHOICES = [
        ('standard',     'Standard (all employees, managed by HR)'),
        ('departmental', 'Departmental (managed by dept HOD)'),
    ]

    task_detail = models.CharField(max_length=255)
    task_type   = models.CharField(max_length=20, choices=TYPE_CHOICES, default='departmental')

    # For departmental tasks: which dept is responsible for this task.
    # For standard tasks: leave null — HR handles these.
    department  = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True, blank=True,
        help_text='Required for departmental tasks. Leave blank for standard tasks.',
    )

    def __str__(self):
        if self.task_type == 'standard':
            return f"[Standard] {self.task_detail}"
        return f"[{self.department}] {self.task_detail}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.task_type == 'departmental' and not self.department_id:
            raise ValidationError("Departmental tasks must have a department assigned.")
        if self.task_type == 'standard':
            self.department = None

    class Meta:
        ordering = ['task_type', 'department__department_name', 'pk']


class ExitProcess(models.Model):
    """
    Formally records that an employee is being offboarded.
    Single source of truth for "is this person in an exit process?"
    """
    STATUS_CHOICES = [
        ('initiated',   'Initiated'),
        ('in_progress', 'In Progress'),
        ('cleared',     'Cleared'),
        ('closed',      'Closed'),
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
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    last_working_date = models.DateField(null=True, blank=True)
    notes             = models.TextField(blank=True, null=True)
    initiated_at      = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Exit Process'
        verbose_name_plural = 'Exit Processes'
        ordering            = ['-initiated_at']

    def __str__(self):
        return f"{self.employee} — {self.get_status_display()}"

    def refresh_status(self):
        has_interview  = ExitInterview.objects.filter(employee=self.employee).exists()
        tasks          = EmployeeTask.objects.filter(employee=self.employee)
        total          = tasks.count()
        done           = tasks.filter(status__in=['completed', 'waived']).count()
        all_tasks_done = (total > 0 and done == total)

        if has_interview and all_tasks_done:
            new_status = 'cleared'
        elif has_interview or done > 0:
            new_status = 'in_progress'
        else:
            new_status = 'initiated'

        if new_status != self.status:
            old = self.status
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])
            return old, new_status
        return None, None


class EmployeeTask(models.Model):
    """
    One task assigned to one exiting employee.

    Edit permissions:
      - standard tasks   → only HR can update
      - departmental tasks → only the HOD of task.department can update
    """
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('waived',      'Waived'),
    ]

    employee     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
    )
    task         = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='employee_assignments',
    )
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes        = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'task')
        ordering        = ['task__task_type', 'task__department__department_name', 'task__pk']
        verbose_name    = 'Employee Offboarding Task'
        verbose_name_plural = 'Employee Offboarding Tasks'

    def __str__(self):
        return f"{self.employee} — {self.task.task_detail} [{self.status}]"

    def can_be_edited_by(self, user):
        """
        Returns True if the given user has permission to update this task.
          - HR can edit standard tasks
          - HOD can edit departmental tasks owned by their department
        """
        if user.is_hr and self.task.task_type == 'standard':
            return True
        if user.is_hod and self.task.task_type == 'departmental':
            return self.task.department == user.department
        return False

    def mark_complete(self):
        self.status      = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class ExitInterview(models.Model):
    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exit_interview',
    )
    supervisor_name          = models.CharField(max_length=255)
    initial_employment_date  = models.DateField()
    last_date_of_employment  = models.DateField()
    current_position         = models.CharField(max_length=255)

    DECISION_TIME_CHOICES = [
        ('6-9 months ago',    '6-9 months ago'),
        ('3-5 months ago',    '3-5 months ago'),
        ('1-2 months ago',    '1-2 months ago'),
        ('Less than a month', 'Less than a month'),
    ]
    decision_time          = models.CharField(max_length=20, choices=DECISION_TIME_CHOICES)
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
    reasons        = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_comments = models.TextField(blank=True, null=True)

    specific_event              = models.BooleanField(default=False)
    event_issue_comments        = models.TextField(blank=True, null=True)
    discuss_supervisor          = models.BooleanField(default=False)
    discuss_supervisor_comments = models.TextField(blank=True, null=True)

    SCALE_CHOICES = [(i, str(i)) for i in range(1, 6)]

    training_quality                  = models.IntegerField(choices=SCALE_CHOICES, default=3)
    training_quality_comments         = models.TextField(blank=True, null=True)
    supervisor_relationship           = models.IntegerField(choices=SCALE_CHOICES, default=3)
    supervisor_relationship_comments  = models.TextField(blank=True, null=True)
    employee_relationship             = models.IntegerField(choices=SCALE_CHOICES, default=3)
    employee_relationship_comments    = models.TextField(blank=True, null=True)
    salary                            = models.IntegerField(choices=SCALE_CHOICES, default=3)
    salary_comments                   = models.TextField(blank=True, null=True)
    workload                          = models.IntegerField(choices=SCALE_CHOICES, default=3)
    satisfaction                      = models.IntegerField(choices=SCALE_CHOICES, default=3)
    satisfaction_comments             = models.TextField(blank=True, null=True)

    problems          = models.BooleanField(default=False)
    problems_comments = models.TextField(blank=True, null=True)
    enjoy_most        = models.TextField(blank=True, null=True)
    enjoy_least       = models.TextField(blank=True, null=True)
    recommend         = models.BooleanField(default=False)
    recommend_comments = models.TextField(blank=True, null=True)
    reapply           = models.BooleanField(default=False)
    reapply_comments  = models.TextField(blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)

    interviewer_name    = models.CharField(max_length=255)
    interview_date_time = models.DateTimeField(default=timezone.now)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Exit Interview'
        verbose_name_plural = 'Exit Interviews'
        ordering            = ['-interview_date_time']

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


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('EXIT_INITIATED',      'Exit Initiated'),
        ('EXIT_STATUS_CHANGED', 'Exit Status Changed'),
        ('TASK_UPDATED',        'Task Updated'),
        ('INTERVIEW_SUBMITTED', 'Interview Submitted'),
        ('PROCESS_CLOSED',      'Process Closed'),
    ]

    actor     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='audit_actions',
    )
    subject   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='audit_events',
    )
    action    = models.CharField(max_length=30, choices=ACTION_CHOICES)
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)
    detail    = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-timestamp']
        verbose_name        = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log'

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor} → {self.action} on {self.subject}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    @classmethod
    def log(cls, actor, subject, action, old_value=None, new_value=None, detail=None):
        return cls.objects.create(
            actor=actor, subject=subject, action=action,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            detail=detail,
        )
