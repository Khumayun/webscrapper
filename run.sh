#!/bin/bash
set -e

# Install chromium
apt-get update
apt-get install -y chromium

# Install other dependencies as needed
pip install -r requirements.txt

gunicorn -b :5000 app:app
