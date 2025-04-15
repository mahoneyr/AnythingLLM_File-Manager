import json
import os

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .tasks import main


@api_view(["POST"])
def upload(request):
    print("Uploading files")
    finished_text = main()
    return Response(finished_text, status=status.HTTP_200_OK)
   