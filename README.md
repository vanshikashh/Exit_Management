# Exit Management System

A full-stack Django web application built during my internship at **Clovia Pvt Ltd** to digitise and automate the employee offboarding process. The system replaces paper-based exit workflows with a structured, role-based platform covering exit interviews, department clearance tracking, and an immutable audit trail.

**Live repository:** [github.com/vanshikashh/Exit_Management](https://github.com/vanshikashh/Exit_Management)

---

## What it does

When an employee resigns, HR initiates their exit process on this platform. From that point, the system:

- Assigns clearance tasks automatically across **all departments** (Finance, IT, Legal, HR, etc.)
- Lets each department's HOD track and update only their own tasks for every exiting employee
- Prompts the employee to complete a structured **16-question exit interview**
- Auto-progresses the process status (`Initiated → In Progress → Cleared`) based on real data
- Logs every action immutably in an **audit trail** — who did what, when, and what changed
- Gives HR a live dashboard with aggregate satisfaction ratings across 5 dimensions

---

## Roles

| Role | Access |
|------|--------|
| **HR** | Initiate exits, manage standard tasks, view full dashboard and audit log |
| **HOD** | View all exiting employees, update tasks owned by their department only |
| **Employee** | View own offboarding status and department-wise clearance progress |
| **Admin** | Full database access via Django admin panel |

---

## Tech Stack

- **Backend:** Python, Django, Django ORM
- **Database:** SQLite (development)
- **Frontend:** HTML, CSS (custom Windows 11 Fluent Design system — no UI library)
- **Auth:** Django AbstractUser with role-based access control
- **Version control:** Git

---

## Key Technical Features

- **Role-based access control** — 3 user types with separate dashboards, login redirects, and enforced view permissions
- **Two task types** — Standard tasks (HR-managed, everyone gets them) and Departmental tasks (HOD-managed, scoped to owning department)
- **Auto task assignment** — On exit initiation, all tasks from all departments are bulk-assigned in a single `bulk_create` call
- **Annotation over N+1** — Dashboard queries use Django `Count` with conditional filters via `annotate()` — O(1) queries regardless of employee count
- **Immutable audit log** — `AuditLog.save()` raises `ValueError` on updates; every HR and HOD action is permanently recorded with actor, subject, old value, new value
- **State machine** — `ExitProcess.refresh_status()` auto-computes process state after every task update or interview submission
- **CSRF-hardened logout** — POST-only logout endpoint; GET requests do not log out the user
- **51 automated tests** — covering models, views, form validation, role enforcement, task ownership, and audit logging

---

## Project Structure

```
Exit_Management/
├── Exit_management/          # Django project config (settings, urls, wsgi)
├── tasks/                    # Main application
│   ├── models.py             # CustomUser, Department, Task, EmployeeTask,
│   │                         # ExitProcess, ExitInterview, AuditLog
│   ├── views.py              # All views with role guards and business logic
│   ├── forms.py              # ExitInterviewForm, InitiateExitForm, TaskForm
│   ├── admin.py              # Fully customised admin with badges and summaries
│   ├── urls.py               # App URL patterns
│   ├── tests.py              # 51 tests
│   └── templates/tasks/      # HTML templates (login, dashboards, checklist,
│                             # interview form, audit log, status page)
├── static/css/styles.css     # Custom design system (Win11 Fluent)
├── requirements.txt
└── manage.py
```

---

## Setup

```bash
# Clone the repo
git clone https://github.com/vanshikashh/Exit_Management.git
cd Exit_Management

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser (for admin access)
python manage.py createsuperuser

# Run the server
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## Seeding test data

```python
# Run: python manage.py shell
from tasks.models import CustomUser, Department, Task

eng = Department.objects.create(department_id=1, department_name='Engineering')
fin = Department.objects.create(department_id=2, department_name='Finance')
hr_dept = Department.objects.create(department_id=3, department_name='HR')

CustomUser.objects.create_user('hr_user',    password='Pass@123', role='HR',       department=hr_dept, first_name='Priya',  last_name='Sharma')
CustomUser.objects.create_user('hod_eng',    password='Pass@123', role='HOD',      department=eng,     first_name='Rahul',  last_name='Mehta')
CustomUser.objects.create_user('hod_fin',    password='Pass@123', role='HOD',      department=fin,     first_name='Sneha',  last_name='Kapoor')
CustomUser.objects.create_user('emp_alice',  password='Pass@123', role='Employee', department=eng,     first_name='Alice',  last_name='Roy')
CustomUser.objects.create_user('emp_bob',    password='Pass@123', role='Employee', department=fin,     first_name='Bob',    last_name='Khan')

# Standard tasks — apply to every employee, managed by HR
Task.objects.create(task_detail='Return company ID card', task_type='standard')
Task.objects.create(task_detail='Complete exit interview form', task_type='standard')

# Departmental tasks — managed by that dept's HOD
Task.objects.create(task_detail='Return laptop and accessories',       task_type='departmental', department=eng)
Task.objects.create(task_detail='Revoke system and email access',      task_type='departmental', department=eng)
Task.objects.create(task_detail='Complete knowledge transfer document',task_type='departmental', department=eng)
Task.objects.create(task_detail='Clear all pending dues',              task_type='departmental', department=fin)
Task.objects.create(task_detail='Submit final expense report',         task_type='departmental', department=fin)
Task.objects.create(task_detail='Return company credit card',          task_type='departmental', department=fin)
```

---

## URL Reference

| URL | Role | Page |
|-----|------|------|
| `/login/` | All | Sign in |
| `/my-status/` | Employee | 4-step offboarding tracker with dept clearance breakdown |
| `/exit-interview/` | Employee | 16-question exit interview form |
| `/hod/dashboard/` | HOD | All exiting employees + own dept tasks (editable) |
| `/hr/dashboard/` | HR | Full dashboard with stats and aggregate ratings |
| `/hr/initiate/` | HR | Initiate a new exit process |
| `/hr/checklist/<id>/` | HR | Full task checklist for one employee |
| `/hr/audit-log/` | HR | Filterable immutable audit log |
| `/admin/` | Superuser | Django admin — full DB access |

---

## Running tests

```bash
python manage.py test tasks
```

Expected output: `Ran 41 tests in Xs — OK`

---

*Built with Python · Django · SQLite · HTML/CSS · Git*
