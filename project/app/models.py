from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import slugify

is_numeric = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')

# Sets readable name of specs/rubrics when saved
@deconstructible
class rename_file(object):
    def __init__(self, content):
        self.content = content

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f"{instance.course.slug}_{instance.pk}_{self.content}.{ext}"
        return new_filename


class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    course_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    markers = models.ManyToManyField(User, related_name='courses_marked')

    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.code)
        super(Course, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.name}"

    
class Assignment(models.Model):
    MODERATION_ALGORITHMS = (
        ('linear', 'Linear'), # param_1 = multiplier, param_2 = shift
        ('z-score', 'Z-Score'), # param_1 = target mean, param_2 = target SD
    )

    TONES = (
        ('formal', 'Formal'),
        ('friendly', 'Friendly'),
    )
    
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    markers = models.ManyToManyField(User, related_name='assignments_marked')
    spec = models.FileField(upload_to=rename_file('spec'), null=True, blank=True)
    rubric = models.FileField(upload_to=rename_file('rubric'), null=True, blank=True)

    # Grade moderation settings
    grade_moderation = models.CharField(max_length=10, choices=MODERATION_ALGORITHMS, null=True, blank=True)
    grade_moderation_param_1 = models.FloatField(null=True, blank=True)
    grade_moderation_param_2 = models.FloatField(null=True, blank=True)

    # Feedback moderation settings
    feedback_tone = models.CharField(max_length=10, choices=TONES, null=True, blank=True)
    feedback_length_min = models.PositiveIntegerField(null=True, blank=True)
    feedback_length_max = models.PositiveIntegerField(null=True, blank=True)
    feedback_moderation_requests = models.TextField(null=True, blank=True)
    feedback_moderation_prompt = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('course', 'name')

    def __str__(self):
        return f"{self.course.code} - {self.name}"

    
class MarkedSubmission(models.Model):
    marker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student_cid = models.CharField(max_length=8, validators=[is_numeric, MinLengthValidator(8)])
    
    # By marker
    marker_grade = models.FloatField(null=True, blank=True)
    initial_marker_feedback = models.TextField(null=True, blank=True)
    improved_marker_feedback = models.TextField(null=True, blank=True)

    # By lead
    moderated_grade = models.FloatField(null=True, blank=True)
    moderated_feedback = models.TextField(null=True, blank=True)

    # By LLM
    suggested_improvements = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student_cid', 'marker')
    
    def __str__(self):
        return f"{self.assignment} - {self.marker.username} - {self.student_cid}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_staff = models.BooleanField(default=False)
    is_marker = models.BooleanField(default=False)
    is_course_lead = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username