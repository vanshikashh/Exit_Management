from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .forms import ExitInterviewForm, InitiateExitForm
from .models import ExitInterview, EmployeeTask, Task, ExitProcess, CustomUser


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _require_hr(request):
    if not request.user.is_authenticated or not request.user.is_hr:
        return HttpResponseForbidden("Access restricted to HR staff.")
    return None

def _require_hr_or_hod(request):
    if not request.user.is_authenticated or (not request.user.is_hr and not request.user.is_hod):
        return HttpResponseForbidden("Access restricted to HR and HOD staff.")
    return None


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return _role_redirect(user)
        messages.error(request, 'Invalid username or password.')

    return render(request, 'tasks/login.html')


def _role_redirect(user):
    """Send each role to their home page after login."""
    if user.is_hr:
        return redirect('hr_dashboard')
    if user.is_hod:
        return redirect('hod_dashboard')
    return redirect('employee_status')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('employee_status')


# ─── Employee views ───────────────────────────────────────────────────────────

@login_required(login_url='login')
def employee_status(request):
    """
    Employee home page — shows their full offboarding status at a glance:
    - Has the process been initiated by HR?
    - Have they submitted the exit interview?
    - Which tasks are pending / done?
    """
    user = request.user

    # Block HR and HOD from this page
    if user.is_hr:
        return redirect('hr_dashboard')
    if user.is_hod:
        return redirect('hod_dashboard')

    process = ExitProcess.objects.filter(employee=user).first()
    interview = ExitInterview.objects.filter(employee=user).first()
    tasks = (EmployeeTask.objects
             .filter(employee=user)
             .select_related('task', 'task__department')
             .order_by('task__department__department_name', 'task__pk'))

    completed = tasks.filter(status__in=['completed', 'waived']).count()
    total = tasks.count()

    return render(request, 'tasks/employee_status.html', {
        'process': process,
        'interview': interview,
        'tasks': tasks,
        'completed': completed,
        'total': total,
        'progress_pct': round(completed / total * 100) if total else 0,
    })


@login_required(login_url='login')
def exit_interview_form(request):
    user = request.user
    if user.is_hr:
        return redirect('hr_dashboard')
    if user.is_hod:
        return redirect('hod_dashboard')

    # Must be initiated by HR first
    process = ExitProcess.objects.filter(employee=user).first()
    if not process:
        messages.warning(request, 'Your exit process has not been initiated yet. Please contact HR.')
        return redirect('employee_status')

    existing = ExitInterview.objects.filter(employee=user).first()

    if request.method == 'POST':
        if existing:
            messages.warning(request, 'Already submitted. Contact HR for corrections.')
            return redirect('form_success')
        form = ExitInterviewForm(request.POST)
        if form.is_valid():
            iv = form.save(commit=False)
            iv.employee = user
            iv.save()
            process.refresh_status()
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


# ─── HOD views ────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def hod_dashboard(request):
    """
    HOD sees only employees in their department who are being offboarded.
    They can view checklist progress but cannot modify tasks or initiate exits.
    """
    denied = _require_hr_or_hod(request)
    if denied:
        return denied

    user = request.user

    # HOD: filter to own department. HR visiting this page sees all.
    if user.is_hod:
        processes = (ExitProcess.objects
                     .filter(employee__department=user.department)
                     .select_related('employee', 'employee__department')
                     .order_by('-initiated_at'))
    else:
        processes = (ExitProcess.objects
                     .select_related('employee', 'employee__department')
                     .order_by('-initiated_at'))

    # Annotate each process with task completion counts
    for p in processes:
        tasks = EmployeeTask.objects.filter(employee=p.employee)
        p.task_total = tasks.count()
        p.task_done = tasks.filter(status__in=['completed', 'waived']).count()
        p.has_interview = hasattr(p.employee, 'exit_interview')
        p.progress_pct = round(p.task_done / p.task_total * 100) if p.task_total else 0

    return render(request, 'tasks/hod_dashboard.html', {
        'processes': processes,
        'is_hod': user.is_hod,
        'department': user.department if user.is_hod else None,
    })


# ─── HR views ────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def hr_dashboard(request):
    """HR home — aggregate stats + list of all active exit processes."""
    denied = _require_hr(request)
    if denied:
        return denied

    processes = (ExitProcess.objects
                 .select_related('employee', 'employee__department', 'initiated_by')
                 .order_by('-initiated_at'))

    # Annotate
    for p in processes:
        tasks = EmployeeTask.objects.filter(employee=p.employee)
        p.task_total = tasks.count()
        p.task_done  = tasks.filter(status__in=['completed', 'waived']).count()
        p.has_interview = hasattr(p.employee, 'exit_interview')
        p.progress_pct  = round(p.task_done / p.task_total * 100) if p.task_total else 0

    total = processes.count()
    cleared = processes.filter(status='cleared').count()
    in_progress = processes.filter(status='in_progress').count()
    initiated = processes.filter(status='initiated').count()

    # Interview aggregate stats
    interviews = ExitInterview.objects.all()
    iv_total = interviews.count()
    recommend_pct = reapply_pct = 0
    avg_ratings = {}
    if iv_total:
        recommend_pct = round(interviews.filter(recommend=True).count() / iv_total * 100)
        reapply_pct   = round(interviews.filter(reapply=True).count()   / iv_total * 100)
        avg_ratings   = interviews.aggregate(
            avg_training=Avg('training_quality'),
            avg_supervisor=Avg('supervisor_relationship'),
            avg_peers=Avg('employee_relationship'),
            avg_salary=Avg('salary'),
            avg_satisfaction=Avg('satisfaction'),
        )
        avg_ratings = {k: round(v, 1) if v else '—' for k, v in avg_ratings.items()}

    return render(request, 'tasks/hr_dashboard.html', {
        'processes': processes,
        'total': total,
        'cleared': cleared,
        'in_progress': in_progress,
        'initiated': initiated,
        'iv_total': iv_total,
        'recommend_pct': recommend_pct,
        'reapply_pct': reapply_pct,
        'avg_ratings': avg_ratings,
    })


@login_required(login_url='login')
def initiate_exit(request):
    """HR initiates the offboarding process for an employee."""
    denied = _require_hr(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = InitiateExitForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            last_working_date = form.cleaned_data['last_working_date']
            notes = form.cleaned_data.get('notes', '')

            process, created = ExitProcess.objects.get_or_create(
                employee=employee,
                defaults={
                    'initiated_by': request.user,
                    'last_working_date': last_working_date,
                    'notes': notes,
                    'status': 'initiated',
                }
            )
            if created:
                # Auto-assign all department tasks immediately
                if employee.department:
                    dept_tasks = Task.objects.filter(department=employee.department)
                    EmployeeTask.objects.bulk_create(
                        [EmployeeTask(employee=employee, task=t) for t in dept_tasks],
                        ignore_conflicts=True,
                    )
                messages.success(
                    request,
                    f"Exit process initiated for {employee.get_full_name() or employee.username}."
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
    HR (and HOD read-only) view of one employee's offboarding checklist.
    HR can update task statuses. HOD can only view.
    """
    denied = _require_hr_or_hod(request)
    if denied:
        return denied

    employee = get_object_or_404(CustomUser, pk=user_id)
    process  = get_object_or_404(ExitProcess, employee=employee)

    # HOD can only see employees in their department
    if request.user.is_hod and employee.department != request.user.department:
        return HttpResponseForbidden("This employee is not in your department.")

    # Bulk-assign any new department tasks not yet assigned
    if employee.department:
        dept_tasks = Task.objects.filter(department=employee.department)
        already    = set(EmployeeTask.objects.filter(employee=employee)
                         .values_list('task_id', flat=True))
        new_tasks  = [EmployeeTask(employee=employee, task=t)
                      for t in dept_tasks if t.pk not in already]
        if new_tasks:
            EmployeeTask.objects.bulk_create(new_tasks, ignore_conflicts=True)

    if request.method == 'POST' and request.user.is_hr:
        task_id    = request.POST.get('task_id')
        new_status = request.POST.get('status')
        notes      = request.POST.get('notes', '')
        valid      = dict(EmployeeTask.STATUS_CHOICES).keys()

        if task_id and new_status in valid:
            et = get_object_or_404(EmployeeTask, pk=task_id, employee=employee)
            et.status = new_status
            et.notes  = notes
            if new_status == 'completed' and not et.completed_at:
                et.completed_at = timezone.now()
            elif new_status != 'completed':
                et.completed_at = None
            et.save()
            process.refresh_status()
            messages.success(request, 'Task updated.')
        return redirect('offboarding_checklist', user_id=user_id)

    assigned = (EmployeeTask.objects
                .filter(employee=employee)
                .select_related('task', 'task__department')
                .order_by('task__department__department_name', 'task__pk'))

    completed   = assigned.filter(status__in=['completed', 'waived']).count()
    total_tasks = assigned.count()
    interview   = ExitInterview.objects.filter(employee=employee).first()

    return render(request, 'tasks/offboarding_checklist.html', {
        'employee':      employee,
        'process':       process,
        'assigned_tasks': assigned,
        'completed':     completed,
        'total_tasks':   total_tasks,
        'progress_pct':  round(completed / total_tasks * 100) if total_tasks else 0,
        'status_choices': EmployeeTask.STATUS_CHOICES,
        'interview':     interview,
        'can_edit':      request.user.is_hr,
    })
