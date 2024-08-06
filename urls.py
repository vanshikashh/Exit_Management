from django.urls import path
from . import views

urlpatterns = [
    path('exit-interview/', views.exit_interview_form, name='exit_interview_form'),
    path('form-success/', views.form_success, name='form_success'),  # You may need to create this view
]
