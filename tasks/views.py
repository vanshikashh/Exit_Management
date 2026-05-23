from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .forms import ExitInterviewForm, InitiateExitForm
from .models import (
    ExitInterview, EmployeeTask, Task,
    ExitProcess, CustomUser, AuditLog, Department,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_hr(request):
    if not request.user.is_authenticated or not request.user.is_hr:
        return HttpResponseForbidden("Access restricted to HR staff.")
    return None

def _require_hr_or_hod(request):
    if not request.user.is_authenticated or (not request.user.is_hr and not request.user.is_hod):
        return HttpResponseForbidden("Access restricted to HR and HOD staff.")
    return None


def _annotate_processes(qs):
    """
    Single annotated query replacing N+1 loops.
    Computes task_total, task_done, has_interview per process in one DB hit.
    """
    return qs.annotate(
        task_total=Count('employee__assigned_tasks', distinct=True),
        task_done=Count(
            'employee__assigned_tasks',
            filter=Q(employee__assigned_tasks__status__in=['completed', 'waived']),
            distinct=True,
        ),
        has_interview=Count('employee__exit_interview', distinct=True),
    )


def _assign_all_tasks(employee):
    """
    On exit initiation, assign ALL tasks to the employee:
      - All standard tasks (HR-managed, apply to everyone)
      - All departmental tasks from ALL departments (each dept's HOD manages their own)
    """
    all_tasks = Task.objects.all()
    already   = set(EmployeeTask.objects
                    .filter(employee=employee)
                    .values_list('task_id', flat=True))
    new_tasks = [
        EmployeeTask(employee=employee, task=t)
        for t in all_tasks if t.pk not in already
    ]
    if new_tasks:
        EmployeeTask.objects.bulk_create(new_tasks, ignore_conflicts=True)
    return len(new_tasks)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return _role_redirect(user)
        messages.error(request, 'Invalid username or password.')
    return render(request, 'tasks/login.html')


def _role_redirect(user):
    # Superusers and staff go straight to Django admin
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    if user.is_hr:  return redirect('hr_dashboard')
    if user.is_hod: return redirect('hod_dashboard')
    return redirect('employee_status')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('employee_status')


# ─── Employee views ───────────────────────────────────────────────────────────

@login_required(login_url='login')
def employee_status(request):
    user = request.user
    # Superusers/staff don't belong on the employee status page
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    if user.is_hr:  return redirect('hr_dashboard')
    if user.is_hod: return redirect('hod_dashboard')

    process   = ExitProcess.objects.filter(employee=user).first()
    interview = ExitInterview.objects.filter(employee=user).first()

    # Group tasks by department for department-wise clearance view
    dept_clearance = []
    all_tasks      = []
    if process:
        all_tasks = (EmployeeTask.objects
                     .filter(employee=user)
                     .select_related('task', 'task__department')
                     .order_by('task__task_type', 'task__department__department_name', 'task__pk'))

        # Standard tasks — shown as "HR / General" block
        standard_tasks = [et for et in all_tasks if et.task.task_type == 'standard']
        if standard_tasks:
            done  = sum(1 for et in standard_tasks if et.status in ['completed', 'waived'])
            total = len(standard_tasks)
            dept_clearance.append({
                'dept_name': 'General / HR',
                'tasks':     standard_tasks,
                'done':      done,
                'total':     total,
                'cleared':   done == total,
                'pct':       round(done / total * 100) if total else 0,
            })

        # Departmental tasks — grouped by owning department
        dept_ids = (Task.objects
                    .filter(task_type='departmental')
                    .values_list('department_id', flat=True)
                    .distinct())
        for dept in Department.objects.filter(pk__in=dept_ids).order_by('department_name'):
            dept_tasks = [et for et in all_tasks
                          if et.task.task_type == 'departmental'
                          and et.task.department_id == dept.pk]
            if dept_tasks:
                done  = sum(1 for et in dept_tasks if et.status in ['completed', 'waived'])
                total = len(dept_tasks)
                dept_clearance.append({
                    'dept_name': dept.department_name,
                    'tasks':     dept_tasks,
                    'done':      done,
                    'total':     total,
                    'cleared':   done == total,
                    'pct':       round(done / total * 100) if total else 0,
                })

    total_tasks = len(all_tasks) if process else 0
    completed   = sum(1 for et in all_tasks if et.status in ['completed', 'waived']) if process else 0

    return render(request, 'tasks/employee_status.html', {
        'process':        process,
        'interview':      interview,
        'dept_clearance': dept_clearance,
        'completed':      completed,
        'total':          total_tasks,
        'progress_pct':   round(completed / total_tasks * 100) if total_tasks else 0,
    })


@login_required(login_url='login')
def exit_interview_form(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    if user.is_hr:  return redirect('hr_dashboard')
    if user.is_hod: return redirect('hod_dashboard')

    process = ExitProcess.objects.filter(employee=user).first()
    if not process:
        messages.warning(request, 'Your exit process has not been initiated. Please contact HR.')
        return redirect('employee_status')

    existing = ExitInterview.objects.filter(employee=user).first()

    if request.method == 'POST':
        if existing:
            messages.warning(request, 'Already submitted. Contact HR for corrections.')
            return redirect('form_success')
        form = ExitInterviewForm(request.POST)
        if form.is_valid():
            iv          = form.save(commit=False)
            iv.employee = user
            iv.save()
            old, new = process.refresh_status()
            AuditLog.log(
                actor=user, subject=user,
                action='INTERVIEW_SUBMITTED',
                detail=f"Exit interview submitted. Position: {iv.current_position}",
            )
            if old and new:
                AuditLog.log(
                    actor=user, subject=user,
                    action='EXIT_STATUS_CHANGED',
                    old_value=old, new_value=new,
                    detail="Auto-progressed after interview submission",
                )
            messages.success(request, 'Exit interview submitted successfully.')
            return redirect('form_success')
        messages.error(request, 'Please correct the errors below.')
    else:
        if existing:
            form = ExitInterviewForm(instance=existing)
            return render(request, 'tasks/exit_interview_form.html', {
                'form': form, 'already_submitted': True,
                'interview': existing, 'employee': user,
            })
        form = ExitInterviewForm()

    return render(request, 'tasks/exit_interview_form.html', {
        'form': form, 'already_submitted': False, 'employee': user,
    })


@login_required(login_url='login')
def form_success(request):
    interview = get_object_or_404(ExitInterview, employee=request.user)
    return render(request, 'tasks/form_success.html', {'interview': interview})


# ─── HOD dashboard ────────────────────────────────────────────────────────────

@login_required(login_url='login')
def hod_dashboard(request):
    """
    HOD sees ALL exiting employees, but ONLY the tasks that belong
    to their department. They are the ones who mark those tasks done.

    A Finance HOD sees Alice (Engineering), Bob (Finance), Cara (Engineering)
    — but only their Finance tasks for each person.

    HOD can update status of their dept's tasks.
    HOD cannot see or touch standard (HR) tasks or other depts' tasks.
    """
    denied = _require_hr_or_hod(request)
    if denied: return denied

    user = request.user

    # All active exit processes
    processes = (_annotate_processes(
        ExitProcess.objects
        .select_related('employee', 'employee__department')
        .order_by('-initiated_at')
    ))

    for p in processes:
        p.progress_pct = round(p.task_done / p.task_total * 100) if p.task_total else 0

        # For each process, get only this HOD's department tasks
        if user.is_hod:
            dept_tasks = (EmployeeTask.objects
                          .filter(employee=p.employee,
                                  task__task_type='departmental',
                                  task__department=user.department)
                          .select_related('task'))
            p.my_tasks   = list(dept_tasks)
            p.my_done    = sum(1 for et in p.my_tasks if et.status in ['completed', 'waived'])
            p.my_total   = len(p.my_tasks)
            p.my_pct     = round(p.my_done / p.my_total * 100) if p.my_total else 0
            p.my_cleared = p.my_done == p.my_total and p.my_total > 0

    return render(request, 'tasks/hod_dashboard.html', {
        'processes':  processes,
        'is_hod':     user.is_hod,
        'department': user.department if user.is_hod else None,
    })


@login_required(login_url='login')
def hod_update_task(request, task_id):
    """
    HOD updates a single task that belongs to their department.
    Only departmental tasks for their own department — enforced at DB level.
    """
    denied = _require_hr_or_hod(request)
    if denied: return denied

    et = get_object_or_404(
        EmployeeTask,
        pk=task_id,
        task__task_type='departmental',
    )

    # Enforce: HOD can only touch their own dept's tasks
    if request.user.is_hod and et.task.department != request.user.department:
        return HttpResponseForbidden("This task belongs to a different department.")

    if request.method == 'POST':
        new_status = request.POST.get('status', '')
        notes      = request.POST.get('notes', '')
        valid      = dict(EmployeeTask.STATUS_CHOICES).keys()

        if new_status in valid:
            old_status      = et.status
            et.status       = new_status
            et.notes        = notes
            if new_status == 'completed' and not et.completed_at:
                et.completed_at = timezone.now()
            elif new_status != 'completed':
                et.completed_at = None
            et.save()

            # Refresh the overall exit process status
            process = get_object_or_404(ExitProcess, employee=et.employee)
            old_p, new_p = process.refresh_status()

            AuditLog.log(
                actor=request.user, subject=et.employee,
                action='TASK_UPDATED',
                old_value=old_status, new_value=new_status,
                detail=(f"[{et.task.department}] {et.task.task_detail}"
                        + (f" — {notes}" if notes else "")),
            )
            if old_p and new_p:
                AuditLog.log(
                    actor=request.user, subject=et.employee,
                    action='EXIT_STATUS_CHANGED',
                    old_value=old_p, new_value=new_p,
                    detail=f"Auto-progressed after task '{et.task.task_detail}' marked {new_status}",
                )
            messages.success(request, 'Task updated.')

    return redirect('hod_dashboard')


# ─── HR views ─────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def hr_dashboard(request):
    denied = _require_hr(request)
    if denied: return denied

    processes = _annotate_processes(
        ExitProcess.objects
        .select_related('employee', 'employee__department', 'initiated_by')
        .order_by('-initiated_at')
    )
    for p in processes:
        p.progress_pct = round(p.task_done / p.task_total * 100) if p.task_total else 0

    total       = processes.count()
    cleared     = processes.filter(status='cleared').count()
    in_progress = processes.filter(status='in_progress').count()
    initiated   = processes.filter(status='initiated').count()

    interviews    = ExitInterview.objects.all()
    iv_total      = interviews.count()
    recommend_pct = reapply_pct = 0
    avg_ratings   = {}
    if iv_total:
        recommend_pct = round(interviews.filter(recommend=True).count() / iv_total * 100)
        reapply_pct   = round(interviews.filter(reapply=True).count()   / iv_total * 100)
        avg_ratings   = {
            k: round(v, 1) if v else '—'
            for k, v in interviews.aggregate(
                avg_training=Avg('training_quality'),
                avg_supervisor=Avg('supervisor_relationship'),
                avg_peers=Avg('employee_relationship'),
                avg_salary=Avg('salary'),
                avg_satisfaction=Avg('satisfaction'),
            ).items()
        }

    return render(request, 'tasks/hr_dashboard.html', {
        'processes':     processes,
        'total':         total,
        'cleared':       cleared,
        'in_progress':   in_progress,
        'initiated':     initiated,
        'iv_total':      iv_total,
        'recommend_pct': recommend_pct,
        'reapply_pct':   reapply_pct,
        'avg_ratings':   avg_ratings,
    })


@login_required(login_url='login')
def initiate_exit(request):
    denied = _require_hr(request)
    if denied: return denied

    if request.method == 'POST':
        form = InitiateExitForm(request.POST)
        if form.is_valid():
            employee          = form.cleaned_data['employee']
            last_working_date = form.cleaned_data['last_working_date']
            notes             = form.cleaned_data.get('notes', '')

            process, created = ExitProcess.objects.get_or_create(
                employee=employee,
                defaults={
                    'initiated_by':      request.user,
                    'last_working_date': last_working_date,
                    'notes':             notes,
                    'status':            'initiated',
                }
            )
            if created:
                assigned_count = _assign_all_tasks(employee)
                AuditLog.log(
                    actor=request.user, subject=employee,
                    action='EXIT_INITIATED',
                    new_value='initiated',
                    detail=(
                        f"Initiated by {request.user.get_full_name() or request.user.username}. "
                        f"Last working date: {last_working_date}. "
                        f"{assigned_count} tasks auto-assigned across all departments."
                    ),
                )
                messages.success(
                    request,
                    f"Exit process initiated for "
                    f"{employee.get_full_name() or employee.username}. "
                    f"{assigned_count} tasks assigned."
                )
            else:
                messages.warning(request, 'Exit process already exists for this employee.')
            return redirect('offboarding_checklist', user_id=employee.pk)
    else:
        form = InitiateExitForm()

    return render(request, 'tasks/initiate_exit.html', {'form': form})


@login_required(login_url='login')
def offboarding_checklist(request, user_id):
    """
    Full checklist for one employee — HR view.

    Shows all tasks grouped by:
      - Standard tasks (HR manages)
      - Department tasks (grouped by owning dept, updated by that dept's HOD)

    HR can update standard tasks here.
    HR can see dept tasks but cannot update them (HOD's responsibility).
    """
    denied = _require_hr_or_hod(request)
    if denied: return denied

    employee = get_object_or_404(CustomUser, pk=user_id)
    process  = get_object_or_404(ExitProcess, employee=employee)
    user     = request.user

    # Ensure all tasks are assigned (catches new tasks added after initiation)
    _assign_all_tasks(employee)

    # HR updating a standard task
    if request.method == 'POST' and user.is_hr:
        task_id    = request.POST.get('task_id')
        new_status = request.POST.get('status')
        notes      = request.POST.get('notes', '')
        valid      = dict(EmployeeTask.STATUS_CHOICES).keys()

        if task_id and new_status in valid:
            et = get_object_or_404(
                EmployeeTask, pk=task_id, employee=employee,
                task__task_type='standard',  # HR can ONLY update standard tasks here
            )
            old_status      = et.status
            et.status       = new_status
            et.notes        = notes
            if new_status == 'completed' and not et.completed_at:
                et.completed_at = timezone.now()
            elif new_status != 'completed':
                et.completed_at = None
            et.save()

            old_p, new_p = process.refresh_status()
            AuditLog.log(
                actor=user, subject=employee,
                action='TASK_UPDATED',
                old_value=old_status, new_value=new_status,
                detail=f"[Standard] {et.task.task_detail}" + (f" — {notes}" if notes else ""),
            )
            if old_p and new_p:
                AuditLog.log(
                    actor=user, subject=employee,
                    action='EXIT_STATUS_CHANGED',
                    old_value=old_p, new_value=new_p,
                    detail=f"Auto-progressed after standard task marked {new_status}",
                )
            messages.success(request, 'Task updated.')
        return redirect('offboarding_checklist', user_id=user_id)

    # Build task groups
    all_et = (EmployeeTask.objects
              .filter(employee=employee)
              .select_related('task', 'task__department')
              .order_by('task__task_type', 'task__department__department_name', 'task__pk'))

    standard_tasks = [et for et in all_et if et.task.task_type == 'standard']
    dept_groups    = {}
    for et in all_et:
        if et.task.task_type == 'departmental':
            d = et.task.department
            if d not in dept_groups:
                dept_groups[d] = []
            dept_groups[d].append(et)

    completed   = sum(1 for et in all_et if et.status in ['completed', 'waived'])
    total_tasks = len(list(all_et))
    interview   = ExitInterview.objects.filter(employee=employee).first()
    audit_trail = (AuditLog.objects
                   .filter(subject=employee)
                   .select_related('actor')
                   .order_by('-timestamp')[:20])

    return render(request, 'tasks/offboarding_checklist.html', {
        'employee':       employee,
        'process':        process,
        'standard_tasks': standard_tasks,
        'dept_groups':    dict(sorted(dept_groups.items(), key=lambda x: x[0].department_name)),
        'completed':      completed,
        'total_tasks':    total_tasks,
        'progress_pct':   round(completed / total_tasks * 100) if total_tasks else 0,
        'status_choices': EmployeeTask.STATUS_CHOICES,
        'interview':      interview,
        'audit_trail':    audit_trail,
    })


@login_required(login_url='login')
def audit_log_view(request):
    denied = _require_hr(request)
    if denied: return denied

    logs = (AuditLog.objects
            .select_related('actor', 'subject', 'subject__department')
            .order_by('-timestamp'))

    action_filter   = request.GET.get('action', '')
    employee_filter = request.GET.get('employee', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    if employee_filter:
        logs = logs.filter(
            Q(subject__username__icontains=employee_filter) |
            Q(subject__first_name__icontains=employee_filter) |
            Q(subject__last_name__icontains=employee_filter)
        )

    return render(request, 'tasks/audit_log.html', {
        'logs':            logs[:200],
        'action_choices':  AuditLog.ACTION_CHOICES,
        'action_filter':   action_filter,
        'employee_filter': employee_filter,
        'total_logs':      AuditLog.objects.count(),
    })
