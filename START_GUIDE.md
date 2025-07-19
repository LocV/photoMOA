# PhotoMOA - Quick Start Guide

## Prerequisites
- Python 3.9+ installed
- Node.js and npm installed
- macOS (tested on macOS)

## Step 1: Start the Backend Server

Open a terminal and navigate to the PhotoMOA project directory:

```bash
cd /Users/lvuu/Developer/photoMOA
```

Start the backend server:

```bash
cd backend
source venv/bin/activate
python app.py
```

You should see output like:
```
* Running on http://127.0.0.1:5001
* Debug mode: on
```

**Leave this terminal open** - the backend server needs to keep running.

## Step 2: Test the Backend (Optional)

Open a **new terminal** and test the backend:

```bash
cd /Users/lvuu/Developer/photoMOA/backend
source venv/bin/activate
python test_backend.py
```

You should see:
```
✓ Backend health check passed
✓ History endpoint working
```

## Step 3: Start the Frontend

Open a **new terminal** (keep the backend running in the first terminal):

```bash
cd /Users/lvuu/Developer/photoMOA/frontend
npm start
```

This will:
- Start the React development server
- Automatically open your browser to `http://localhost:3000`
- Show the PhotoMOA web interface

## Step 4: Test the Application

1. **Upload a Target Photo**:
   - Click on the upload area or drag and drop an image file
   - Supported formats: JPEG, JPG, PNG, GIF, BMP
   - The app will analyze the image and detect shots

2. **View Results**:
   - See the number of shots detected
   - View the calculated MOA value
   - See the annotated image with highlighted shots

3. **Check History**:
   - Click the "History" tab to see all previous uploads
   - View past results and images

## Troubleshooting

### Backend Issues
- If port 5001 is busy, the backend will fail to start
- Check if anything else is running on port 5001: `lsof -i :5001`
- Kill any processes using the port: `kill <PID>`

### Frontend Issues
- If port 3000 is busy, React will ask to use a different port
- Type 'y' to accept the alternative port

### Connection Issues
- Make sure both backend (port 5001) and frontend (port 3000) are running
- Check that the backend is accessible: `curl http://localhost:5001/api/health`

## Test with Sample Images

For best results, use images with:
- Clear, high-contrast target backgrounds
- Visible shot holes
- Good lighting
- Minimal shadows or glare

## Stopping the Application

1. Stop the frontend: Press `Ctrl+C` in the frontend terminal
2. Stop the backend: Press `Ctrl+C` in the backend terminal

## Quick Test Commands

```bash
# Test backend health
curl http://localhost:5001/api/health

# Test backend history
curl http://localhost:5001/api/history

# Check if ports are available
lsof -i :5001  # Backend port
lsof -i :3000  # Frontend port
```
