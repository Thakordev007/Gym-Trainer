"""
core/urls.py

Every page path here matches a plain href already used inside the templates
(templates use plain paths like /login/ instead of the {% url %} tag).
The extra "AJAX" paths at the bottom of each group are new — they're called
via fetch() from the matching static/js/*.js file, not linked directly from
any template href.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Public marketing site
    path("", views.home, name="home"),

    # Accounts
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),

    # Onboarding wizard
    path("onboarding/goal/", views.onboarding_goal, name="onboarding_goal"),
    path("onboarding/body-details/", views.onboarding_body_details, name="onboarding_body_details"),
    path("onboarding/workout-preferences/", views.onboarding_preferences, name="onboarding_workout_preferences"),
    path("onboarding/equipment/", views.onboarding_equipment, name="onboarding_equipment"),
    path("onboarding/summary/", views.onboarding_summary, name="onboarding_summary"),
    path("onboarding/generate/", views.onboarding_generate, name="onboarding_generate"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/workout-plan/", views.workout_plan, name="workout_plan"),
    path("dashboard/workout-detail/<slug:day>/", views.workout_detail, name="workout_detail"),
    path("dashboard/workout-session/", views.workout_session, name="workout_session"),
    path("dashboard/diet-plan/", views.diet_plan, name="diet_plan"),
    path("dashboard/progress/", views.progress_view, name="progress"),
    path("dashboard/activity/", views.activity_view, name="activity"),
    path("dashboard/profile/", views.profile_view, name="profile"),
    path("dashboard/profile/edit/", views.profile_edit, name="profile_edit"),
    path("dashboard/profile/preferences/", views.profile_preferences, name="profile_preferences"),
    path("dashboard/profile/change-password/", views.profile_change_password, name="profile_change_password"),

    # Dashboard AJAX
    path("dashboard/exercise/<int:de_id>/toggle/", views.toggle_exercise, name="toggle_exercise"),
    path("dashboard/exercise/<int:de_id>/log/", views.log_exercise, name="log_exercise"),
    path("dashboard/workout-session/complete-set/", views.complete_set, name="complete_set"),
    path("dashboard/notifications/mark-all-read/", views.mark_all_read, name="mark_all_read"),
    path("dashboard/photo/add/", views.add_progress_photo, name="add_progress_photo"),

    # AI Assistant
    path("ai-assistant/", views.ai_assistant, name="ai_assistant"),
    path("ai-assistant/send/", views.ai_assistant_send, name="ai_assistant_send"),

    # Custom admin panel (separate from Django's built-in /admin/)
    path("admin-panel/login/", views.admin_login, name="admin_login"),
    path("admin-panel/logout/", views.admin_logout, name="admin_logout"),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/<int:user_id>/", views.admin_user_detail, name="admin_user_detail"),
    path("admin-panel/users/<int:user_id>/toggle-active/", views.admin_toggle_user, name="admin_toggle_user"),
    path("admin-panel/ai-activity/", views.admin_ai_activity, name="admin_ai_activity"),
    path("admin-panel/workouts/", views.admin_workouts, name="admin_workouts"),
    path("admin-panel/exercises/", views.admin_exercises, name="admin_exercises"),
    path("admin-panel/diet-plans/", views.admin_diet_plans, name="admin_diet_plans"),
    path("admin-panel/progress/", views.admin_progress, name="admin_progress"),
    path("admin-panel/notifications/", views.admin_notifications, name="admin_notifications"),
    path("admin-panel/notifications/broadcast/", views.admin_broadcast, name="admin_broadcast"),
    path("admin-panel/settings/", views.admin_settings, name="admin_settings"),
    path("admin-panel/settings/save/", views.admin_settings_save, name="admin_settings_save"),
]
