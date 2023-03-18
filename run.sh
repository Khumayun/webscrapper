#!/bin/bash
set -e

# Install chromium
sudo apt-get update
sudo apt-get install -y chromium

# Install other dependencies as needed
pip install -r requirements.txt

gunicorn -b :8080 app:app
