from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Projects
    path("project/new/", views.project_create, name="project_create"),
    path("p/<slug:slug>/", views.project_board, name="project_board"),

    # Columns
    path("p/<slug:slug>/column/new/", views.column_create, name="column_create"),
    path("column/<int:column_id>/edit/", views.column_edit, name="column_edit"),
    path("column/<int:column_id>/delete/", views.column_delete, name="column_delete"),

    # Tasks
    path("p/<slug:slug>/task/new/", views.task_create, name="task_create"),
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("task/<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("task/<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("task/<int:task_id>/move/", views.task_move, name="task_move"),
    path("task/<int:task_id>/chat/", views.task_chat, name="task_chat"),

    # Checklist
    path("task/<int:task_id>/checklist/add/", views.checklist_add, name="checklist_add"),
    path("checklist/<int:item_id>/toggle/", views.checklist_toggle, name="checklist_toggle"),
    path("checklist/<int:item_id>/delete/", views.checklist_delete, name="checklist_delete"),

    # Labels
    path("p/<slug:slug>/label/new/", views.label_create, name="label_create"),
    path("label/<int:label_id>/delete/", views.label_delete, name="label_delete"),
]