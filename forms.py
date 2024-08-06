from django import forms
from .models import ExitInterview

class ExitInterviewForm(forms.ModelForm):
    class Meta:
        model = ExitInterview
        fields = [
            'employee', 'supervisor_name', 'initial_employment_date', 'last_date_of_employment',
            'current_position', 'decision_time', 'decision_time_comments', 'reasons', 'reason_comments',
            'specific_event', 'event_issue_comments', 'discuss_supervisor', 'discuss_supervisor_comments',
            'training_quality', 'training_quality_comments', 'supervisor_relationship', 
            'supervisor_relationship_comments', 'employee_relationship', 'employee_relationship_comments',
            'salary', 'salary_comments', 'workload', 'satisfaction', 'satisfaction_comments', 'problems',
            'problems_comments', 'enjoy_most', 'enjoy_least', 'recommend', 'recommend_comments', 'reapply',
            'reapply_comments', 'additional_comments', 'interviewer_name', 'interview_date_time'
        ]
        labels = {
            'employee': 'Employee Name',
            'decision_time': 'At approximately what point in time did you begin making your decision to resign?',
            'decision_time_comments': 'Comments:',
            'reasons': 'Please indicate reason(s) below, which contributed to your decision to resign your current position?',
            'specific_event': 'Was there a specific event or issue that prompted your resignation?',
            'event_issue_comments': 'If yes, please briefly explain:',
            'discuss_supervisor': 'If yes, did you discuss this matter with your supervisor/manager?',
            'training_quality': 'Quality of training received for your position(s) here at Clovia.',
            'training_quality_comments': 'Your comments on the quality of training:',
            'supervisor_relationship': 'Working relationship with your current supervisor.',
            'supervisor_relationship_comments': 'Your comments on working relationship with your current supervisor:',
            'employee_relationship': 'Working relationship with fellow employees.',
            'employee_relationship_comments': 'Your comments on working relationship with fellow employees.',
            'salary': 'Salary for your position.',
            'salary_comments': 'Comments:',
            'workload': 'Overall workload for your position.',
            'satisfaction': 'Overall satisfaction and enjoyment in your current position.',
            'satisfaction_comments': 'Your comments on overall satisfaction and enjoyment',
            'problems': 'Did you encounter any problems in your current position?',
            'problems_comments': 'If yes, please briefly comment:',
            'enjoy_most': 'What did you enjoy most about your employment with Clovia?',
            'enjoy_least': 'What did you enjoy least about your employment with Clovia?',
            'recommend': 'Based on your experiences here, would you recommend Clovia as a potential employer for your friends, relatives, etc.?',
            'recommend_comments': 'If no, please briefly explain:',
            'reapply': 'Would you re-apply to Clovia if a future opportunity arose?',
            'reapply_comments': 'If no, please briefly explain:',
            'additional_comments': 'Please add any additional comments:',
            'interviewer_name': 'Exit interview conducted by:',
            'interview_date_time': 'Date/Time:',
        }
        widgets = {
            'initial_employment_date': forms.DateInput(attrs={'type': 'date'}),
            'last_date_of_employment': forms.DateInput(attrs={'type': 'date'}),
            'interview_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'decision_time_comments': forms.Textarea(attrs={'rows': 4}),
            'reason_comments': forms.Textarea(attrs={'rows': 4}),
            'event_issue_comments': forms.Textarea(attrs={'rows': 4}),
            'discuss_supervisor_comments': forms.Textarea(attrs={'rows': 4}),
            'training_quality_comments': forms.Textarea(attrs={'rows': 4}),
            'supervisor_relationship_comments': forms.Textarea(attrs={'rows': 4}),
            'employee_relationship_comments': forms.Textarea(attrs={'rows': 4}),
            'salary_comments': forms.Textarea(attrs={'rows': 4}),
            'satisfaction_comments': forms.Textarea(attrs={'rows': 4}),
            'problems_comments': forms.Textarea(attrs={'rows': 4}),
            'enjoy_most': forms.Textarea(attrs={'rows': 4}),
            'enjoy_least': forms.Textarea(attrs={'rows': 4}),
            'recommend_comments': forms.Textarea(attrs={'rows': 4}),
            'reapply_comments': forms.Textarea(attrs={'rows': 4}),
            'additional_comments': forms.Textarea(attrs={'rows': 4}),
        }
