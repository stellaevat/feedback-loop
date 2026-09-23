from django.urls import path
from app import views

app_name = 'app'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('new-course/', views.new_course, name='new_course'),
    path('course-<str:course_slug>/', views.view_course, name='view_course'),
    path('course-<str:course_slug>/manage/', views.manage_course, name='manage_course'),
    path('course-<str:course_slug>/delete/', views.delete_course, name='delete_course'),
    path('course-<str:course_slug>/new-assignment/', views.new_assignment, name='new_assignment'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/', views.view_assignment, name='view_assignment'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/export_csv/', views.export_csv, name='export_csv'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/manage/', views.manage_assignment, name='manage_assignment'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/mark_new_submission/', views.mark_submission, name='mark_new_submission'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/submission-<int:submission_id>/', views.mark_submission, name='mark_existing_submission'),
    path('course-<str:course_slug>/assignment-<int:assignment_id>/submission-<int:submission_id>/delete/', views.delete_submission, name='delete_submission'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
]