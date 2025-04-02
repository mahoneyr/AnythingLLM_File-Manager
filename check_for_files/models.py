from django.db import models


class TaskError(models.Model):
    """Model to track task execution and errors"""

    date = models.DateTimeField(auto_now_add=True)
    error = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"Task execution at {self.date} - {'Success' if self.success else 'Failed'}"
        )


class FileInfo(models.Model):
    filename = models.CharField(max_length=255)
    absolute_path = models.CharField(max_length=1024)
    main_folder = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    created_at = models.DateTimeField()
    modified_at = models.DateTimeField()

    def __str__(self):
        return f" {self.id} - {self.filename} - {self.absolute_path} - {self.main_folder}"


class created_workspaces(models.Model):
    name = models.CharField(max_length=255)
