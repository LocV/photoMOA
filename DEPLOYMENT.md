# PhotoMOA Deployment Guide

Your PhotoMOA application has been successfully deployed to Firebase Hosting!

## 🎉 Frontend Deployed Successfully

**Live URL**: https://bulletbaseai.web.app

Your React frontend is now live and accessible at the above URL.

## Backend Deployment Options

The Python backend requires additional setup for Firebase Functions. Here are your options:

### Option 1: Use Google Cloud Run (Recommended)

The easiest way to deploy the Python backend is using Google Cloud Run:

1. **Enable Google Cloud Run API**:
   ```bash
   gcloud services enable run.googleapis.com
   ```

2. **Create a Dockerfile for the backend**:
   ```dockerfile
   FROM python:3.10
   
   WORKDIR /app
   COPY backend/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY backend/ .
   
   ENV PORT=8080
   CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
   ```

3. **Deploy to Cloud Run**:
   ```bash
   cd backend
   gcloud run deploy photomoa-api --source . --platform managed --region us-central1 --allow-unauthenticated
   ```

4. **Update frontend configuration**:
   Update `frontend/src/config.ts` to point to your Cloud Run URL in production.

### Option 2: Use Railway, Render, or Heroku

Deploy the backend to any Python-compatible platform:

- **Railway**: `railway new` and deploy the backend folder
- **Render**: Connect your GitHub repo and deploy the backend as a web service
- **Heroku**: `heroku create photomoa-api` and deploy

### Option 3: Set up Python 3.10+ for Firebase Functions

If you prefer Firebase Functions:

1. **Install Python 3.10+**:
   ```bash
   brew install python@3.10  # macOS
   ```

2. **Recreate virtual environment**:
   ```bash
   cd functions
   rm -rf venv
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Deploy**:
   ```bash
   firebase deploy
   ```

## Current Status

✅ **Frontend**: Deployed and live at https://bulletbaseai.web.app  
⚠️ **Backend**: Needs deployment (see options above)

## Configuration

The frontend is configured to:
- Use `http://localhost:5001/api` in development
- Use `/api` in production (expecting backend at same domain)

Once you deploy your backend, update the `config.ts` file if needed to point to the correct backend URL.

## Files Updated for Deployment

1. **Firebase Configuration**: `firebase.json` and `.firebaserc` created
2. **API Configuration**: `frontend/src/config.ts` for environment-based API URLs  
3. **Frontend Build**: Production build created in `frontend/build/`
4. **Functions Setup**: Python environment and dependencies in `functions/`

## Next Steps

1. Choose a backend deployment option from above
2. Deploy your Python backend  
3. Update frontend config if the backend URL differs from `/api`
4. Test the full application

Your PhotoMOA application architecture:
- **Frontend**: React app with Tailwind CSS → Firebase Hosting
- **Backend**: Flask API with OpenCV, NumPy, SciPy → Your chosen platform
- **Storage**: Will use the backend platform's storage or Google Cloud Storage
- **Database**: Will use the backend platform's storage or Firebase Firestore

The application includes all your features:
- Target image upload and analysis
- Shot detection with multiple algorithms
- Manual shot addition with click interface
- Scale calibration with drag-and-click
- MOA calculations with calibrated measurements
- History management with delete functionality
- Responsive UI with professional styling
