from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings

class Role(models.Model):
    role_id = models.PositiveIntegerField(primary_key=True)
    role_name = models.CharField(max_length=255, default='Unknown Role')

class Department(models.Model):
    department_id = models.PositiveIntegerField(primary_key=True)
    department_name = models.CharField(max_length=255, default='Unknown Department')
    hod_id = models.PositiveIntegerField(default=0)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('HR', 'HR'),
        ('HOD', 'HOD'),
        ('Employee', 'Employee'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, default=1)
    
    # Define related_name to avoid conflicts
    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True, related_name='custom_user_groups')
    user_permissions = models.ManyToManyField(Permission, verbose_name='user permissions', blank=True, related_name='custom_user_permissions')

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

class Task(models.Model):
    task_id = models.PositiveIntegerField(primary_key=True)
    task_detail = models.CharField(max_length=255, default='No details provided')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.task_detail

class ExitInterview(models.Model):
    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    supervisor_name = models.CharField(max_length=255)
    initial_employment_date = models.DateField()
    last_date_of_employment = models.DateField()
    current_position = models.CharField(max_length=255)
    
    DECISION_TIME_CHOICES = [
        ('6-9 months ago', '6-9 months ago'),
        ('3-5 months ago', '3-5 months ago'),
        ('1-2 months ago', '1-2 months ago'),
        ('Less than a month', 'Less than a month'),
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

    training_quality = models.IntegerField(choices=SCALE_CHOICES, default=1)
    training_quality_comments = models.TextField(blank=True, null=True)
    
    supervisor_relationship = models.IntegerField(choices=SCALE_CHOICES, default=1)
    supervisor_relationship_comments = models.TextField(blank=True, null=True)
    
    employee_relationship = models.IntegerField(choices=SCALE_CHOICES, default=1)
    employee_relationship_comments = models.TextField(blank=True, null=True)
    
    salary = models.IntegerField(choices=SCALE_CHOICES, default=1)
    salary_comments = models.TextField(blank=True, null=True)
    
    workload = models.IntegerField(choices=SCALE_CHOICES, default=1)
    
    satisfaction = models.IntegerField(choices=SCALE_CHOICES, default=1)
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

    def __str__(self):
        return f"Exit Interview for {self.employee.username} on {self.interview_date_time}"
