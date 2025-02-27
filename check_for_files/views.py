import json
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv


@csrf_exempt
@require_http_methods(["POST"])
def execute_command(request):
    pass
