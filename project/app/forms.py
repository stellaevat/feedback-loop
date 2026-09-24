from django import forms
from django.forms import TextInput, NumberInput, Select, SelectMultiple, ClearableFileInput
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from app.models import Course, Assignment, MarkedSubmission


class CourseForm(forms.ModelForm):
    code = forms.CharField(max_length=10, help_text=mark_safe('<b>Course code: </b>'), widget=TextInput(attrs={'placeholder': 'Enter course code'}))
    name = forms.CharField(required=False, max_length=100, help_text=mark_safe('<b>Course name: </b>'), widget=TextInput(attrs={'placeholder': 'Enter course name'}))
    markers = forms.ModelMultipleChoiceField(required=False, help_text=mark_safe('<b>Markers: </b>'), queryset=User.objects.filter(userprofile__is_marker=True), widget=SelectMultiple(attrs={'size':'1'}))

    class Meta:
        model = Course
        fields = ('code', 'name', 'markers')

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)

        super().__init__(*args, **kwargs)

        if course is not None:
            self.fields['code'].initial = course.code
            self.fields['name'].initial = course.name
            self.fields['markers'].initial = course.markers.all()

    def clean_code(self):
        # Ensure course code is unique case-insensitive
        return self.cleaned_data['code'].upper()

    def clean_name(self):
        # Ensure course name is unique case-insensitive
        return self.cleaned_data['name'].title()


class AssignmentForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100, 
        help_text=mark_safe('<b>Name: </b>'), 
        widget=TextInput(attrs={'placeholder': 'Enter assignment name'})
    )
    spec = forms.FileField(
        required=False, 
        help_text=mark_safe('<p>Specification: </p>'), 
        widget=ClearableFileInput()
    )
    rubric = forms.FileField(
        required=False, 
        help_text=mark_safe('<p>Rubric: </p>'), 
        widget=ClearableFileInput()
    )
    markers = forms.ModelMultipleChoiceField(
        required=False, 
        help_text=mark_safe('<b>Markers assigned: </b>'), 
        queryset=User.objects.filter(userprofile__is_marker=True), 
        widget=SelectMultiple(attrs={"size":'1'})
    )

    class Meta:
        model = Assignment
        fields = ('name', 'spec', 'rubric', 'markers')

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        assignment = kwargs.pop('assignment', None)

        self.course = course
        self.assignment = assignment

        super().__init__(*args, **kwargs)

        if course is not None:
            # Only allow markers that have been assigned to this assignment's course
            self.fields['markers'].queryset = User.objects.filter(courses_marked=course)
        if assignment is not None:
            self.fields['name'].initial = assignment.name
            self.fields['spec'].initial = assignment.spec
            self.fields['rubric'].initial = assignment.rubric
            self.fields['markers'].initial = assignment.markers.all()

    def clean(self):
        # Set course under which the assignment was created
        self.instance.course = self.course
        cleaned_data = super().clean()

        # Enforce unique_together constraint between course and assignment name
        name = cleaned_data.get('name')
        same_assignments = Assignment.objects.filter(course=self.course, name=name)
        if self.assignment:
            # Not considering the assignment itself when being updated
            same_assignments = same_assignments.exclude(pk=self.assignment.pk)

        if same_assignments.exists():
            raise ValidationError({'name': 'Course already contains assignment with this name.'})

        return cleaned_data

    def clean_name(self):
        # Ensure assignment name is unique case-insensitive
        return self.cleaned_data['name'].title()


class GradeModerationForm(forms.ModelForm):
    grade_moderation = forms.ChoiceField(
        help_text=mark_safe('<p>Grade moderation:</p>'), 
        choices=[(None, '')] + list(Assignment.MODERATION_ALGORITHMS), 
        widget=Select(attrs={'id': 'grade-moderation-alg',  'onchange': 'revealModerationParams(this)'})
    )
    grade_moderation_param_1 = forms.FloatField(
        help_text=mark_safe('<span id="param-1-text"></span>'), 
        widget=NumberInput(attrs={'id': 'param-1', 'class':'short-input', 'step': '0.1', 'hidden': True})
    )
    grade_moderation_param_2 = forms.FloatField(
        help_text=mark_safe('<span id="param-2-text"></span>'), 
        widget=NumberInput(attrs={'id': 'param-2', 'class':'short-input', 'step': '0.1', 'hidden': True})
    )

    class Meta:
        model = Assignment
        fields = ('grade_moderation', 'grade_moderation_param_1', 'grade_moderation_param_2')

    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)

        super().__init__(*args, **kwargs)

        if assignment is not None and assignment.grade_moderation is not None:
            self.fields['grade_moderation'].initial = assignment.grade_moderation
            self.fields['grade_moderation_param_1'].initial = assignment.grade_moderation_param_1
            self.fields['grade_moderation_param_2'].initial = assignment.grade_moderation_param_2

            # Not hidden if moderation has already been performed
            self.fields['grade_moderation_param_1'].widget = NumberInput(attrs={
                'id': 'param-1', 
                'class':'short-input', 
                'step': '0.1',
            })
            self.fields['grade_moderation_param_2'].widget = NumberInput(attrs={
                'id': 'param-2', 
                'class':'short-input', 
                'step': '0.1'
            })

            # Display informative names for parameters depending on algorithm
            if assignment.grade_moderation == 'linear':
                self.fields['grade_moderation_param_1'].help_text = mark_safe('<span id="param-1-text">Multiplier: </span>')
                self.fields['grade_moderation_param_2'].help_text = mark_safe('<span id="param-2-text">Shift: </span>')
            elif assignment.grade_moderation == 'z-score':
                self.fields['grade_moderation_param_1'].help_text = mark_safe('<span id="param-1-text">Target μ: </span>')
                self.fields['grade_moderation_param_2'].help_text = mark_safe('<span id="param-2-text">Target σ: </span>')


class FeedbackModerationForm(forms.ModelForm):
    feedback_tone = forms.ChoiceField(
        required=False, 
        help_text='Desired tone: ', 
        choices=[(None, '')] + list(Assignment.TONES), # Include empty (null) option
        widget=Select()
    )
    feedback_length_min = forms.IntegerField(
        required=False, 
        min_value=0, 
        help_text='Min. feedback length: ', 
        widget=NumberInput(attrs={'placeholder':'min', 'class':'short-input'})
    )
    feedback_length_max = forms.IntegerField(
        required=False, 
        min_value=0, 
        help_text='Max. feedback length: ', 
        widget=NumberInput(attrs={'placeholder':'max', 'class':'short-input'})
    )
    feedback_moderation_requests = forms.CharField(
        required=False, 
        help_text='Additional requests: ', 
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Describe any additional moderation requests...'})
    )

    class Meta:
        model = Assignment
        fields = ('feedback_tone', 'feedback_length_min', 'feedback_length_max', 'feedback_moderation_requests')

    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)

        super().__init__(*args, **kwargs)

        if assignment is not None:
            self.fields['feedback_tone'].initial = assignment.feedback_tone
            self.fields['feedback_length_min'].initial = assignment.feedback_length_min
            self.fields['feedback_length_max'].initial = assignment.feedback_length_max
            self.fields['feedback_moderation_requests'].initial = assignment.feedback_moderation_requests

    # Combine min/max length errors into one since they're presented together
    @property
    def feedback_length_min_max_errors(self):
        min_length_errors = list(self.errors.get("feedback_length_min", []))
        max_length_errors = list(self.errors.get("feedback_length_max", []))
        return ErrorList(min_length_errors + max_length_errors)


class MarkedSubmissionForm(forms.ModelForm):
    student_cid = forms.CharField(
        max_length=8, 
        help_text=mark_safe('<b>Student CID: </b>'), 
        widget=TextInput(attrs={'placeholder': 'Enter student CID'})
    )
    marker_grade = forms.FloatField(
        required=False, 
        min_value=0, 
        max_value=100, 
        help_text=mark_safe('<b>Grade: </b>'), 
        widget=NumberInput(attrs={'step': '0.1'})
    )
    initial_marker_feedback = forms.CharField(
        required=False, 
        help_text=mark_safe('<p>Feedback: </p>'), 
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Enter your feedback...', 'class':'small-indent'})
    )
    suggested_improvements = forms.CharField(
        required=False, 
        help_text=mark_safe('<p id="suggestion-label">Suggested improvements: </p>'), 
        widget=forms.Textarea(attrs={'readonly': True, 'rows': 6, 'class':'small-indent'})
    )
    improved_marker_feedback = forms.CharField(
        required=False, 
        help_text=mark_safe('<p>Final feedback: </p>'), 
        widget=forms.Textarea(attrs={'disabled': True, 'rows': 6, 'class':'small-indent', 'placeholder': 'Enter your final improved feedback...'}))

    class Meta:
        model = MarkedSubmission
        fields = ('student_cid', 'marker_grade', 'initial_marker_feedback', 'improved_marker_feedback', 'suggested_improvements')

    def __init__(self, *args, **kwargs):
        submission = kwargs.pop('submission', None)
        assignment = kwargs.pop('assignment', None)
        marker = kwargs.pop('marker', None)

        self.submission = submission
        self.assignment = assignment
        self.marker = marker

        super().__init__(*args, **kwargs)

        if submission is not None:
            self.fields['student_cid'].initial = submission.student_cid
            self.fields['marker_grade'].initial = submission.marker_grade
            self.fields['initial_marker_feedback'].initial = submission.initial_marker_feedback
            self.fields['suggested_improvements'].initial = submission.suggested_improvements
            self.fields['improved_marker_feedback'].initial = submission.improved_marker_feedback
            if submission.suggested_improvements:
                # Not hidden if suggestions have already been generated
                self.fields['improved_marker_feedback'].widget = forms.Textarea(attrs={
                    'rows': 6, 
                    'class':'small-indent', 
                    'placeholder': 'Enter your final improved feedback...'
                })

    def clean(self):
        # Set assignment/marker under which the submission was marked
        self.instance.assignment = self.assignment
        self.instance.marker = self.marker

        cleaned_data = super().clean()

        # Enforce unique_together constraint between assignment, marker and student
        student_cid = cleaned_data.get('student_cid')
        same_submission = MarkedSubmission.objects.filter(assignment=self.assignment, marker=self.marker, student_cid=student_cid)
        if self.submission:
            # Not considering the submission itself when being updated
            same_submission = same_submission.exclude(pk=self.submission.pk)
        
        if same_submission.exists():
            raise ValidationError({'student_cid': 'You have already marked this student for this assignment.'})

        return cleaned_data


# Temporary local user authentication
class UserForm(forms.Form):
    username = forms.CharField(max_length=10, widget=TextInput())
    password = forms.CharField(max_length=128, widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')


