import React from 'react';
import Analysis from './Analysis';

function AnalysisList({ analyses, onDeleteAnalysis, onEditAnalysis }) {
  return (
    <div className="analysis-list">
      {analyses.length === 0 ? (
        <div className="empty-state">
          <h3>Welcome to AI vs Human Text Checker</h3>
          <p>Make your first text analysis to determine if content was written by AI or a human.</p>
          <div className="empty-state-features">
            <div className="feature-item">
              <span className="feature-icon">🔍</span>
              <span>Analyze text authenticity</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📊</span>
              <span>Get detailed insights</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">💾</span>
              <span>Save analysis history</span>
            </div>
          </div>
        </div>
      ) : (
        analyses.map((analysis, idx) => (
          <Analysis key={idx} analysis={analysis} onDelete={onDeleteAnalysis} onEdit={onEditAnalysis} />
        ))
      )}
    </div>
  );
}

export default AnalysisList;
