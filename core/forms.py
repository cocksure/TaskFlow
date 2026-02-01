from django import forms
from django.utils.text import slugify
from .models import Task, Project, Label, Column


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "due_date"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название задачи..."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Добавьте описание (опционально)..."
            }),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }
        labels = {
            "title": "Название",
            "description": "Описание",
            "priority": "Приоритет",
            "due_date": "Срок выполнения",
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "icon", "color"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название проекта..."
            }),
            "icon": forms.RadioSelect(attrs={"class": "icon-radio"}),
            "color": forms.RadioSelect(attrs={"class": "color-radio"}),
        }
        labels = {
            "name": "Название проекта",
            "icon": "Иконка",
            "color": "Цвет",
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        base_slug = slugify(instance.name)
        if not base_slug:
            base_slug = "project"
        slug = base_slug
        counter = 1
        while Project.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug
        if commit:
            instance.save()
            # Создаем колонки по умолчанию для нового проекта
            if not instance.columns.exists():
                instance.create_default_columns()
        return instance


class ColumnForm(forms.ModelForm):
    COLOR_CHOICES = [
        ('#64748b', 'Серый'),
        ('#ef4444', 'Красный'),
        ('#f59e0b', 'Оранжевый'),
        ('#eab308', 'Желтый'),
        ('#22c55e', 'Зеленый'),
        ('#10b981', 'Изумрудный'),
        ('#06b6d4', 'Голубой'),
        ('#3b82f6', 'Синий'),
        ('#8b5cf6', 'Фиолетовый'),
        ('#ec4899', 'Розовый'),
    ]

    color = forms.ChoiceField(choices=COLOR_CHOICES, widget=forms.RadioSelect())

    class Meta:
        model = Column
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Название колонки..."
            }),
        }
        labels = {
            "name": "Название",
            "color": "Цвет",
        }


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Название метки..."
            }),
            "color": forms.RadioSelect(attrs={"class": "color-radio"}),
        }