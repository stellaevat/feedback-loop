from django.contrib import admin
from app.models import UserProfile, Course, Assignment, MarkedSubmission

class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('code',)}

admin.site.register(UserProfile)
admin.site.register(Course, CourseAdmin)
admin.site.register(Assignment)
admin.site.register(MarkedSubmission)