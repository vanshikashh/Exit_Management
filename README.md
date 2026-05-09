# Exit Management System

A Django web application for managing the employee offboarding process at Clovia. Employees complete a structured exit interview, and HR staff can review all submissions and track department-level offboarding checklists.

---

## Features

- **Employee exit interview** — structured questionnaire with ratings, multiple-choice, and open-ended responses
- **Duplicate submission guard** — each employee can only submit once; re-visits show their existing response
- **Offboarding task checklist** — department-specific tasks tracked per employee (IT handover, access revocation, etc.)
- **HR dashboard** — paginated list of all submissions with key metrics at a glance
- **Role-based access** — Employee, HOD, and HR roles with appropriate view restrictions
- **Django admin** — full admin interface for HR and superusers

---

## Setup

### 1. Clone / unzip the project

```bash
cd exit_management_fixed
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/exit-interview/](http://127.0.0.1:8000/exit-interview/)

---

## URL Routes

| URL | View | Access |
|-----|------|--------|
| `/login/` | Login page | Public |
| `/logout/` | Logout | Authenticated |
| `/exit-interview/` | Exit interview form | Authenticated employees |
| `/exit-interview/success/` | Submission confirmation | Authenticated employees |
| `/hr/dashboard/` | HR submissions list | HR role only |
| `/hr/checklist/<user_id>/` | Offboarding checklist | HR role only |
| `/admin/` | Django admin | Staff/superuser |

---

## Project Structure

```
exit_management_fixed/
├── Exit_management/          # Django project config
│   ├── settings.py
│   └── urls.py
├── tasks/                    # Main application
│   ├── models.py             # CustomUser, Department, Task, ExitInterview, EmployeeTask
│   ├── views.py              # All views
│   ├── forms.py              # ExitInterviewForm
│   ├── admin.py              # Admin registrations
│   ├── urls.py               # App URL patterns
│   └── templates/tasks/      # HTML templates
├── static/css/styles.css     # Stylesheet
├── requirements.txt
└── manage.py
```

---

## Roles

| Role | Permissions |
|------|-------------|
| **Employee** | Submit and view own exit interview |
| **HOD** | Same as Employee (department head oversight via admin) |
| **HR** | View all interviews, manage offboarding checklists, full admin access |

---

## Notes for production

- Change `SECRET_KEY` in `settings.py` (load from environment variable)
- Set `DEBUG = False`
- Add your domain to `ALLOWED_HOSTS`
- Configure a production database (PostgreSQL recommended)
- Run `python manage.py collectstatic`
