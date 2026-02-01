from django.contrib import admin
from .models import Project, Column, Task, Label, ChecklistItem, Message


class ColumnInline(admin.TabularInline):
    model = Column
    extra = 0
    ordering = ['order']


class LabelInline(admin.TabularInline):
    model = Label
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'task_count', 'created_at']
    list_filter = ['color', 'icon', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ColumnInline, LabelInline]
    readonly_fields = ['created_at']

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Задач'


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'color', 'order', 'task_count']
    list_filter = ['project']
    search_fields = ['name', 'project__name']
    ordering = ['project', 'order']

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Задач'


class ChecklistInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    ordering = ['order']


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['user', 'text', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'column', 'priority', 'due_date', 'created_by', 'is_overdue_display', 'created_at']
    list_filter = ['priority', 'project', 'column', 'created_by', 'due_date']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['labels']
    inlines = [ChecklistInline, MessageInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'project', 'column')
        }),
        ('Детали', {
            'fields': ('priority', 'due_date', 'labels', 'order')
        }),
        ('Метаданные', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_overdue_display(self, obj):
        return '⚠️ Да' if obj.is_overdue else '✓ Нет'
    is_overdue_display.short_description = 'Просрочено'


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'color', 'task_count']
    list_filter = ['project', 'color']
    search_fields = ['name', 'project__name']

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Задач'


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['text', 'task', 'is_completed', 'order']
    list_filter = ['is_completed', 'task__project']
    search_fields = ['text', 'task__title']
    list_editable = ['is_completed']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'user', 'task', 'created_at']
    list_filter = ['user', 'task__project', 'created_at']
    search_fields = ['text', 'user__username', 'task__title']
    readonly_fields = ['user', 'task', 'text', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Сообщение'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False