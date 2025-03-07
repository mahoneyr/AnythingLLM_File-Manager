import json
import os

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .tasks import anythingLLM_update


@api_view(["POST"])
def upload(request):
    finished_text = anythingLLM_update()
    return Response(finished_text, status=status.HTTP_200_OK)
