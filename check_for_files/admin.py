from django.contrib import admin

from .models import FileInfo, TaskError

# Register your models here.
admin.site.register(TaskError)
admin.site.register(FileInfo)
