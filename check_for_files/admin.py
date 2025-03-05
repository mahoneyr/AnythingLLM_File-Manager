from django.contrib import admin

from .models import FileInfo, TaskError, created_workspaces

# Register your models here.
admin.site.register(TaskError)
admin.site.register(FileInfo)
admin.site.register(created_workspaces)
