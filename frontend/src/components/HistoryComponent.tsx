import React from 'react';
import { HistoryEntry } from '../types';
import { config } from '../config';

interface HistoryComponentProps {
  history: HistoryEntry[];
  onHistoryUpdate: () => void;
}

const HistoryComponent: React.FC<HistoryComponentProps> = ({ history, onHistoryUpdate }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload History</h2>
        <div className="text-center py-8">
          <svg
            className="h-12 w-12 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-gray-500">No targets analyzed yet</p>
          <p className="text-sm text-gray-400">Upload your first target to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload History</h2>
      
      <div className="space-y-4">
        {history.map((entry) => (
          <div
            key={entry.id}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-medium text-gray-900">{entry.filename}</h3>
                <p className="text-sm text-gray-500">{formatDate(entry.upload_time)}</p>
              </div>
            <div className="text-right">
                <button
                  className="text-sm text-red-600 hover:underline"
                  onClick={async () => {
                    const confirmed = window.confirm('Are you sure you want to delete this target?');
                    if (confirmed) {
                      await fetch(`${config.apiBaseUrl}/delete/${entry.id}`, { method: 'DELETE' });
                      onHistoryUpdate();
                    }
                  }}
                >
                  Delete
                </button>
                <div className="flex space-x-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Shots</p>
                    <p className="text-lg font-semibold text-blue-600">{entry.shot_count}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">MOA</p>
                    <p className="text-lg font-semibold text-green-600">
                      {entry.moa_value ? `${entry.moa_value}"` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Thumbnail */}
            <div className="mt-3">
              <img
                src={`${config.apiBaseUrl}/image/${entry.annotated_filename}`}
                alt="Target analysis"
                className="w-full h-48 object-contain border border-gray-200 rounded bg-gray-50"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            
            {/* Shot positions preview */}
            {entry.shots.length > 0 && (
              <div className="mt-3 bg-gray-50 p-3 rounded">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Shot Positions</h4>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {entry.shots.slice(0, 6).map((shot, index) => (
                    <span key={index} className="font-mono text-gray-600">
                      {index + 1}: ({shot[0]}, {shot[1]})
                    </span>
                  ))}
                  {entry.shots.length > 6 && (
                    <span className="text-gray-500">+{entry.shots.length - 6} more</span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default HistoryComponent;

