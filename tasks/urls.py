from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Employee
    path('my-status/',              views.employee_status,     name='employee_status'),
    path('my-tasks/',               views.employee_tasks,      name='employee_tasks'),
    path('exit-interview/',         views.exit_interview_form, name='exit_interview_form'),
    path('exit-interview/success/', views.form_success,        name='form_success'),

    # HOD
    path('hod/dashboard/',                    views.hod_dashboard,      name='hod_dashboard'),
    path('hod/task/<int:task_id>/',           views.hod_update_task,    name='hod_update_task'),
    path('hod/employee/<int:user_id>/tasks/', views.hod_employee_tasks, name='hod_employee_tasks'),

    # HR
    path('hr/dashboard/',                views.hr_dashboard,          name='hr_dashboard'),
    path('hr/initiate/',                 views.initiate_exit,         name='initiate_exit'),
    path('hr/checklist/<int:user_id>/',  views.offboarding_checklist, name='offboarding_checklist'),
    path('hr/audit-log/',                views.audit_log_view,        name='audit_log'),
]
