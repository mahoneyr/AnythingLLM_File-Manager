import os
import socket

import paramiko
import requests
from dotenv import load_dotenv

from .models import links_to_check, page_error


def check_all_servers():
    pass