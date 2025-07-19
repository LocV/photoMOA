import React, { useState, useEffect } from 'react';
import './App.css';
import UploadComponent from './components/UploadComponent';
import ResultsComponent from './components/ResultsComponent';
import HistoryComponent from './components/HistoryComponent';
import { AnalysisResult, HistoryEntry } from './types';

function App() {
  const [currentResult, setCurrentResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/history');
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleUploadComplete = (result: AnalysisResult) => {
    setCurrentResult(result);
    fetchHistory(); // Refresh history after upload
  };

  const handleResultUpdate = (updatedResult: AnalysisResult) => {
    setCurrentResult(updatedResult);
    fetchHistory(); // Refresh history after update
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">PhotoMOA</h1>
            <p className="text-gray-600">Shot Grouping Analysis Tool</p>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'upload'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Upload & Analyze
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              History
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {activeTab === 'upload' ? (
          <div className="px-4 py-6 sm:px-0">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <UploadComponent onUploadComplete={handleUploadComplete} />
              </div>
              <div>
                {currentResult && <ResultsComponent result={currentResult} onResultUpdate={handleResultUpdate} />}
              </div>
            </div>
          </div>
        ) : (
          <div className="px-4 py-6 sm:px-0">
            <HistoryComponent history={history} onHistoryUpdate={fetchHistory} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
