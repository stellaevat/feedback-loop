# Documentation: Feedback Loop

**Platform name:** Feedback Loop

**Technology:**

- Python 3.10 or newer
- Django 5.2
- SQLite, configured as the default database
- Vanilla HTML, CSS and JavaScript

**Author:** Stella Eva Tsiapali
**Year:** 2026  
**Institution:** Imperial College London  
**Supervisors:** Iro Ntonia (Centre for Higher Education Research and Scholarship); Zohaib Akhtar (Department of Electrical and Electronic Engineering)


## 1. Overview

Feedback Loop is a Django-based web application to support the provision, improvement, and moderation of student feedback at scale. It is designed around two main user roles:

- **Course leads:** create and manage courses and assignments, assign markers, configure grade & LLM-aided feedback moderation, inspect all marked submissions;
- **Markers:** mark assigned submissions and request pedagogically-informed LLM-generated suggestions, which they can use to improve their initial feedback.

The current implementation provides a working foundation for:

- Course and assignment management;
- Assignment specification and rubric uploads;
- Marker assignment at course and assignment level;
- Recording student identifiers, grades and marker feedback;
- Grade moderation using linear scaling or z-score scaling;
- Storage and display of improved feedback, moderated feedback and LLM-generated suggestions;
- CSV export of assignment results;
- Temporary local username/password authentication.

The LLM-related functions are currently placeholders, and server deployment/SSO authentication are to be implemented.

## 2. Repository structure

The repository contains one Django project (`project`), containing a single application (`app`):

```text
project/
├── manage.py                         Django command-line entry point
├── requirements.txt                  Python dependencies
├── populate_platform.py              Example database population script
├── app/
│   ├── admin.py                       Django admin registrations
│   ├── apps.py                        Django application configuration
│   ├── forms.py                       Course, assignment, moderation and marking forms
│   ├── grade_moderation.py            Grade moderation algorithms
│   ├── models.py                      Database models
│   ├── tests.py                       Test module placeholder
│   ├── urls.py                        Application URL routes
│   ├── views.py                       Main logic and workflows
│   └── templatetags/                  Custom template filters
├── project/
│   ├── settings.py                    Django settings
│   ├── urls.py                        Root URL configuration
│   ├── asgi.py                        ASGI entry point
│   └── wsgi.py                        WSGI entry point
├── templates/
│   ├── app/                           Main platform HTML templates
│   └── errors/                        Error page HTML templates
├── static/                            CSS, JavaScript, fonts and favicon assets
└── media/                             Uploaded specifications and rubrics
```

## 3. Application architecture

We follow a conventional Django structure:

1. A browser request reaches the root URL configuration in `project/project/urls.py`.
2. Requests under `/app/` are delegated to `app/urls.py`.
3. View functions in `app/views.py` authenticate the request, enforce role-based access, query or update models and render templates.
4. Forms in `app/forms.py` validate user input and populate model instances.
5. Templates under `templates/app/` render the user interface.
6. `grade_moderation.py` applies deterministic grade transformations under specific moderation algorithms.
7. The future LLM layer should generate prompts and call an LLM service to receive prompts for feedback improvement or feedback moderation outputs.

The current application uses function-based views and Django’s built-in authentication/session middleware.

## 4. Getting started

1. **Create a virtual environment**, from the `project/` directory:

   ```bash
   python -m venv .venv
   ```

   **Activate it on macOS/Linux:**

   ```bash
   source .venv/bin/activate
   ```

   **Activate it on Windows PowerShell:**

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Run database migrations:**

   ```bash
   python manage.py migrate
   ```

4. **Create an administrator**, if required, for example for development or maintenance:

   ```bash
   python manage.py createsuperuser
   ```

5. **Optionally populate development data:**

   ```bash
   python populate_platform.py
   ```

6. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

7. Open `http://127.0.0.1:8000/` in a browser.

## 5. Data model

### User and roles

Django’s built-in `User` model stores usernames, passwords, and account status. `UserProfile` extends it with application-specific role flags:

- `is_staff`
- `is_marker`
- `is_course_lead`

`UserProfile` has a one-to-one relationship with `User`, and the current code for temporary local authentication of pre-existing users expects a `UserProfile` to exist for all existing users.

### Course

A `Course` contains:

- `code`: unique course code, up to 10 characters;
- `name`: optional display name;
- `course_lead`: the responsible `User`;
- `markers`: users assigned to mark within the course;
- `slug`: generated from the course code and used in URLs.

The `save()` method regenerates the slug from the course code using Django’s `slugify` function.

### Assignment

An `Assignment` belongs to one `Course` and contains:

- `name`: unique display name;
- `course`: the course within which the assignment was created;
- `markers`: Users from the course markers specifically assigned to mark this assignment;
- `spec` and `rubric`: optional file uploads;
- Grade moderation settings;
- Feedback moderation settings.

Grade moderation choices are:

- `linear`: using a float multiplier and shift;
- `z-score`: mapping the raw distribution to a target mean and target standard deviation.

Feedback moderation fields currently include:

- `feedback_tone`: formal or friendly;
- `feedback_length_min` and `feedback_length_max`;
- `feedback_moderation_requests`: free-text requests from the course lead;
- `feedback_moderation_prompt`: generated prompt storage field, currently populated with a placeholder.

Assignment names are unique within a course.

### MarkedSubmission

A `MarkedSubmission` represents one marker’s marking for one student in one assignment. It stores:

- `student_cid`: an eight-digit numeric student identifier;
- `marker`: the `User` who marked it;
- `assignment`: the `Assignment` for which the student is being marked;
- `marker_grade`: the original grade;
- `initial_marker_feedback`: the marker’s first feedback draft;
- `suggested_improvements`: LLM-generated suggestions;
- `improved_marker_feedback`: the marker’s revised feedback;
- `moderated_grade`: grade after assignment-level moderation;
- `moderated_feedback`: feedback after assignment-level feedback moderation.

The combination of assignment, student identifier and marker is unique.

## 6. Main user workflows

### Course lead workflow

1. Log in;
2. Open My Courses;
3. Create a course and select course markers;
4. Open the course and create an assignment;
5. Upload the assignment specification and/or rubric;
6. Assign markers from the course’s marker pool;
7. Configure grade moderation if required;
8. Configure feedback moderation preferences, if required;
9. Review marked submissions and export a CSV;
10. Apply grade moderation or request feedback moderation.

### Marker workflow

1. Log in;
2. Open a course and assignment to which the marker has been assigned;
3. Create a marked submission record;
4. Enter the student CID, grade and initial feedback;
5. Save the submission or select **Check feedback** to request LLM-generated suggested improvements;
6. Review the suggestions and write the final improved feedback;
7. Update the submission.

## 7. URL and view reference

Application routes are defined in `project/app/urls.py` and mounted under `/app/` by the root URL configuration.

| Route purpose | URL pattern | Access |
|---|---|---|
| Homepage | `/` and `/app/` | Public |
| My courses | `/app/my-courses/` | Authenticated |
| Create course | `/app/new-course/` | Course lead |
| View course | `/app/course-<course_slug>/` | Assigned lead or marker |
| Manage course | `/app/course-<course_slug>/manage/` | Course lead |
| Delete course | `/app/course-<course_slug>/delete/` | Course lead |
| Create assignment | `/app/course-<course_slug>/new-assignment/` | Course lead |
| View assignment | `/app/course-<course_slug>/assignment-<assignment_id>/` | Assigned lead or marker |
| Export CSV | `/app/course-<course_slug>/assignment-<assignment_id>/export_csv/` | Assigned lead or marker (with marker only able to export their own marked submissions) |
| Manage assignment | `/app/course-<course_slug>/assignment-<assignment_id>/manage/` | Course lead |
| Delete assignment | `/app/course-<course_slug>/assignment-<assignment_id>/delete/` | Course lead |
| New marked submission | `/app/course-<course_slug>/assignment-<assignment_id>/mark_new_submission/` | Assigned lead or marker |
| Existing submission | `/app/course-<course_slug>/assignment-<assignment_id>/submission-<submission_id>/` | Lead or submission marker |
| Delete submission | `/app/course-<course_slug>/assignment-<assignment_id>/submission-<submission_id>/delete/` | Lead or submission marker |
| Login | `/app/login/` | Public |
| Logout | `/app/logout/` | Authenticated |

The application also includes Django’s administrative interface at `/admin/`.

## 8. Forms and validation

`app/forms.py` defines the following forms:

- `CourseForm`: creates or updates courses and selects course markers;
- `AssignmentForm`: creates or updates assignments, uploads files and selects assignment markers;
- `GradeModerationForm`: selects a moderation algorithm and its parameters;
- `FeedbackModerationForm`: captures tone, length range and additional moderation requests;
- `MarkedSubmissionForm`: captures student CID, grade, initial feedback, suggested improvements and final feedback;
- `UserForm`: temporary local login form.

Important validation behaviour includes:

- Assignment names are validated to be unique within a course;
- Duplicate marked submissions for the same Assignment, marker, and student are rejected;
- Course codes are converted to uppercase, and Course/Assignment names are converted to title case, to enforce case-insensitive uniqueness;
- A marker can only be assigned to an Assignment if they are assigned to the relevant Course;
- Student CIDs must contain exactly eight numeric characters;
- Grades are currently constrained to the range 0–100.

## 9. Grade moderation

`app/grade_moderation.py` currently provides two deterministic grade moderation algorithms:

- **Linear scaling:** a raw grade is transformed using a multiplier and shift, i.e.

  $$
  \text{moderated grade} = \text{raw grade} \times \text{multiplier} + \text{shift}
  $$

- **Z-score scaling:** the raw grade distribution is transformed using its mean and standard deviation, and mapped to target values, i.e.

  $$
  \text{moderated grade} = \left(\frac{\text{raw grade} - \text{raw mean}}{\text{raw standard deviation}}\right) \times \text{target standard deviation} + \text{target mean}
  $$

Results are currently rounded to one decimal place, and only `MarkedSubmissions` with non-null grades are considered. Grade capping (min or max) could be added if deemed appropriate, although course leads can view the results of the grade moderation and repeat as required.

## 10. LLM-related work remaining

The most important unfinished functionality is in `app/views.py`:

```python
# TODO: LLM-related processes left to implement

def get_feedback_moderation_prompt(assignment):
    return "Moderation prompt created."

def get_suggested_improvements_prompt(submission):
    return "Improvement prompts created."

def generate_suggested_improvements(submission):
    return "You should consider..."
```

These functions currently return placeholders. They should be replaced with tested workflows that maintain separation between prompt construction and LLM communication, as indicated by the placeholder methods.

### 10.1 Prompt generation for suggested improvements

`get_suggested_improvements_prompt(submission)` should construct a prompt using the minimum information needed to support useful feedback revision, likely including:

- The assignment specification, if available;
- The rubric, if available;
- The marker’s initial feedback;
- The grade, where pedagogically appropriate;
- Explicit instructions about the intended student audience and feedback purpose.

### 10.2 Prompt generation for feedback moderation

`get_feedback_moderation_prompt(assignment)` should create a reusable (saved) moderation instruction based on the course lead’s settings:

- Desired tone, if specified;
- Minimum and maximum length, if specified;
- Additional moderation requests, if provided;
- Assignment specification and rubric;
- Expected educational level and learning outcomes.

The system should preserve the original feedback and make the moderated output reviewable, rather than replacing the marker’s text, as expected by the existing `MarkedSubmission` model fields.

### 10.3 Pedagogical context for feedback generation and moderation

Feedback Loop’s aim is to stay pedagogically informed. LLM prompts should, therefore, be designed around learning and improvement from a research-based pedagogical perspective. For example:

- **Feedback should be formative and actionable**, to help a student understand and improve:
  - What they did well and what needs improvement (**feedback**);
  - Why the issue matters in relation to the learning goals or rubric (**feed-up**);
  - What specific next step they can take (**feed-forward**).
- **Feedback should be specific, evidence-based, spec- and rubric-aligned:**
  - The improved and moderated feedback should be grounded in the assignment specification, rubric, marking criteria and learning outcomes.
  - Feedback should identify specific features of the student’s work and connect them to a criterion.
  - The LLM should be instructed not to invent criteria, penalise work for requirements absent from the rubric, or make claims that cannot be supported by the supplied evidence. Similarly, if evidence is insufficient, the model should say so rather than hallucinating details.
- **Feedback should be balanced and respectful:**
  - The requested tone should remain professional, respectful and inclusive.
  - “Friendly” should not mean informal, patronising or excessively positive.
  - “Formal” should not mean cold or opaque.

Importantly, the feedback provided on Feedback Loop should preserve marker judgement, without erasing useful variation:

- The LLM suggestions should remain advisory (as expected by the current implementation), so the marker or course lead can remain responsible for the academic judgement.
- The interface should maintain its current clarity on which text was written by the marker, which was suggested by the LLM and which was finally approved or edited by a human.
- The suggestions should preserve valid disciplinary and marker-specific insights, while identifying any feedback that is unsupported, vague, inappropriate or inconsistent with the rubric.
- Before deployment, the project should define an evaluation process involving representative assignments, marker feedback, and expert review. Evaluation criteria should include alignment with criteria, actionability, accuracy, tone, fairness, usefulness to students and the rate of unsupported claims. Human review should remain part of the release process for high-impact outputs.

### 10.4 Recommended LLM workflow

1. Gather assignment-level pedagogical context;
2. Gather the relevant submission feedback and grade;
3. Remove or minimise personal data;
4. Generate a structured prompt;
5. Submit the request through a dedicated LLM client;
6. Parse and validate the response;
7. Store the output separately from human-authored feedback;
8. Display the output as a suggestion or moderation draft;
9. Require human review and editing.

## 11. Important deployment configuration & testing notes

The checked-in settings currently use development-oriented configuration (`project/settings.py`):

- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- SQLite as the database
- A hard-coded Django secret key
- Development media serving

Before deployment:

1. Move the secret key to an environment variable and rotate the exposed development key;
2. Set `DEBUG = False`;
3. Configure `ALLOWED_HOSTS` and CSRF trusted origins;
4. Use a production database and configure backups;
5. Run `python manage.py collectstatic` and serve static files through server;
6. Review role management and ensure profile records are created reliably for every user acquired from the College’s SSO system;
7. Do not use the sample credentials from `populate_platform.py` in any shared environment;
8. Run Django's deployment checks `python manage.py check --deploy` before release.

`app/tests.py` currently contains no substantive tests. Before the platform is used with real data, add tests for:

- Model constraints and deletion behaviour;
- Course lead and marker permissions;
- Cross-course and cross-assignment access attempts;
- Course and assignment form validation;
- Student CID and grade validation;
- Grade moderation calculations, including zero-variance and missing-grade cases;
- CSV export permissions and contents;
- Authentication and SSO callback behaviour;
- LLM prompt generation using representative pedagogical scenarios.

Run the Django checks and tests with:

```bash
python manage.py check
python manage.py test
```