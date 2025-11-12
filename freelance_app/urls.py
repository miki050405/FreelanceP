from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("tasks/", views.tasks_list, name="tasks_list"),
    path("tasks/<int:task_id>/respond/", views.respond_to_task, name="respond_to_task"),
    path(
        "response/<int:pk>/status/",
        views.response_set_status,
        name="response_set_status",
    ),
    path("profile/<int:user_id>/", views.profile_public_view, name="profile_public"),
    path("response/<int:pk>/cancel/", views.response_cancel, name="response_cancel"),
    path("notifications/", views.notifications_list, name="notifications"),
    path(
        "notifications/settings/",
        views.notification_settings,
        name="notification_settings"
    ),

]
