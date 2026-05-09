from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import CustomUser, Department, Task, EmployeeTask, ExitInterview, ExitProcess


# ─── Factories ────────────────────────────────────────────────────────────────

def make_department(dept_id=1, name='Engineering'):
    return Department.objects.create(department_id=dept_id, department_name=name)

def make_user(username='alice', role='Employee', department=None, **kwargs):
    return CustomUser.objects.create_user(
        username=username, password='testpass123',
        role=role, department=department, **kwargs
    )

def make_process(employee, initiated_by, **kwargs):
    defaults = dict(status='initiated', last_working_date=date(2024, 8, 31))
    defaults.update(kwargs)
    return ExitProcess.objects.create(employee=employee, initiated_by=initiated_by, **defaults)

def make_interview(employee, **kwargs):
    defaults = dict(
        supervisor_name='Bob Manager',
        initial_employment_date=date(2022, 1, 1),
        last_date_of_employment=date(2024, 6, 30),
        current_position='Software Engineer',
        decision_time='1-2 months ago',
        reasons='Salary',
        training_quality=4, supervisor_relationship=3,
        employee_relationship=4, salary=2, workload=3, satisfaction=3,
        interviewer_name='HR Person',
        interview_date_time=timezone.now(),
    )
    defaults.update(kwargs)
    return ExitInterview.objects.create(employee=employee, **defaults)


# ─── Model tests ──────────────────────────────────────────────────────────────

class DepartmentModelTest(TestCase):
    def test_str(self):
        self.assertEqual(str(make_department()), 'Engineering')


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.dept = make_department()

    def test_str_with_full_name(self):
        user = make_user(department=self.dept, first_name='Alice', last_name='Smith')
        self.assertIn('Alice Smith', str(user))

    def test_str_fallback_to_username(self):
        self.assertIn('alice', str(make_user(department=self.dept)))

    def test_is_hr(self):
        self.assertTrue(make_user(username='hr1', role='HR', department=self.dept).is_hr)

    def test_is_hod(self):
        self.assertTrue(make_user(username='hod1', role='HOD', department=self.dept).is_hod)

    def test_employee_is_neither(self):
        emp = make_user(department=self.dept)
        self.assertFalse(emp.is_hr)
        self.assertFalse(emp.is_hod)


class ExitProcessModelTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1', role='HR',      department=self.dept)
        self.emp  = make_user(username='emp1', role='Employee', department=self.dept)

    def test_str(self):
        p = make_process(self.emp, self.hr)
        self.assertIn('emp1', str(p))

    def test_refresh_status_no_interview_no_tasks(self):
        p = make_process(self.emp, self.hr)
        p.refresh_status()
        self.assertEqual(p.status, 'initiated')

    def test_refresh_status_interview_only(self):
        p = make_process(self.emp, self.hr)
        make_interview(self.emp)
        p.refresh_status()
        self.assertEqual(p.status, 'in_progress')

    def test_refresh_status_all_done_marks_cleared(self):
        p = make_process(self.emp, self.hr)
        make_interview(self.emp)
        task = Task.objects.create(task_detail='Return laptop', department=self.dept)
        et = EmployeeTask.objects.create(employee=self.emp, task=task)
        et.mark_complete()
        p.refresh_status()
        self.assertEqual(p.status, 'cleared')


class ExitInterviewModelTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.user = make_user(department=self.dept)

    def test_tenure_days(self):
        iv = make_interview(self.user,
            initial_employment_date=date(2020, 1, 1),
            last_date_of_employment=date(2022, 1, 1))
        self.assertEqual(iv.tenure_days, 731)

    def test_avg_rating(self):
        iv = make_interview(self.user,
            training_quality=5, supervisor_relationship=4,
            employee_relationship=3, salary=2, satisfaction=1)
        self.assertEqual(iv.avg_rating, 3.0)


class EmployeeTaskModelTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.user = make_user(department=self.dept)
        self.task = Task.objects.create(task_detail='Return laptop', department=self.dept)

    def test_mark_complete(self):
        et = EmployeeTask.objects.create(employee=self.user, task=self.task)
        et.mark_complete()
        self.assertEqual(et.status, 'completed')
        self.assertIsNotNone(et.completed_at)

    def test_unique_together(self):
        EmployeeTask.objects.create(employee=self.user, task=self.task)
        with self.assertRaises(Exception):
            EmployeeTask.objects.create(employee=self.user, task=self.task)


class TaskModelTest(TestCase):
    def test_auto_pk_and_str(self):
        dept = make_department()
        t = Task.objects.create(task_detail='Hand over badge', department=dept)
        self.assertIsNotNone(t.pk)
        self.assertIn('Engineering', str(t))


# ─── Auth view tests ──────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.dept = make_department()

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_valid_employee_login_redirects_to_status(self):
        make_user(department=self.dept)
        r = self.client.post(reverse('login'), {'username': 'alice', 'password': 'testpass123'})
        self.assertRedirects(r, reverse('employee_status'))

    def test_valid_hr_login_redirects_to_hr_dashboard(self):
        make_user(username='hr1', role='HR', department=self.dept)
        r = self.client.post(reverse('login'), {'username': 'hr1', 'password': 'testpass123'})
        self.assertRedirects(r, reverse('hr_dashboard'))

    def test_valid_hod_login_redirects_to_hod_dashboard(self):
        make_user(username='hod1', role='HOD', department=self.dept)
        r = self.client.post(reverse('login'), {'username': 'hod1', 'password': 'testpass123'})
        self.assertRedirects(r, reverse('hod_dashboard'))

    def test_invalid_login_shows_error(self):
        make_user(department=self.dept)
        r = self.client.post(reverse('login'), {'username': 'alice', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid username')

    def test_get_logout_does_not_log_out(self):
        make_user(department=self.dept)
        self.client.login(username='alice', password='testpass123')
        self.client.get(reverse('logout'))
        r = self.client.get(reverse('employee_status'))
        self.assertEqual(r.status_code, 200)

    def test_post_logout_redirects_to_login(self):
        make_user(department=self.dept)
        self.client.login(username='alice', password='testpass123')
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'))


# ─── Employee status view tests ───────────────────────────────────────────────

class EmployeeStatusViewTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1',  role='HR',       department=self.dept)
        self.emp  = make_user(username='alice', role='Employee', department=self.dept)
        self.client.login(username='alice', password='testpass123')

    def test_status_page_renders(self):
        r = self.client.get(reverse('employee_status'))
        self.assertEqual(r.status_code, 200)

    def test_shows_not_initiated_message_when_no_process(self):
        r = self.client.get(reverse('employee_status'))
        self.assertIsNone(r.context['process'])

    def test_shows_process_when_initiated(self):
        p = make_process(self.emp, self.hr)
        r = self.client.get(reverse('employee_status'))
        self.assertEqual(r.context['process'], p)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        r = self.client.get(reverse('employee_status'))
        self.assertRedirects(r, '/login/?next=/my-status/')

    def test_hr_redirected_to_hr_dashboard(self):
        self.client.login(username='hr1', password='testpass123')
        r = self.client.get(reverse('employee_status'))
        self.assertRedirects(r, reverse('hr_dashboard'))


# ─── Exit interview view tests ────────────────────────────────────────────────

class ExitInterviewViewTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1',  role='HR',       department=self.dept)
        self.emp  = make_user(username='alice', role='Employee', department=self.dept)
        self.client.login(username='alice', password='testpass123')

    def _post_data(self, **overrides):
        data = {
            'supervisor_name': 'Bob',
            'initial_employment_date': '2022-01-01',
            'last_date_of_employment': '2024-06-30',
            'current_position': 'Engineer',
            'decision_time': '1-2 months ago',
            'reasons': 'Salary',
            'training_quality': 4, 'supervisor_relationship': 3,
            'employee_relationship': 4, 'salary': 2,
            'workload': 3, 'satisfaction': 3,
            'interviewer_name': 'HR Person',
            'interview_date_time': '2024-07-01T10:00',
        }
        data.update(overrides)
        return data

    def test_form_blocked_without_process(self):
        """Employee cannot access interview form if HR hasn't initiated exit."""
        r = self.client.get(reverse('exit_interview_form'))
        self.assertRedirects(r, reverse('employee_status'))

    def test_form_accessible_with_process(self):
        make_process(self.emp, self.hr)
        r = self.client.get(reverse('exit_interview_form'))
        self.assertEqual(r.status_code, 200)

    def test_valid_submission_creates_record(self):
        make_process(self.emp, self.hr)
        r = self.client.post(reverse('exit_interview_form'), self._post_data())
        self.assertRedirects(r, reverse('form_success'))
        self.assertTrue(ExitInterview.objects.filter(employee=self.emp).exists())

    def test_submission_updates_process_status(self):
        p = make_process(self.emp, self.hr)
        self.client.post(reverse('exit_interview_form'), self._post_data())
        p.refresh_from_db()
        self.assertEqual(p.status, 'in_progress')

    def test_duplicate_submission_blocked(self):
        make_process(self.emp, self.hr)
        make_interview(self.emp)
        self.client.post(reverse('exit_interview_form'), self._post_data())
        self.assertEqual(ExitInterview.objects.filter(employee=self.emp).count(), 1)

    def test_invalid_dates_rejected(self):
        make_process(self.emp, self.hr)
        r = self.client.post(reverse('exit_interview_form'), self._post_data(
            initial_employment_date='2024-06-30',
            last_date_of_employment='2022-01-01',
        ))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(ExitInterview.objects.filter(employee=self.emp).exists())


# ─── HR view tests ────────────────────────────────────────────────────────────

class HRDashboardTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1',  role='HR',       department=self.dept)
        self.emp  = make_user(username='alice', role='Employee', department=self.dept)

    def test_hr_can_access(self):
        self.client.login(username='hr1', password='testpass123')
        self.assertEqual(self.client.get(reverse('hr_dashboard')).status_code, 200)

    def test_employee_is_forbidden(self):
        self.client.login(username='alice', password='testpass123')
        self.assertEqual(self.client.get(reverse('hr_dashboard')).status_code, 403)

    def test_unauthenticated_redirects(self):
        r = self.client.get(reverse('hr_dashboard'))
        self.assertRedirects(r, '/login/?next=/hr/dashboard/')

    def test_stats_in_context(self):
        self.client.login(username='hr1', password='testpass123')
        make_process(self.emp, self.hr)
        r = self.client.get(reverse('hr_dashboard'))
        self.assertEqual(r.context['total'], 1)
        self.assertEqual(r.context['initiated'], 1)


class InitiateExitViewTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1',  role='HR',       department=self.dept)
        self.emp  = make_user(username='alice', role='Employee', department=self.dept)
        self.client.login(username='hr1', password='testpass123')

    def test_initiate_page_renders(self):
        self.assertEqual(self.client.get(reverse('initiate_exit')).status_code, 200)

    def test_initiating_creates_process(self):
        self.client.post(reverse('initiate_exit'), {
            'employee': self.emp.pk,
            'last_working_date': '2024-08-31',
            'notes': 'Test exit',
        })
        self.assertTrue(ExitProcess.objects.filter(employee=self.emp).exists())

    def test_initiating_auto_assigns_dept_tasks(self):
        Task.objects.create(task_detail='Return laptop', department=self.dept)
        Task.objects.create(task_detail='Return badge',  department=self.dept)
        self.client.post(reverse('initiate_exit'), {
            'employee': self.emp.pk,
            'last_working_date': '2024-08-31',
        })
        self.assertEqual(EmployeeTask.objects.filter(employee=self.emp).count(), 2)

    def test_employee_cannot_access(self):
        self.client.login(username='alice', password='testpass123')
        r = self.client.get(reverse('initiate_exit'))
        self.assertEqual(r.status_code, 403)


# ─── HOD view tests ───────────────────────────────────────────────────────────

class HODDashboardTest(TestCase):
    def setUp(self):
        self.dept1 = make_department(dept_id=1, name='Engineering')
        self.dept2 = make_department(dept_id=2, name='Finance')
        self.hr    = make_user(username='hr1',  role='HR',       department=self.dept1)
        self.hod   = make_user(username='hod1', role='HOD',      department=self.dept1)
        self.emp1  = make_user(username='emp1', role='Employee',  department=self.dept1)
        self.emp2  = make_user(username='emp2', role='Employee',  department=self.dept2)

    def test_hod_can_access(self):
        self.client.login(username='hod1', password='testpass123')
        self.assertEqual(self.client.get(reverse('hod_dashboard')).status_code, 200)

    def test_employee_is_forbidden(self):
        self.client.login(username='emp1', password='testpass123')
        self.assertEqual(self.client.get(reverse('hod_dashboard')).status_code, 403)

    def test_hod_only_sees_own_dept(self):
        make_process(self.emp1, self.hr)
        make_process(self.emp2, self.hr)
        self.client.login(username='hod1', password='testpass123')
        r = self.client.get(reverse('hod_dashboard'))
        processes = list(r.context['processes'])
        employees = [p.employee for p in processes]
        self.assertIn(self.emp1, employees)
        self.assertNotIn(self.emp2, employees)


# ─── Checklist view tests ─────────────────────────────────────────────────────

class OffboardingChecklistTest(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.hr   = make_user(username='hr1',  role='HR',       department=self.dept)
        self.hod  = make_user(username='hod1', role='HOD',      department=self.dept)
        self.emp  = make_user(username='alice', role='Employee', department=self.dept)
        self.task = Task.objects.create(task_detail='Return laptop', department=self.dept)
        self.process = make_process(self.emp, self.hr)

    def test_auto_creates_tasks_on_first_visit(self):
        self.client.login(username='hr1', password='testpass123')
        self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        self.assertEqual(EmployeeTask.objects.filter(employee=self.emp).count(), 1)

    def test_no_duplicate_tasks_on_revisit(self):
        self.client.login(username='hr1', password='testpass123')
        url = reverse('offboarding_checklist', args=[self.emp.pk])
        self.client.get(url)
        self.client.get(url)
        self.assertEqual(EmployeeTask.objects.filter(employee=self.emp).count(), 1)

    def test_hr_can_update_task(self):
        self.client.login(username='hr1', password='testpass123')
        self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        et = EmployeeTask.objects.get(employee=self.emp, task=self.task)
        self.client.post(
            reverse('offboarding_checklist', args=[self.emp.pk]),
            {'task_id': et.pk, 'status': 'completed', 'notes': 'Done'},
        )
        et.refresh_from_db()
        self.assertEqual(et.status, 'completed')
        self.assertIsNotNone(et.completed_at)

    def test_completed_at_cleared_when_moved_back(self):
        self.client.login(username='hr1', password='testpass123')
        self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        et = EmployeeTask.objects.get(employee=self.emp, task=self.task)
        et.mark_complete()
        self.client.post(
            reverse('offboarding_checklist', args=[self.emp.pk]),
            {'task_id': et.pk, 'status': 'pending', 'notes': ''},
        )
        et.refresh_from_db()
        self.assertEqual(et.status, 'pending')
        self.assertIsNone(et.completed_at)

    def test_task_completion_refreshes_process_status(self):
        make_interview(self.emp)
        self.client.login(username='hr1', password='testpass123')
        self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        et = EmployeeTask.objects.get(employee=self.emp, task=self.task)
        self.client.post(
            reverse('offboarding_checklist', args=[self.emp.pk]),
            {'task_id': et.pk, 'status': 'completed', 'notes': ''},
        )
        self.process.refresh_from_db()
        self.assertEqual(self.process.status, 'cleared')

    def test_hod_can_view_checklist(self):
        self.client.login(username='hod1', password='testpass123')
        r = self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context['can_edit'])

    def test_employee_cannot_access_checklist(self):
        self.client.login(username='alice', password='testpass123')
        r = self.client.get(reverse('offboarding_checklist', args=[self.emp.pk]))
        self.assertEqual(r.status_code, 403)
