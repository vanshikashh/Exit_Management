from django import forms
from .models import ExitInterview, CustomUser, ExitProcess


class ExitInterviewForm(forms.ModelForm):
    class Meta:
        model = ExitInterview
        exclude = ['employee', 'created_at', 'updated_at']
        labels = {
            'supervisor_name': 'Supervisor / Manager Name',
            'initial_employment_date': 'Initial Employment Date',
            'last_date_of_employment': 'Last Date of Employment',
            'current_position': 'Current Position / Title',
            'decision_time': '1. When did you begin making your decision to resign?',
            'decision_time_comments': 'Comments:',
            'reasons': '2. Primary reason for resigning:',
            'reason_comments': 'Additional comments on your reason:',
            'specific_event': '3. Was there a specific event that prompted your resignation?',
            'event_issue_comments': 'If yes, please explain:',
            'discuss_supervisor': '4. Did you discuss this with your supervisor?',
            'discuss_supervisor_comments': 'Comments:',
            'training_quality': '5. Quality of training received (1 = Poor, 5 = Excellent)',
            'training_quality_comments': 'Comments:',
            'supervisor_relationship': '6. Working relationship with supervisor (1 = Poor, 5 = Excellent)',
            'supervisor_relationship_comments': 'Comments:',
            'employee_relationship': '7. Working relationship with fellow employees (1 = Poor, 5 = Excellent)',
            'employee_relationship_comments': 'Comments:',
            'salary': '8. Satisfaction with salary (1 = Poor, 5 = Excellent)',
            'salary_comments': 'Comments:',
            'workload': '9. Overall workload (1 = Too Light, 5 = Too Heavy)',
            'satisfaction': '10. Overall satisfaction in your position (1 = Very Dissatisfied, 5 = Very Satisfied)',
            'satisfaction_comments': 'Comments:',
            'problems': '11. Did you encounter any unresolved problems?',
            'problems_comments': 'If yes, please describe:',
            'enjoy_most': '12. What did you enjoy most about working at Clovia?',
            'enjoy_least': '13. What did you enjoy least?',
            'recommend': '14. Would you recommend Clovia as an employer?',
            'recommend_comments': 'If no, please explain:',
            'reapply': '15. Would you re-apply to Clovia in future?',
            'reapply_comments': 'If no, please explain:',
            'additional_comments': '16. Any additional comments or suggestions:',
            'interviewer_name': 'Exit Interview Conducted By:',
            'interview_date_time': 'Date / Time of Interview:',
        }
        widgets = {
            'initial_employment_date':  forms.DateInput(attrs={'type': 'date', 'class': 'win-input'}),
            'last_date_of_employment':  forms.DateInput(attrs={'type': 'date', 'class': 'win-input'}),
            'interview_date_time':      forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'win-input'}),
            'decision_time_comments':   forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'reason_comments':          forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'event_issue_comments':     forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'discuss_supervisor_comments': forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'training_quality_comments':   forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'supervisor_relationship_comments': forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'employee_relationship_comments': forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'salary_comments':          forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'satisfaction_comments':    forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'problems_comments':        forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'enjoy_most':               forms.Textarea(attrs={'rows': 3, 'class': 'win-input'}),
            'enjoy_least':              forms.Textarea(attrs={'rows': 3, 'class': 'win-input'}),
            'recommend_comments':       forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'reapply_comments':         forms.Textarea(attrs={'rows': 2, 'class': 'win-input'}),
            'additional_comments':      forms.Textarea(attrs={'rows': 4, 'class': 'win-input'}),
            'supervisor_name':          forms.TextInput(attrs={'class': 'win-input'}),
            'current_position':         forms.TextInput(attrs={'class': 'win-input'}),
            'interviewer_name':         forms.TextInput(attrs={'class': 'win-input'}),
            'decision_time':   forms.RadioSelect(),
            'reasons':         forms.RadioSelect(),
            'training_quality':         forms.RadioSelect(),
            'supervisor_relationship':  forms.RadioSelect(),
            'employee_relationship':    forms.RadioSelect(),
            'salary':                   forms.RadioSelect(),
            'workload':                 forms.RadioSelect(),
            'satisfaction':             forms.RadioSelect(),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('initial_employment_date')
        end   = cleaned.get('last_date_of_employment')
        if start and end and end < start:
            raise forms.ValidationError(
                "Last date of employment cannot be earlier than initial employment date."
            )
        return cleaned


class InitiateExitForm(forms.Form):
    """HR uses this to formally start an employee's offboarding process."""
    employee = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='Employee', is_active=True),
        label='Employee',
        widget=forms.Select(attrs={'class': 'win-input'}),
        help_text='Only active employees not yet in an exit process are shown.',
    )
    last_working_date = forms.DateField(
        label='Last Working Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'win-input'}),
    )
    notes = forms.CharField(
        label='HR Notes (optional)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'win-input',
                                     'placeholder': 'Any context for this exit...'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show employees who don't already have an exit process
        existing_ids = ExitProcess.objects.values_list('employee_id', flat=True)
        self.fields['employee'].queryset = (
            CustomUser.objects
            .filter(role='Employee', is_active=True)
            .exclude(id__in=existing_ids)
        )
