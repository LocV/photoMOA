#!/bin/bash

echo "🎯 PhotoMOA Setup Test"
echo "====================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the PhotoMOA root directory"
    exit 1
fi

echo "✅ Project structure looks good"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✅ Python 3 is available"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js"
    exit 1
fi

echo "✅ Node.js is available"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Run './setup.sh' first"
    exit 1
fi

echo "✅ Virtual environment exists"

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Node modules not found. Run './setup.sh' first"
    exit 1
fi

echo "✅ Node modules installed"

# Check if ports are available
if lsof -i :5001 &> /dev/null; then
    echo "⚠️  Port 5001 is in use. You may need to stop other services"
else
    echo "✅ Port 5001 is available"
fi

if lsof -i :3000 &> /dev/null; then
    echo "⚠️  Port 3000 is in use. React will ask to use a different port"
else
    echo "✅ Port 3000 is available"
fi

echo ""
echo "🚀 Setup looks good! Follow these steps to start the application:"
echo ""
echo "1. Start the backend (in one terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "📖 For detailed instructions, see START_GUIDE.md"
