from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Department, Task, EmployeeTask, ExitInterview, ExitProcess
from .forms import ExitInterviewForm


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff')
    list_filter   = ('role', 'department', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering      = ('username',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Department', {'fields': ('role', 'department')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Department', {'fields': ('role', 'department')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ('department_name', 'hod')
    search_fields = ('department_name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ('task_detail', 'department')
    search_fields = ('task_detail',)
    list_filter   = ('department',)


@admin.register(EmployeeTask)
class EmployeeTaskAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'task', 'status', 'assigned_at', 'completed_at')
    list_filter   = ('status', 'task__department')
    search_fields = ('employee__username', 'task__task_detail')
    readonly_fields = ('assigned_at', 'completed_at')


@admin.register(ExitProcess)
class ExitProcessAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'status', 'last_working_date', 'initiated_by', 'initiated_at')
    list_filter   = ('status',)
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('initiated_at', 'updated_at')
    fieldsets = (
        ('Process', {
            'fields': ('employee', 'initiated_by', 'status', 'last_working_date', 'notes')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'updated_at'),
        }),
    )


@admin.register(ExitInterview)
class ExitInterviewAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'current_position', 'last_date_of_employment', 'interview_date_time')
    list_filter   = ('decision_time', 'recommend', 'reapply')
    search_fields = ('employee__username', 'employee__first_name', 'supervisor_name')
    readonly_fields = ('interview_date_time', 'created_at', 'updated_at')
    date_hierarchy = 'interview_date_time'
    fieldsets = (
        ('Employee Info', {
            'fields': ('employee', 'supervisor_name', 'initial_employment_date',
                       'last_date_of_employment', 'current_position')
        }),
        ('Decision & Reason', {
            'fields': ('decision_time', 'decision_time_comments', 'reasons',
                       'reason_comments', 'specific_event', 'event_issue_comments',
                       'discuss_supervisor', 'discuss_supervisor_comments')
        }),
        ('Ratings', {
            'fields': ('training_quality', 'training_quality_comments',
                       'supervisor_relationship', 'supervisor_relationship_comments',
                       'employee_relationship', 'employee_relationship_comments',
                       'salary', 'salary_comments', 'workload',
                       'satisfaction', 'satisfaction_comments')
        }),
        ('Feedback', {
            'fields': ('problems', 'problems_comments', 'enjoy_most', 'enjoy_least',
                       'recommend', 'recommend_comments', 'reapply', 'reapply_comments',
                       'additional_comments')
        }),
        ('Sign-Off', {
            'fields': ('interviewer_name', 'interview_date_time', 'created_at', 'updated_at'),
        }),
    )
