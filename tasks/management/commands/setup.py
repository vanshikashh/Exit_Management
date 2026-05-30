from django.core.management.base import BaseCommand
from tasks.models import CustomUser, Department, Task


class Command(BaseCommand):
    help = 'Create initial data for the Exit Management System'

    def handle(self, *args, **kwargs):
        # Superuser
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_superuser(
                'admin', 'admin@clovia.com', 'Admin@123'
            )
            self.stdout.write('Created superuser: admin / Admin@123')

        # Departments
        eng,   _ = Department.objects.get_or_create(department_id=1, defaults={'department_name': 'Engineering'})
        fin,   _ = Department.objects.get_or_create(department_id=2, defaults={'department_name': 'Finance'})
        legal, _ = Department.objects.get_or_create(department_id=3, defaults={'department_name': 'Legal'})
        hr_d,  _ = Department.objects.get_or_create(department_id=4, defaults={'department_name': 'HR'})

        # Users
        users = [
            ('hr_priya',  'Priya',  'Sharma', 'HR',       hr_d),
            ('hod_rahul', 'Rahul',  'Mehta',  'HOD',      eng),
            ('hod_sneha', 'Sneha',  'Kapoor', 'HOD',      fin),
            ('hod_arjun', 'Arjun',  'Verma',  'HOD',      legal),
            ('emp_alice', 'Alice',  'Roy',    'Employee',  eng),
            ('emp_bob',   'Bob',    'Khan',   'Employee',  fin),
            ('emp_cara',  'Cara',   'Singh',  'Employee',  eng),
            ('emp_dev',   'Dev',    'Patel',  'Employee',  legal),
            ('emp_esha',  'Esha',   'Gupta',  'Employee',  fin),
        ]
        for username, first, last, role, dept in users:
            if not CustomUser.objects.filter(username=username).exists():
                CustomUser.objects.create_user(
                    username, password='Pass@123',
                    role=role, department=dept,
                    first_name=first, last_name=last
                )
                self.stdout.write(f'Created {role}: {username}')

        # Tasks
        tasks = [
            ('Return company ID card',          'standard', None),
            ('Complete exit interview form',     'standard', None),
            ('Sign full and final settlement',   'standard', None),
            ('Return laptop and accessories',    'departmental', eng),
            ('Revoke system and email access',   'departmental', eng),
            ('Knowledge transfer document',      'departmental', eng),
            ('Clear all pending dues',           'departmental', fin),
            ('Submit final expense report',      'departmental', fin),
            ('Return company credit card',       'departmental', fin),
            ('Sign NDA termination agreement',   'departmental', legal),
            ('Return all company documents',     'departmental', legal),
            ('Complete IP assignment form',      'departmental', legal),
        ]
        for detail, ttype, dept in tasks:
            if not Task.objects.filter(task_detail=detail).exists():
                Task.objects.create(
                    task_detail=detail,
                    task_type=ttype,
                    department=dept
                )
                self.stdout.write(f'Created task: {detail}')

        self.stdout.write(self.style.SUCCESS('Setup complete!'))
