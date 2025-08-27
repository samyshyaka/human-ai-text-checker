import React, { useState } from 'react';

function Analysis({ analysis, onDelete, onEdit }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(analysis.title);
  const [editContent, setEditContent] = useState(analysis.content);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleEditSubmit = (e) => {
    e.preventDefault();
    onEdit({ ...analysis, title: editTitle, content: editContent });
    setIsEditing(false);
  };

  return (
    <div className="analysis">
      {isEditing ? (
        <form className="create-analysis" onSubmit={handleEditSubmit}>
          <input
            type="text"
            value={editTitle}
            onChange={e => setEditTitle(e.target.value)}
            required
          />
          <textarea
            value={editContent}
            onChange={e => setEditContent(e.target.value)}
            required
          />
          <div className="edit-actions">
            <button type="submit">Save</button>
            <button type="button" onClick={() => setIsEditing(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <>
          <h3>{analysis.title}</h3>
          <p>{analysis.content}</p>
          {analysis.humanPercent !== undefined && analysis.aiPercent !== undefined && (
            <div className="analysis-analysis">
              <div className="score-labels">
                <span className="score-human-label">Human: {analysis.humanPercent}%</span>
                <span className="score-ai-label">AI: {analysis.aiPercent}%</span>
              </div>
              <div className="score-bar">
                <div
                  className="score-bar-human"
                  style={{ width: `${analysis.humanPercent}%` }}
                />
                <div
                  className="score-bar-ai"
                  style={{ width: `${analysis.aiPercent}%` }}
                />
              </div>
              
              {/* AI Analysis Details */}
              {analysis.analysis && (
                <div className="analysis-details">
                  <button 
                    className="analysis-toggle"
                    onClick={() => setShowAnalysis(!showAnalysis)}
                  >
                    {showAnalysis ? 'Hide' : 'Show'} AI Analysis Details
                  </button>
                  
                  {showAnalysis && (
                    <div className="analysis-content">
                      <div className="analysis-source">
                        <strong>Source:</strong> {analysis.analysis.source || 'Llama API'}
                      </div>
                      <div className="analysis-method">
                        <strong>Method:</strong> {analysis.analysis.extractionMethod || 'Direct API'}
                      </div>
                      <div className="analysis-reasoning">
                        <strong>AI Reasoning:</strong>
                        <p>{analysis.analysis.reasoning || 'No reasoning provided'}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          <div className="analysis-footer">
            <span className="analysis-action">🔗 Share</span>
            <span className="analysis-action" onClick={() => setIsEditing(true)}>✏️ Edit</span>
            <span className="analysis-action" onClick={() => onDelete(analysis)}>🗑️ Delete</span>
          </div>
        </>
      )}
    </div>
  );
}

export default Analysis;
