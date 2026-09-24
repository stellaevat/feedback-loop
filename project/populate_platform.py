import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

from django.contrib.auth.models import User
from app.models import UserProfile, Course, Assignment, MarkedSubmission

def add_user_profile(username, password, is_staff=False, is_marker=False, is_course_lead=False):
    user = User.objects.get_or_create(username=username)[0]
    user.set_password(password)
    user.save()

    user_profile = UserProfile.objects.get_or_create(
        user=user,
        defaults={'is_staff': is_staff, 'is_marker': is_marker, 'is_course_lead': is_course_lead}
    )[0]
    user_profile.save()

    return user_profile

def add_course_lead(username, password='password'):
    user_profile = add_user_profile(username, password, is_course_lead=True)
    return user_profile

def add_marker(username, password='password'):
    user_profile = add_user_profile (username, password, is_marker=True)
    return user_profile

def add_course(code, name, course_lead_username, marker_usernames=[]):
    course_lead = User.objects.get(username=course_lead_username)

    course = Course.objects.get_or_create(
        code=code,
        course_lead=course_lead,
        defaults={'name': name}
    )[0]

    for username in marker_usernames:
        marker = User.objects.get(username=username)
        course.markers.add(marker)

    return course

def add_assignment(name, course_code, marker_usernames=[], spec=None):
    course = Course.objects.get(code=course_code)

    assignment = Assignment.objects.get_or_create(
        name=name,
        course=course
    )[0]

    assignment.spec = spec

    # Add markers to the assignment
    for username in marker_usernames:
        marker = User.objects.get(username=username)
        assignment.markers.add(marker)

    return assignment

def add_marked_submission(assignment_name, student_cid, marker_username, marker_grade=None, initial_marker_feedback=None, improved_marker_feedback=None):
    assignment = Assignment.objects.get(name=assignment_name)
    marker = User.objects.get(username=marker_username)

    submission = MarkedSubmission.objects.get_or_create(
        assignment=assignment,
        student_cid=student_cid,
        marker=marker,
        defaults={'marker_grade': marker_grade, 'initial_marker_feedback': initial_marker_feedback, 'improved_marker_feedback': improved_marker_feedback}
    )[0]
    submission.save()

    return submission

def populate():
    # Add course leads
    add_course_lead('lead1')
    add_course_lead('lead2')
    print("Added course leads: lead1, lead2")

    # Add markers
    add_marker('gta1')
    add_marker('gta2')
    add_marker('gta3')
    print("Added markers: gta1, gta2, gta3")

    # Add courses
    add_course('CS101', 'Introduction to Computer Science', 'lead1', ['gta1', 'gta2', 'gta3'])
    add_course('CS102', 'Data Structures and Algorithms', 'lead2', ['gta2', 'gta3'])
    print("Added courses: CS101, CS102")

    # Add assignments
    add_assignment('Assignment 1', 'CS101', ['gta1', 'gta2'], 'cs101_1_spec.docx')
    add_assignment('Assignment 2', 'CS102', ['gta2', 'gta3'])
    print("Added assignments: Assignment 1, Assignment 2")

    # Add submissions
    add_marked_submission('Assignment 1', '12345678', 'gta1', marker_grade=75.0, initial_marker_feedback='Good work!')
    add_marked_submission('Assignment 1', '87654321', 'gta2', marker_grade=90.0, initial_marker_feedback='Excellent!', improved_marker_feedback='Excellent work! You have...')
    add_marked_submission('Assignment 2', '11111111', 'gta2', marker_grade=68.0, initial_marker_feedback='Good effort!', improved_marker_feedback='Good effort! Note that...')
    add_marked_submission('Assignment 2', '22222222', 'gta3', marker_grade=92.0, initial_marker_feedback='Outstanding work!')
    print("Added submissions for students: 12345678, 87654321, 11111111, 22222222")

    print("Platform population completed successfully.")

if __name__ == '__main__':
    print("Starting platform population script...")
    populate()