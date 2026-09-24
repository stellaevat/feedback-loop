import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from app.models import Course, Assignment, MarkedSubmission
from app.forms import CourseForm, AssignmentForm, GradeModerationForm, FeedbackModerationForm, MarkedSubmissionForm, UserForm
from app.grade_moderation import apply_grade_moderation

# Customise platform name
PLATFORM_NAME = 'Feedback Loop'

# Whether the double o shows as inf in the logo (enforces platform logo 'Feedback Loop')
INF_SYMBOL_IN_LOGO = True

# Custom error handling for course lead/marker-restricted access
class CustomMessagePermissionDenied(PermissionDenied):
    pass

only_leads_msg = "Only course leads can access this content."
only_leads_and_markers_msg = "Only course leads and markers can access this content."
only_leads_and_sub_markers_msg = "Only course leads and submission markers can access this content."


# TODO: LLM-related processes left to implement

def get_feedback_moderation_prompt(assignment):
    return "Moderation prompr created."

def get_suggested_improvements_prompt(submission):
    return "Improvement prompts created."

def generate_suggested_improvements(submission):
    return "You should consider..."


# --------------------------------------------------------------
# Views
# --------------------------------------------------------------

def homepage(request):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}
    return render(request, 'app/homepage.html', context=context_dict)

@login_required
def my_courses(request):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    courses_led = Course.objects.filter(course_lead=request.user)
    courses_marked = Course.objects.filter(markers=request.user)

    # No. of assignments created by user as course lead (all of them)
    course_assignments_led = {course : Assignment.objects.filter(course=course).count() for course in courses_led}

    # No. of assignments marked by user
    course_assignments_marked = {course : Assignment.objects.filter(course=course, markers=request.user).count() for course in courses_marked}

    # If a course is both led and marked, display total assignment count
    all_courses = list(course_assignments_led.items())
    for (course, assignment_count) in course_assignments_marked.items():
        if course not in course_assignments_led:
            all_courses.append((course, assignment_count))

    context_dict['is_course_lead'] = request.user.userprofile.is_course_lead
    context_dict['courses'] = all_courses
    return render(request, 'app/my_courses.html', context=context_dict)


@login_required
def view_course(request, course_slug):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead and request.user not in course.markers.all():
        raise CustomMessagePermissionDenied(only_leads_and_markers_msg)

    all_assignments = Assignment.objects.filter(course=course).prefetch_related('markers')

    if course.course_lead == request.user:
        context_dict['is_course_lead'] = True

        # Assignments/submissions monitored by user as course lead (all of them)
        assignments = all_assignments
        submission_count = [MarkedSubmission.objects.filter(assignment=a).count() for a in assignments]
    else:
        # Assignments/submissions marked by user
        assignments = [a for a in all_assignments if request.user in a.markers.all()]
        submission_count = [MarkedSubmission.objects.filter(assignment=a, marker=request.user).count() for a in assignments]
    

    context_dict['course'] = course
    context_dict['assignments'] = zip(assignments, submission_count) if assignments else None
    return render(request, 'app/view_course.html', context=context_dict)


@login_required
def view_assignment(request, course_slug, assignment_id):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    if request.user != course.course_lead and request.user not in assignment.markers.all():
        raise CustomMessagePermissionDenied(only_leads_and_markers_msg)
    
    all_submissions = MarkedSubmission.objects.filter(assignment=assignment)

    if course.course_lead == request.user:
        context_dict['is_course_lead'] = True

        # Submissions monitored by user as course lead (all of them)
        submissions = all_submissions
    else:
        # Submissions marked by user
        submissions = [s for s in all_submissions if s.marker == request.user]

    context_dict['course'] = course
    context_dict['assignment'] = assignment
    context_dict['submissions'] = submissions
    return render(request, 'app/view_assignment.html', context=context_dict)


@login_required
def export_csv(request, course_slug, assignment_id):
    course = get_object_or_404(Course, slug=course_slug)
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    if request.user != course.course_lead and request.user not in assignment.markers.all():
        raise CustomMessagePermissionDenied(only_leads_and_markers_msg)

    if request.user == course.course_lead:
        submissions = MarkedSubmission.objects.filter(assignment=assignment)
    else:
        submissions = MarkedSubmission.objects.filter(assignment=assignment, marker=request.user)

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{course_slug}_{assignment_id}_grades.csv"'},
    )
    writer = csv.writer(response)

    writer.writerow([
        'Student ID', 
        'Marker', 
        'Marker_Grade', 
        'Moderated_Grade', 
        'Initial_Marker_Feedback', 
        'Improved_Marker_Feedback', 
        'Moderated Feedback'
    ])
    for s in submissions:
        writer.writerow([
            s.student_cid, 
            s.marker, 
            s.marker_grade, 
            s.moderated_grade, 
            s.initial_marker_feedback, 
            s.improved_marker_feedback, 
            s.moderated_feedback
        ])
    return response


# --------------------------------------------------------------
# Only for course leads
# --------------------------------------------------------------

@login_required
def new_course(request):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    if not request.user.userprofile.is_course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)
        
    if request.method == 'POST':
        course_form = CourseForm(request.POST)
        if course_form.is_valid():
            course = course_form.save(commit=False)
            course.course_lead = request.user
            course.save()
            course.markers.add(*course_form.cleaned_data.get('markers'))
            return redirect(reverse('app:view_course', kwargs={'course_slug': course.slug}))
        else:
            print(course_form.errors)
    else:
        course_form = CourseForm()

    context_dict['course_form'] = course_form
    return render(request, 'app/new_course.html', context=context_dict)


@login_required
def manage_course(request, course_slug):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)

    if request.method == 'POST':
        course_form = CourseForm(request.POST, instance=course, course=course)
        if course_form.is_valid():
            course = course_form.save()
            return redirect(reverse('app:view_course', kwargs={'course_slug': course.slug}))
        else:
            course = get_object_or_404(Course, slug=course_slug)
            print(course_form.errors)
    else:
        course_form = CourseForm(course=course)

    context_dict['course'] = course
    context_dict['course_form'] = course_form
    return render(request, 'app/manage_course.html', context=context_dict)


@login_required
def delete_course(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)

    course.delete()
    return redirect(reverse('app:my_courses'))


@login_required
def new_assignment(request, course_slug):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)

    if request.method == 'POST':
        assignment_form = AssignmentForm(request.POST, request.FILES, course=course)
        if assignment_form.is_valid():
            assignment = assignment_form.save()
            return redirect(reverse('app:view_assignment', kwargs={
                'course_slug': course.slug, 
                'assignment_id': assignment.pk
            }))
        else:
            print(assignment_form.errors)
    else:
        assignment_form = AssignmentForm(course=course)

    context_dict['course'] = course
    context_dict['assignment_form'] = assignment_form
    return render(request, 'app/new_assignment.html', context=context_dict)


@login_required
def manage_assignment(request, course_slug, assignment_id):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)
    
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    submissions = MarkedSubmission.objects.filter(assignment=assignment)

    context_dict['course'] = course
    context_dict['assignment'] = assignment
    context_dict['submissions'] = submissions
    context_dict['is_course_lead'] = True

    assignment_form = AssignmentForm(course=course, assignment=assignment)
    grade_form = GradeModerationForm(assignment=assignment)
    feedback_form = FeedbackModerationForm(assignment=assignment)
    
    if request.method == 'POST':
        if 'edit-assignment' in request.POST:
            assignment_form = AssignmentForm(
                request.POST, request.FILES, 
                instance=assignment, 
                course=course, 
                assignment=assignment
            )
            form = assignment_form
        elif 'grade-moderation' in request.POST:
            grade_form = GradeModerationForm(request.POST, instance=assignment, assignment=assignment)
            form = grade_form
        elif 'feedback-moderation' in request.POST:
            feedback_form = FeedbackModerationForm(request.POST, instance=assignment, assignment=assignment)
            form = feedback_form

        if form.is_valid():
            form.save()
            if 'edit-assignment' in request.POST:    
                return redirect(reverse('app:view_assignment', kwargs={
                    'course_slug': course.slug, 
                    'assignment_id': assignment.pk
                }))
            elif 'grade-moderation' in request.POST:
                apply_grade_moderation(assignment)
            elif 'feedback-moderation' in request.POST:
                assignment.feedback_moderation_prompt = get_feedback_moderation_prompt(assignment)
        else:
            print(form.errors)

    context_dict['assignment_form'] = assignment_form
    context_dict['grade_form'] = grade_form
    context_dict['feedback_form'] = feedback_form

    return render(request, 'app/manage_assignment.html', context=context_dict)


@login_required
def delete_assignment(request, course_slug, assignment_id):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user != course.course_lead:
        raise CustomMessagePermissionDenied(only_leads_msg)

    assignment = get_object_or_404(Assignment, pk=assignment_id)
    assignment.delete()
    return redirect(reverse('app:view_course', kwargs={'course_slug': course.slug}))


# --------------------------------------------------------------
# Only for course leads and assigned markers
# --------------------------------------------------------------

@login_required
def mark_submission(request, course_slug, assignment_id, submission_id=None):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    course = get_object_or_404(Course, slug=course_slug)
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    
    if request.user != course.course_lead and request.user not in assignment.markers.all():
        raise CustomMessagePermissionDenied(only_leads_and_markers_msg)

    if submission_id is not None:
        original_submission = get_object_or_404(MarkedSubmission, pk=submission_id)
        if request.user != course.course_lead and request.user != original_submission.marker:
            raise CustomMessagePermissionDenied(only_leads_and_sub_markers_msg)
    else: 
        original_submission = None

    if request.method == 'POST':
        submission_form = MarkedSubmissionForm(
            request.POST, 
            instance=original_submission, 
            submission=original_submission, 
            assignment=assignment, 
            marker=request.user
        )
        if submission_form.is_valid():
            submission = submission_form.save()

            # Clear moderated grade if original grade has just been removed
            if submission.marker_grade is None:
                submission.moderated_grade = None
                submission.save()

            if 'mark-submission' in request.POST:
                return redirect(reverse('app:view_assignment', kwargs={
                    'course_slug': course.slug, 
                    'assignment_id': assignment.pk
                }))

            elif 'check-feedback' in request.POST:
                suggested_improvements = generate_suggested_improvements(submission)
                submission.suggested_improvements = suggested_improvements
                submission.save()
                return redirect(reverse('app:mark_existing_submission', kwargs={
                    'course_slug' : course.slug, 
                    'assignment_id' : assignment.pk, 
                    'submission_id' : submission.pk
                }))
        else:
            print(submission_form.errors)
    else:
        submission_form = MarkedSubmissionForm(
            submission=original_submission, 
            assignment=assignment, 
            marker=request.user
        )

    context_dict['course'] = course
    context_dict['assignment'] = assignment
    context_dict['submission'] = original_submission
    context_dict['submission_form'] = submission_form

    return render(request, 'app/mark_subsmission.html', context=context_dict)


@login_required
def delete_submission(request, course_slug, assignment_id, submission_id):
    course = get_object_or_404(Course, slug=course_slug)
    assignment = get_object_or_404(Assignment, pk=assignment_id)
        
    if request.user != course.course_lead and request.user not in assignment.markers.all():
        raise CustomMessagePermissionDenied(only_leads_and_markers_msg)

    submission = get_object_or_404(MarkedSubmission, pk=submission_id)

    if request.user != course.course_lead and request.user != submission.marker:
        raise CustomMessagePermissionDenied(only_leads_and_sub_markers_msg)
    
    submission.delete()
    return redirect(reverse('app:view_assignment', kwargs={
        'course_slug': course.slug, 
        'assignment_id': assignment.pk
    }))


# --------------------------------------------------------------
# Temporary local user authentication
# --------------------------------------------------------------

def user_login(request):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    login(request, user)
                    return redirect(reverse('app:homepage'))
                else:
                    return HttpResponse("Your account is disabled.")
            else:
                return HttpResponse("Invalid login details supplied.")
        else:
            print(form.errors)
    else:
        form = UserForm()

    context_dict['login_form'] = form
    return render(request, 'app/user_login.html', context=context_dict)

@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('app:homepage'))


# --------------------------------------------------------------
# Custom error pages
# --------------------------------------------------------------

def page_not_found(request, exception):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}
    return render(request, 'errors/page_not_found.html', context=context_dict)

def forbidden(request, exception):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}
    if isinstance(exception, CustomMessagePermissionDenied):
        context_dict['custom_message'] = str(exception)
    return render(request, 'errors/forbidden.html', context=context_dict)

def server_error(request):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}
    return render(request, 'errors/catch_all.html', context=context_dict)
    
def bad_request(request, exception):
    context_dict = {'platform_name': PLATFORM_NAME, 'inf_logo': INF_SYMBOL_IN_LOGO}
    return render(request, 'errors/catch_all.html', context=context_dict)
