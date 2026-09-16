"""PythonAnywhere WSGI Configuration Script for nexgenwebpos.

Copy or point your PythonAnywhere WSGI configuration to this file:
/var/www/nexgenpos_pythonanywhere_com_wsgi.py
"""

import sys
import os

# 1. Project Directory Path (adjust username if needed)
path = '/home/nexgenpos/POS_V2/nexgenwebpos'
if not os.path.exists(path):
    path = '/home/nexgenpos/nexgenwebpos'
if path not in sys.path:
    sys.path.insert(0, path)

# 2. Virtual Environment site-packages path
virtualenv_path = '/home/nexgenpos/.virtualenvs/pos_env/lib/python3.10/site-packages'
if os.path.exists(virtualenv_path) and virtualenv_path not in sys.path:
    sys.path.insert(0, virtualenv_path)

# 3. Load .env file
from dotenv import load_dotenv
env_file = os.path.join(path, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# 4. Import application object for WSGI server
from app import app as application
