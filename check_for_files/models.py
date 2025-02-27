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
