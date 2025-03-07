from django.urls import path

from .views import upload

app_name = "pingLinks"

urlpatterns = [
    path("update/", upload),
    # path("redeploy/execute/", views.execute_command, name="execute_command"),
]
