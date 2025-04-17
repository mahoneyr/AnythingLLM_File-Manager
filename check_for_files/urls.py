from django.urls import path

from .views import *

app_name = "pingLinks"

urlpatterns = [
    path("update/", full_upload_and_cleaning, name="update"),
    path("sort/", sort_files, name="sort"),
    path("clean/", clean_folders, name="clean"),
    path("scan/", get_file_differences, name="scan"),
    path("create_image_descriptions/", create_image_descriptions, name="create_image_descriptions"),
]
