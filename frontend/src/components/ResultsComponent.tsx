import React, { useState, useRef, useCallback } from 'react';
import { AnalysisResult } from '../types';

interface ResultsComponentProps {
  result: AnalysisResult;
  onResultUpdate?: (updatedResult: AnalysisResult) => void;
}

const ResultsComponent: React.FC<ResultsComponentProps> = ({ result, onResultUpdate }) => {
  const [manualShots, setManualShots] = useState<Array<[number, number]>>([]);
  const [calibrationMode, setCalibrationMode] = useState(false);
  const [calibrationPoints, setCalibrationPoints] = useState<Array<[number, number]>>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<[number, number] | null>(null);
  const [calibrationDistance, setCalibrationDistance] = useState('1.0');
  const [calibrationUnit, setCalibrationUnit] = useState<'inches' | 'centimeters'>('inches');
  const [calibrationState, setCalibrationState] = useState<'idle' | 'firstPoint' | 'dragging' | 'complete'>('idle');
  const imageRef = useRef<HTMLImageElement | null>(null);

  const getImageCoordinates = useCallback((e: React.MouseEvent) => {
    if (!imageRef.current) return null;
    const rect = imageRef.current.getBoundingClientRect();
    const scaleX = imageRef.current.naturalWidth / rect.width;
    const scaleY = imageRef.current.naturalHeight / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    return [x, y] as [number, number];
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    const coords = getImageCoordinates(e);
    if (!coords) return;

    if (calibrationMode) {
      if (calibrationState === 'idle') {
        // First click - set first point
        setCalibrationPoints([coords]);
        setDragStart(coords);
        setCalibrationState('firstPoint');
      } else if (calibrationState === 'dragging') {
        // Second click - finalize second point
        setCalibrationPoints([dragStart!, coords]);
        setCalibrationState('complete');
        setIsDragging(false);
      }
    } else {
      setManualShots([...manualShots, coords]);
    }
  }, [calibrationMode, calibrationState, dragStart, manualShots, getImageCoordinates]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    if (calibrationMode && calibrationState === 'firstPoint' && dragStart) {
      const coords = getImageCoordinates(e);
      if (coords) {
        setCalibrationPoints([dragStart, coords]);
        setCalibrationState('dragging');
        setIsDragging(true);
      }
    } else if (calibrationMode && calibrationState === 'dragging' && dragStart) {
      const coords = getImageCoordinates(e);
      if (coords) {
        setCalibrationPoints([dragStart, coords]);
      }
    }
  }, [calibrationMode, calibrationState, dragStart, getImageCoordinates]);

  const handleMouseUp = useCallback(() => {
    // Mouse up doesn't finalize the calibration - only the second click does
  }, []);

  const undoLastShot = () => {
    setManualShots(manualShots.slice(0, -1));
  };

  const clearManualShots = () => {
    setManualShots([]);
  };

  const startCalibration = () => {
    setCalibrationMode(true);
    setCalibrationPoints([]);
    setManualShots([]);
    setCalibrationState('idle');
    setDragStart(null);
    setIsDragging(false);
  };

  const cancelCalibration = () => {
    setCalibrationMode(false);
    setCalibrationPoints([]);
    setCalibrationState('idle');
    setDragStart(null);
    setIsDragging(false);
  };

  const submitCalibration = async () => {
    if (!result || !result.id || calibrationPoints.length !== 2) return;

    // Convert distance to inches if needed
    const distanceInInches = calibrationUnit === 'centimeters' 
      ? parseFloat(calibrationDistance) / 2.54 
      : parseFloat(calibrationDistance);

    try {
      const response = await fetch(`http://localhost:5001/api/calibrate/${result.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          point1: calibrationPoints[0],
          point2: calibrationPoints[1],
          distance_inches: distanceInInches
        }),
      });

      if (response.ok) {
        const updatedResult = await response.json();
        // Update the current result with the new MOA value
        const newResult = {
          ...result,
          moa_value: updatedResult.moa_value
        };
        if (onResultUpdate) {
          onResultUpdate(newResult);
        }
        setCalibrationMode(false);
        setCalibrationPoints([]);
        setCalibrationState('idle');
        alert(`Calibration successful! Scale: ${updatedResult.pixels_per_inch.toFixed(2)} pixels per inch. New MOA: ${updatedResult.moa_value || 'N/A'}`);
      } else {
        console.error('Failed to calibrate');
      }
    } catch (error) {
      console.error('Error calibrating:', error);
    }
  };

  const submitManualShots = async () => {
    if (!result || !result.id) return;

    try {
      const response = await fetch(`http://localhost:5001/api/update-shots/${result.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ manual_shots: manualShots }),
      });

      if (response.ok) {
        const updatedResult = await response.json();
        if (onResultUpdate) {
          onResultUpdate(updatedResult);
        }
        // Clear manual shots after successful update
        setManualShots([]);
      } else {
        console.error('Failed to update shots');
      }
    } catch (error) {
      console.error('Error updating shots:', error);
    }
  };

  if (!result.success) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h2>
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{result.error || 'Analysis failed'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h2>
      
      {/* Statistics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700">Shots Detected</h3>
          <p className="text-2xl font-bold text-blue-600">{result.shot_count}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700">MOA Value</h3>
          <p className="text-2xl font-bold text-green-600">
            {result.moa_value ? `${result.moa_value}"` : 'N/A'}
          </p>
        </div>
      </div>

{/* Scale Calibration Section */}
      {!calibrationMode && (
        <div className="mb-6">
          <div className="bg-purple-50 border border-purple-200 rounded-md p-3">
            <h3 className="text-sm font-medium text-purple-800 mb-2">Scale Calibration</h3>
            <p className="text-sm text-purple-700 mb-3">
              Calibrate the scale for accurate MOA calculations by selecting two points with a known distance.
            </p>
            <button
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium"
              onClick={startCalibration}
            >
              Calibrate Scale
            </button>
          </div>
        </div>
      )}

      {/* Calibration Mode UI */}
      {calibrationMode && (
        <div className="mb-6">
          <div className="bg-purple-50 border border-purple-200 rounded-md p-3">
            <h3 className="text-sm font-medium text-purple-800 mb-2">Scale Calibration Mode</h3>
            <p className="text-sm text-purple-700 mb-3">
              {calibrationState === 'idle' && 'Click on the first point of a known distance (e.g., edge of a 1-inch square).'}
              {calibrationState === 'firstPoint' && 'Now drag to the second point and click to set it.'}
              {calibrationState === 'dragging' && 'Click to set the second point.'}
              {calibrationState === 'complete' && 'Perfect! Now enter the distance and apply calibration.'}
            </p>
            <div className="flex items-center gap-3 mb-3">
              <label className="text-sm font-medium text-purple-700">Distance between points:</label>
              <input
                type="number"
                step="0.1"
                value={calibrationDistance}
                onChange={(e) => setCalibrationDistance(e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                disabled={calibrationState !== 'complete'}
              />
              <select
                value={calibrationUnit}
                onChange={(e) => setCalibrationUnit(e.target.value as 'inches' | 'centimeters')}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
                disabled={calibrationState !== 'complete'}
              >
                <option value="inches">inches</option>
                <option value="centimeters">centimeters</option>
              </select>
            </div>
            <div className="flex gap-2 flex-wrap items-center">
              <span className="text-xs text-purple-700">
                State: {calibrationState === 'idle' ? 'Ready for first point' : 
                        calibrationState === 'firstPoint' ? 'Drag to second point' :
                        calibrationState === 'dragging' ? 'Click to confirm second point' :
                        'Ready to calibrate'}
              </span>
              {calibrationState === 'complete' && (
                <button
                  onClick={submitCalibration}
                  className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 font-medium"
                >
                  Apply Calibration
                </button>
              )}
              <button
                onClick={cancelCalibration}
                className="text-xs bg-gray-600 text-white px-2 py-1 rounded hover:bg-gray-700"
              >
                {calibrationState === 'idle' ? 'Cancel' : 'Reset'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Annotated Image with Manual Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          {calibrationMode ? 'Click-Drag-Click to Set Calibration Line' : 'Annotated Target'}
        </h3>
        {!calibrationMode && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800 mb-2">
            <strong>Manual Shot Selection:</strong> Click on missed bullet holes to add them manually.
          </p>
          <div className="flex gap-2 flex-wrap">
            <span className="text-xs text-yellow-700">Manual shots added: {manualShots.length}</span>
            {manualShots.length > 0 && (
              <>
                <button
                  onClick={undoLastShot}
                  className="text-xs bg-yellow-600 text-white px-2 py-1 rounded hover:bg-yellow-700"
                >
                  Undo Last
                </button>
                <button
                  onClick={clearManualShots}
                  className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                >
                  Clear All
                </button>
              </>
            )}
          </div>
          </div>
        )}
        <div
          className={`border border-gray-200 rounded-lg overflow-hidden relative ${
            calibrationMode ? 
              (calibrationState === 'idle' ? 'cursor-crosshair' :
               calibrationState === 'firstPoint' ? 'cursor-crosshair' :
               calibrationState === 'dragging' ? 'cursor-crosshair' : 'cursor-default') 
              : 'cursor-crosshair'
          }`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <img
            src={result.annotated_image}
            ref={imageRef}
            alt="Annotated target with detected shots"
            className="w-full h-auto"
          />
          {/* Overlay calibration point markers */}
          {calibrationPoints.map((point, index) => {
            const rect = imageRef.current?.getBoundingClientRect();
            if (!rect || !imageRef.current) return null;
            const scaleX = rect.width / imageRef.current.naturalWidth;
            const scaleY = rect.height / imageRef.current.naturalHeight;
            return (
              <div
                key={`cal-${index}`}
                className="absolute pointer-events-none"
                style={{
                  top: `${point[1] * scaleY - 12}px`,
                  left: `${point[0] * scaleX - 12}px`,
                  width: '24px',
                  height: '24px',
                  border: '3px solid #8b5cf6',
                  backgroundColor: 'rgba(139, 92, 246, 0.3)',
                  borderRadius: '50%',
                }}
              >
                <div className="absolute top-[-25px] left-1/2 transform -translate-x-1/2 text-xs font-bold text-purple-600 bg-white px-1 rounded">
                  C{index + 1}
                </div>
              </div>
            );
          })}
          
          {/* Draw calibration line */}
          {calibrationPoints.length === 2 && imageRef.current && (
            <svg
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
              style={{ zIndex: 10 }}
            >
              <line
                x1={`${(calibrationPoints[0][0] / imageRef.current.naturalWidth) * 100}%`}
                y1={`${(calibrationPoints[0][1] / imageRef.current.naturalHeight) * 100}%`}
                x2={`${(calibrationPoints[1][0] / imageRef.current.naturalWidth) * 100}%`}
                y2={`${(calibrationPoints[1][1] / imageRef.current.naturalHeight) * 100}%`}
                stroke="#8b5cf6"
                strokeWidth="2"
                strokeDasharray="5,5"
              />
            </svg>
          )}

          {/* Overlay manual shot markers */}
          {!calibrationMode && manualShots.map((shot, index) => {
            const rect = imageRef.current?.getBoundingClientRect();
            if (!rect || !imageRef.current) return null;
            const scaleX = rect.width / imageRef.current.naturalWidth;
            const scaleY = rect.height / imageRef.current.naturalHeight;
            return (
              <div
                key={index}
                className="absolute pointer-events-none"
                style={{
                  top: `${shot[1] * scaleY - 8}px`,
                  left: `${shot[0] * scaleX - 8}px`,
                  width: '16px',
                  height: '16px',
                  border: '2px solid #ff4444',
                  backgroundColor: 'rgba(255, 68, 68, 0.3)',
                  borderRadius: '50%',
                }}
              >
                <div className="absolute top-[-20px] left-1/2 transform -translate-x-1/2 text-xs font-bold text-red-600 bg-white px-1 rounded">
                  {index + 1}
                </div>
              </div>
            );
          })}
        </div>
        {manualShots.length > 0 && (
          <div className="mt-4 flex gap-2">
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 font-medium"
              onClick={submitManualShots}
            >
              Update MOA with {manualShots.length} Manual Shot{manualShots.length !== 1 ? 's' : ''}
            </button>
            <button
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              onClick={clearManualShots}
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Shot Details */}
      {result.shots.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Shot Positions</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="grid grid-cols-2 gap-2 text-sm">
              {result.shots.map((shot, index) => (
                <div key={index} className="flex justify-between">
                  <span className="text-gray-600">Shot {index + 1}:</span>
                  <span className="font-mono">({shot[0]}, {shot[1]})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Analysis Notes */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Analysis Notes</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• MOA calculated using extreme spread method</li>
          <li>• Assumes 100-yard target distance</li>
          <li>• Green circles indicate detected shots</li>
          <li>• Red dots mark shot centers</li>
        </ul>
      </div>
    </div>
  );
};

export default ResultsComponent;
