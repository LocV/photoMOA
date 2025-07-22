#!/bin/bash

echo "🎯 Starting PhotoMOA Backend Server..."
echo "======================================"

cd backend

# Activate virtual environment
source venv/bin/activate

# Start the Flask app
echo "Starting Flask server on http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
