# Exit_Management
This is my repository for a web Application on Employee exit management that I worked on during my internship at Clovia.

Exit Management System
Table of Contents
Project Overview
Features
Setup and Installation
Usage
Models and Forms
Database
Admin Interface
Known Issues
Contributing
License
Project Overview
The Exit Management System is a Django-based web application designed to streamline the process of managing employee exits within an organization. It enables HR, HODs, and employees to handle the necessary formalities efficiently. The system includes features for handling exit interviews, tracking the completion of exit formalities, and generating reports.

Features
User Roles: HR (Super Admin), HOD (Department Admin), and Employees.
Exit Interviews: Manage and record exit interview details.
Task Management: Track tasks related to employee exits.
Email Notifications: Automatic email notifications for various actions.
Admin Interface: Manage users, departments, and exit formalities.
Setup and Installation
Prerequisites
Python 3.6+
Django 5.0.6+
SQLite (or other preferred database)
Other dependencies as listed in requirements.txt
Installation Steps
Clone the repository:
bash
Copy code
git clone https://github.com/yourusername/exit-management-system.git
Navigate to the project directory:
bash
Copy code
cd exit-management-system
Install dependencies:
bash
Copy code
pip install -r requirements.txt
Set up the database:
bash
Copy code
python manage.py makemigrations
python manage.py migrate
Create a superuser:
bash
Copy code
python manage.py createsuperuser
Run the server:
bash
Copy code
python manage.py runserver
Usage
Accessing the Admin Interface
Navigate to http://127.0.0.1:8000/admin/ and log in with your superuser credentials. From here, you can manage users, departments, and other aspects of the exit process.

Exit Interviews
To add an exit interview, go to the Admin interface, navigate to the "Exit Interviews" section, and click "Add Exit Interview."

Models and Forms
Key Models
CustomUser: Extended User model for custom fields.
ExitInterview: Model to store exit interview details.
Department: Model to manage departments and their HODs.
Task: Model to track tasks related to employee exits.
Forms
ExitInterviewForm: Form for handling the submission of exit interview data.
Database
Schema
The database schema includes tables for users, departments, exit interviews, and tasks. Make sure to apply migrations whenever you modify the models.

Migration Commands
To apply changes to the database schema:

bash
Copy code
python manage.py makemigrations
python manage.py migrate
Admin Interface
The admin interface provides access to all models. Custom user roles and permissions are configured to restrict access based on the role (HR, HOD, Employee).

Known Issues
JSON_VALID Constraint Error: If you encounter an error related to the JSON_VALID constraint, ensure that the reasons field in the ExitInterview model is correctly defined and that the database schema is in sync with the model definitions.
Contributing
We welcome contributions! Please fork the repository and submit a pull request with your changes. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

License
This project is licensed under the MIT License. See the LICENSE file for more details.
