#!/usr/bin/env bash

set -e  # exit immediately on error

echo "Starting project setup..."

### BACKEND ###
echo "Setting up backend..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Run backend (modify as needed)
echo "Running backend..."
uvicorn local_api:app &


### FRONTEND ###
echo "Setting up frontend..."
cd web_ui

# Install node modules
if [ ! -d "node_modules" ]; then
  echo "Installing npm dependencies..."
  npm install
fi

# Run frontend
echo "▶️ Running frontend..."
npm run dev

echo "App is running!"
