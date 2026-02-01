from django.conf import settings
from django.db import models


class Project(models.Model):
    ICON_CHOICES = [
        ('folder', 'Папка'),
        ('briefcase', 'Портфель'),
        ('rocket', 'Ракета'),
        ('star', 'Звезда'),
        ('heart', 'Сердце'),
        ('lightning', 'Молния'),
        ('gear', 'Шестеренка'),
        ('code', 'Код'),
        ('palette', 'Палитра'),
        ('music', 'Музыка'),
        ('camera', 'Камера'),
        ('book', 'Книга'),
    ]

    COLOR_CHOICES = [
        ('purple', 'Фиолетовый'),
        ('blue', 'Синий'),
        ('cyan', 'Голубой'),
        ('green', 'Зеленый'),
        ('yellow', 'Желтый'),
        ('orange', 'Оранжевый'),
        ('red', 'Красный'),
        ('pink', 'Розовый'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='folder')
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='purple')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def create_default_columns(self):
        """Создает стандартные колонки для нового проекта"""
        defaults = [
            ('К выполнению', '#64748b', 0),
            ('В работе', '#f59e0b', 1),
            ('Готово', '#10b981', 2),
        ]
        for name, color, order in defaults:
            Column.objects.create(project=self, name=name, color=color, order=order)


class Column(models.Model):
    """Колонки (статусы) проекта - создаются пользователем"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='#64748b')  # HEX цвет
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Label(models.Model):
    """Метки для задач"""
    COLOR_CHOICES = [
        ('gray', 'Серый'),
        ('red', 'Красный'),
        ('orange', 'Оранжевый'),
        ('yellow', 'Желтый'),
        ('green', 'Зеленый'),
        ('blue', 'Синий'),
        ('purple', 'Фиолетовый'),
        ('pink', 'Розовый'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='blue')

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"
        URGENT = "urgent", "Срочный"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="tasks", null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    labels = models.ManyToManyField(Label, blank=True, related_name='tasks')
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-updated_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date:
            from django.utils import timezone
            return self.due_date < timezone.now().date()
        return False

    @property
    def completed_checklist_count(self):
        return self.checklist_items.filter(is_completed=True).count()

    @property
    def total_checklist_count(self):
        return self.checklist_items.count()


class ChecklistItem(models.Model):
    """Пункты чеклиста (подзадачи)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    text = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class Message(models.Model):
    """Сообщения чата в задаче"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"