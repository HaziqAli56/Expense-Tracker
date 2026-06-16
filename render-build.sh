#!/usr/bin/env bash
# exit on error
set -o errexit

# Install tesseract
apt-get update && apt-get install -y tesseract-ocr

# Install pip requirements (ye zaroori hai)
pip install -r requirements.txt