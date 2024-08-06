from django.contrib import admin
from .models import Role, Department, Task, ExitInterview
from .forms import ExitInterviewForm

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Role, Department, Task, ExitInterview

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')
    search_fields = ('role_name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'hod_id')
    search_fields = ('department_name',)
    list_filter = ('hod_id',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_detail', 'department')
    search_fields = ('task_detail',)
    list_filter = ('department',)


class ExitInterviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'supervisor_name', 'initial_employment_date', 'last_date_of_employment', 'current_position', 'interview_date_time')
    list_filter = ('current_position', 'decision_time', 'specific_event', 'recommend', 'reapply', 'interview_date_time')
    search_fields = ('employee__username', 'supervisor_name', 'current_position')  # Use '__' for ForeignKey fields
    readonly_fields = ('interview_date_time',)

    fieldsets = (
        (None, {
            'fields': ('employee', 'supervisor_name', 'initial_employment_date', 'last_date_of_employment', 'current_position')
        }),
        ('Decision Details', {
            'fields': ('decision_time', 'decision_time_comments', 'reasons', 'reason_comments', 'specific_event', 'event_issue_comments', 'discuss_supervisor', 'discuss_supervisor_comments')
        }),
        ('Ratings', {
            'fields': ('training_quality', 'training_quality_comments', 'supervisor_relationship', 'supervisor_relationship_comments', 'employee_relationship', 'employee_relationship_comments', 'salary', 'salary_comments', 'workload', 'satisfaction', 'satisfaction_comments')
        }),
        ('Additional Feedback', {
            'fields': ('problems', 'problems_comments', 'enjoy_most', 'enjoy_least', 'recommend', 'recommend_comments', 'reapply', 'reapply_comments', 'additional_comments')
        }),
        ('Interview Details', {
            'fields': ('interviewer_name', 'interview_date_time')
        }),
    )
    form = ExitInterviewForm

admin.site.register(ExitInterview, ExitInterviewAdmin)
