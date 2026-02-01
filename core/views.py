from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from .forms import TaskForm, ProjectForm, LabelForm, ColumnForm
from .models import Project, Task, Label, ChecklistItem, Column, Message


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        return render(request, "core/login.html", {"error": "Неверное имя пользователя или пароль"})
    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def home(request):
    projects = Project.objects.order_by("-created_at")
    return render(request, "core/home.html", {"projects": projects})


@login_required
def dashboard(request):
    """Dashboard со статистикой"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Общая статистика
    total_tasks = Task.objects.count()
    my_tasks = Task.objects.filter(created_by=request.user).count()
    overdue_tasks = Task.objects.filter(due_date__lt=today).count()

    # Задачи по приоритетам
    tasks_by_priority = Task.objects.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')

    priority_data = {item['priority']: item['count'] for item in tasks_by_priority}

    # Проекты со статистикой
    projects = Project.objects.annotate(
        task_count=Count('tasks'),
    ).order_by('-created_at')

    # Добавляем статистику по колонкам для каждого проекта
    for project in projects:
        project.columns_stats = []
        for column in project.columns.all():
            project.columns_stats.append({
                'name': column.name,
                'color': column.color,
                'count': column.tasks.count()
            })

    # Последние сообщения в чатах
    recent_messages = Message.objects.select_related(
        'user', 'task', 'task__project'
    ).order_by('-created_at')[:10]

    # Статистика по дням (последние 7 дней) - созданные задачи
    tasks_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Task.objects.filter(created_at__date=day).count()
        tasks_by_day.append({
            'date': day.strftime('%d.%m'),
            'count': count
        })

    context = {
        'total_tasks': total_tasks,
        'my_tasks': my_tasks,
        'overdue_tasks': overdue_tasks,
        'priority_data': priority_data,
        'projects': projects,
        'recent_messages': recent_messages,
        'tasks_by_day': tasks_by_day,
    }

    return render(request, "core/dashboard.html", context)


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            response = HttpResponse()
            response["HX-Redirect"] = f"/p/{project.slug}/"
            return response
    else:
        form = ProjectForm()

    return render(request, "core/partials/project_form.html", {"form": form})


@login_required
def project_board(request, slug):
    project = get_object_or_404(Project, slug=slug)
    columns = project.columns.prefetch_related('tasks__created_by', 'tasks__labels', 'tasks__checklist_items', 'tasks__messages')

    # Filters
    search = request.GET.get("search", "")
    priority = request.GET.get("priority", "")
    label_filter = request.GET.get("label", "")
    due_filter = request.GET.get("due", "")  # overdue, today, week, none
    my_tasks = request.GET.get("my", "")  # "1" = только мои задачи

    # Apply filters to each column's tasks
    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    for column in columns:
        tasks = list(column.tasks.all())

        # Search filter
        if search:
            tasks = [t for t in tasks if search.lower() in t.title.lower()]

        # Priority filter
        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        # Label filter
        if label_filter:
            label_id = int(label_filter)
            tasks = [t for t in tasks if any(lbl.id == label_id for lbl in t.labels.all())]

        # My tasks filter
        if my_tasks:
            tasks = [t for t in tasks if t.created_by == request.user]

        # Due date filter
        if due_filter == "none":
            tasks = [t for t in tasks if t.due_date is None]
        elif due_filter == "overdue":
            tasks = [t for t in tasks if t.due_date and t.due_date < today]
        elif due_filter == "today":
            tasks = [t for t in tasks if t.due_date == today]
        elif due_filter == "week":
            tasks = [t for t in tasks if t.due_date and today <= t.due_date <= week_end]

        column.filtered_tasks = tasks

    context = {
        "project": project,
        "columns": columns,
        "search": search,
        "priority_filter": priority,
        "label_filter": label_filter,
        "due_filter": due_filter,
        "my_tasks": my_tasks,
        "priorities": Task.Priority.choices,
        "labels": project.labels.all(),
    }

    # For HTMX partial updates
    if request.headers.get("HX-Request") and not request.GET.get("full"):
        return render(request, "core/partials/board_columns.html", context)

    return render(request, "core/board.html", context)


@login_required
def task_create(request, slug):
    project = get_object_or_404(Project, slug=slug)
    column_id = request.GET.get("column") or request.POST.get("column")
    column = get_object_or_404(Column, id=column_id, project=project) if column_id else project.columns.first()

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.column = column
            task.created_by = request.user
            task.order = column.tasks.count()
            task.save()

            response = HttpResponse()
            response["HX-Trigger"] = "taskChanged"
            return response

    form = TaskForm()
    return render(request, "core/partials/task_form.html", {
        "form": form,
        "project": project,
        "column": column,
    })


@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            response = HttpResponse()
            response["HX-Trigger"] = "taskChanged"
            return response

    form = TaskForm(instance=task)
    return render(request, "core/partials/task_form.html", {
        "form": form,
        "task": task,
        "project": task.project,
        "column": task.column,
    })


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, "core/partials/task_detail.html", {
        "task": task,
        "checklist_items": task.checklist_items.all()
    })


@login_required
def task_chat(request, task_id):
    """Открытие модалки чата для задачи"""
    task = get_object_or_404(Task, id=task_id)
    return render(request, "core/partials/task_chat.html", {
        "task": task
    })


@login_required
@require_http_methods(["DELETE", "POST"])
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.created_by != request.user:
        return HttpResponse("Forbidden", status=403)

    task.delete()
    response = HttpResponse()
    response["HX-Trigger"] = "taskChanged"
    return response


@login_required
@require_POST
def task_move(request, task_id):
    """Перемещение задачи в другую колонку"""
    task = get_object_or_404(Task, id=task_id)
    column_id = request.POST.get("column_id")
    new_order = request.POST.get("order", 0)

    if column_id:
        column = get_object_or_404(Column, id=column_id, project=task.project)
        task.column = column
        task.order = int(new_order)
        task.save()

    return HttpResponse("OK")


# Column endpoints
@login_required
def column_create(request, slug):
    project = get_object_or_404(Project, slug=slug)

    if request.method == "POST":
        form = ColumnForm(request.POST)
        if form.is_valid():
            column = form.save(commit=False)
            column.project = project
            column.order = project.columns.count()
            column.save()
            response = HttpResponse()
            response["HX-Trigger"] = "columnChanged"
            return response
    else:
        form = ColumnForm()

    return render(request, "core/partials/column_form.html", {"form": form, "project": project})


@login_required
def column_edit(request, column_id):
    column = get_object_or_404(Column, id=column_id)

    if request.method == "POST":
        form = ColumnForm(request.POST, instance=column)
        if form.is_valid():
            form.save()
            response = HttpResponse()
            response["HX-Trigger"] = "columnChanged"
            return response

    form = ColumnForm(instance=column)
    return render(request, "core/partials/column_form.html", {
        "form": form,
        "column": column,
        "project": column.project
    })


@login_required
@require_http_methods(["DELETE", "POST"])
def column_delete(request, column_id):
    column = get_object_or_404(Column, id=column_id)

    # Нельзя удалить последнюю колонку
    if column.project.columns.count() <= 1:
        return HttpResponse("Cannot delete last column", status=400)

    # Переместить задачи в первую колонку
    first_column = column.project.columns.exclude(id=column.id).first()
    if first_column:
        column.tasks.update(column=first_column)

    column.delete()
    response = HttpResponse()
    response["HX-Trigger"] = "columnChanged"
    return response


# Checklist endpoints
@login_required
@require_POST
def checklist_add(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    text = request.POST.get("text", "").strip()

    if text:
        item = ChecklistItem.objects.create(
            task=task,
            text=text,
            order=task.checklist_items.count()
        )
        return render(request, "core/partials/checklist_item.html", {"item": item, "task": task})

    return HttpResponse("")


@login_required
@require_POST
def checklist_toggle(request, item_id):
    item = get_object_or_404(ChecklistItem, id=item_id)
    item.is_completed = not item.is_completed
    item.save()
    return render(request, "core/partials/checklist_item.html", {"item": item, "task": item.task})


@login_required
@require_http_methods(["DELETE", "POST"])
def checklist_delete(request, item_id):
    item = get_object_or_404(ChecklistItem, id=item_id)
    item.delete()
    return HttpResponse("")


# Label endpoints
@login_required
def label_create(request, slug):
    project = get_object_or_404(Project, slug=slug)

    if request.method == "POST":
        form = LabelForm(request.POST)
        if form.is_valid():
            label = form.save(commit=False)
            label.project = project
            label.save()
            response = HttpResponse()
            response["HX-Trigger"] = "labelChanged"
            return response

    form = LabelForm()
    return render(request, "core/partials/label_form.html", {"form": form, "project": project})


@login_required
@require_http_methods(["DELETE", "POST"])
def label_delete(request, label_id):
    label = get_object_or_404(Label, id=label_id)
    label.delete()
    response = HttpResponse()
    response["HX-Trigger"] = "labelChanged"
    return response