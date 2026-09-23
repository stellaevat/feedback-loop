from django.db.models import F, Avg, StdDev
from django.db.models.functions import Round
from app.models import MarkedSubmission

def linear_scaling(value, multiplier, shift):
    result = value * multiplier + shift
    return Round(result, 1)

def z_score_scaling(value, mean_raw, sd_raw, mean_target, sd_target):
    result = ((value - mean_raw) / sd_raw) * sd_target + mean_target
    return Round(result, 1)

def apply_grade_moderation(assignment):
    marked_submissions = MarkedSubmission.objects.filter(assignment=assignment).exclude(marker_grade__isnull=True)

    if assignment.grade_moderation == 'linear':
        multiplier = assignment.grade_moderation_param_1
        shift = assignment.grade_moderation_param_2

        marked_submissions.update(
            moderated_grade=linear_scaling(F('marker_grade'), multiplier, shift)
        )

    elif assignment.grade_moderation == 'z-score':
        stats = marked_submissions.aggregate(Avg('marker_grade'), StdDev('marker_grade'))
        mean_raw = stats['marker_grade__avg']
        sd_raw = stats['marker_grade__stddev']
        mean_target = assignment.grade_moderation_param_1
        sd_target = assignment.grade_moderation_param_2

        marked_submissions.update(
            moderated_grade=z_score_scaling(F('marker_grade'), mean_raw, sd_raw, mean_target, sd_target)
        )

    for submission in marked_submissions:
        submission.save()