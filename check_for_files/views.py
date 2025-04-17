import json
import os

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .tasks import main
from .sort_files import SortFiles
from .tasks import FileScanner, AnythingLLM_API_Client

@api_view(["POST"])
def full_upload_and_cleaning(request):
    print("Uploading files")
    finished_text = main()
    return Response(finished_text, status=status.HTTP_200_OK)

@api_view(["POST"])
def sort_files(request):
    sort_files = SortFiles()
    files_moved = sort_files.sort_files()
    sort_files.reset()
    return Response(f"Files sorted: {files_moved}", status=status.HTTP_200_OK)

@api_view(["POST"])
def clean_folders(request):
    anything_llm_api_client = AnythingLLM_API_Client()
    anything_llm_api_client.delete_unused_folders()
    anything_llm_api_client.reset()
    return Response("Folders cleaned", status=status.HTTP_200_OK)

@api_view(["GET"])
def get_file_differences(request):
    file_scanner = FileScanner(verbose=False)
    files_to_add, files_that_changed, files_got_deleted  = file_scanner.scan_files()
    file_scanner.reset()
    return Response(f"Files to add: {files_to_add}, Files that changed: {files_that_changed}, Files got deleted: {files_got_deleted}", status=status.HTTP_200_OK)

@api_view(["POST"])
def create_image_descriptions(request):
    file_scanner = FileScanner(verbose=False)
    file_scanner.create_image_descriptions()
    file_scanner.reset()
    return Response("Image descriptions created", status=status.HTTP_200_OK)


