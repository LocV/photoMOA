# PhotoMOA - Shot Grouping Analysis Tool

PhotoMOA is a web application that analyzes shooting target photos to determine shot groupings and calculate MOA (Minute of Angle) values.

## Features

- Upload target photos through a React web interface
- Automatic shot detection using computer vision
- MOA calculation and grouping analysis
- Visual highlighting of detected shots
- Local storage of photos and results
- History tracking of uploaded targets and MOA values

## Project Structure

```
photoMOA/
├── backend/          # Python Flask API for image processing
│   ├── app.py        # Main Flask application
│   ├── shot_detector.py  # Computer vision for shot detection
│   ├── moa_calculator.py # MOA calculation logic
│   └── requirements.txt  # Python dependencies
├── frontend/         # React web application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── types.ts      # TypeScript types
│   │   └── App.tsx       # Main App component
│   └── package.json      # Node.js dependencies
├── uploads/          # Local storage for uploaded images
└── README.md
```

## Quick Start

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Start the backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python app.py
   ```

3. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm start
   ```

4. **Open your browser to:** `http://localhost:3000`

## Manual Setup

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Test Backend
```bash
cd backend
source venv/bin/activate
python test_backend.py
```

## How It Works

1. **Upload**: Users upload target photos through the web interface
2. **Detection**: OpenCV analyzes the image to detect shot holes using:
   - Adaptive thresholding
   - Contour detection with circularity filtering
   - Hough Circle Transform as fallback
3. **Analysis**: Calculate MOA using extreme spread method
4. **Visualization**: Annotate the image with detected shots
5. **Storage**: Save results locally with metadata

## Technology Stack

- **Frontend**: React, TypeScript, Tailwind CSS, React Dropzone
- **Backend**: Python, Flask, OpenCV, NumPy, SciPy
- **Image Processing**: OpenCV for shot detection and annotation
- **Storage**: Local filesystem with JSON metadata

## Current Status

✅ **Completed:**
- Basic project structure
- Flask backend API
- React frontend with TypeScript
- Shot detection algorithm
- MOA calculation
- File upload handling
- History tracking
- Image annotation

🔄 **Next Steps:**
- Test with real target images
- Calibration system for different target sizes
- Enhanced shot detection algorithms
- Export functionality
- Mobile responsiveness
- Error handling improvements

## Notes

- MOA calculation assumes 100-yard distance by default
- Shot detection works best with high-contrast target images
- The application stores all data locally
- Green circles indicate detected shots, red dots show centers
