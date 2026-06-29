import React, { useState } from 'react';
import './App.css';
import AnalysisList from './components/AnalysisList';
import CreateAnalysis from './components/CreateAnalysis';
import Sidebar from './components/Sidebar';
import { apiService } from './services/api';

function App() {
  const [analyses, setAnalyses] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [nextId, setNextId] = useState(1);
  const [improvingId, setImprovingId] = useState(null);

  const handleCreateAnalysis = (analysis) => {
    // Analysis now comes with real AI analysis from the API
    setAnalyses([
      {
        ...analysis,
        id: nextId,
      },
      ...analyses,
    ]);
    setNextId(nextId + 1);
    setShowCreate(false);
  };

  const handleCloseCreate = () => {
    setShowCreate(false);
  };

  const handleDeleteAnalysis = (analysisToDelete) => {
    setAnalyses(analyses.filter(analysis => analysis.id !== analysisToDelete.id));
  };

  const handleEditAnalysis = (editedAnalysis) => {
    setAnalyses(analyses.map(analysis => analysis.id === editedAnalysis.id ? { ...analysis, ...editedAnalysis } : analysis));
  };

  const handleImproveAnalysis = async (analysisToImprove) => {
    setImprovingId(analysisToImprove.id);
    try {
      const response = await apiService.improveText(analysisToImprove.content);
      const verification = response.verification || {};
      const toPercent = (value) => {
        const num = Number(value);
        if (Number.isNaN(num)) return null;
        return num <= 1 ? Math.round(num * 100) : Math.round(num);
      };
      const improvedHumanPercent = toPercent(verification.human_probability);
      const improvedAiPercent = toPercent(verification.ai_probability);

      setAnalyses(analyses.map(analysis =>
        analysis.id === analysisToImprove.id
          ? {
              ...analysis,
              improvedText: response.humanized_text,
              improvedVerification: verification,
              improvedHumanPercent,
              improvedAiPercent,
            }
          : analysis
      ));
    } catch (error) {
      console.error('Improve request failed:', error);
      alert(error.message || 'Could not improve text. Please try again.');
    } finally {
      setImprovingId(null);
    }
  };

  const handleNavigateHome = () => {
    setShowCreate(false);
  };

  // Filter analyses by search
  const filteredAnalyses = analyses.filter(analysis =>
    analysis.title.toLowerCase().includes(search.toLowerCase()) ||
    analysis.content.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-left">
          <h1>AI vs Human Text Checker</h1>
        </div>
        <div className="header-center">
          <input
            className="search-bar"
            type="text"
            placeholder="Search analyses..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="header-right">
          <button className="create-btn" onClick={() => setShowCreate(true)}>Analyze Text</button>
          <svg className="header-icon notification-icon" title="Notifications" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"/>
          </svg>
          <svg className="header-icon profile-icon" title="Profile" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
      </header>
      <div className="app-container">
        <Sidebar onNavigateHome={handleNavigateHome} />
        <main className="main-content">
          {showCreate ? (
            <CreateAnalysis onCreateAnalysis={handleCreateAnalysis} onClose={handleCloseCreate} />
          ) : (
            <AnalysisList
              analyses={filteredAnalyses}
              onDeleteAnalysis={handleDeleteAnalysis}
              onEditAnalysis={handleEditAnalysis}
              onImproveAnalysis={handleImproveAnalysis}
              improvingId={improvingId}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
