#!/bin/bash

cd /home/kyonshi0104/discord/bots/kyonshi-botv3 || exit 1

echo "Pulling latest changes..."
git pull origin main || exit 2

echo "Installing requirements..."
./venv/bin/pip install -r requirements.txt

echo "Starting bot..."
./venv/bin/python main.py
