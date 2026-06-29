import React, { useState } from 'react';

function Analysis({ analysis, onDelete, onEdit, onImprove, isImproving }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(analysis.title);
  const [editContent, setEditContent] = useState(analysis.content);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleEditSubmit = (e) => {
    e.preventDefault();
    onEdit({ ...analysis, title: editTitle, content: editContent });
    setIsEditing(false);
  };

  const isAiGenerated = analysis.aiPercent !== undefined && analysis.aiPercent >= 50;

  const getImprovedPercents = () => {
    if (
      analysis.improvedHumanPercent != null &&
      analysis.improvedAiPercent != null &&
      !Number.isNaN(analysis.improvedHumanPercent) &&
      !Number.isNaN(analysis.improvedAiPercent)
    ) {
      return {
        human: analysis.improvedHumanPercent,
        ai: analysis.improvedAiPercent,
      };
    }

    const verification = analysis.improvedVerification;
    if (!verification) return null;

    const toPercent = (value) => {
      const num = Number(value);
      if (Number.isNaN(num)) return null;
      return num <= 1 ? Math.round(num * 100) : Math.round(num);
    };

    const human = toPercent(verification.human_probability);
    const ai = toPercent(verification.ai_probability);
    if (human == null || ai == null) return null;
    return { human, ai };
  };

  const improvedPercents = getImprovedPercents();

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
                      <div className="analysis-reasoning">
                        <strong>Reasoning:</strong>
                        <p>{analysis.analysis.reasoning || 'No reasoning provided'}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {analysis.improvedText && (
            <div className="analysis-improved">
              <strong>Humanized Text (verified human-written):</strong>
              {analysis.improvedVerification?.attempts > 1 && (
                <div className="improved-verification">
                  Verified in {analysis.improvedVerification.attempts} attempts
                </div>
              )}
              <p>{analysis.improvedText}</p>
              {improvedPercents && (
                <div className="analysis-analysis improved-scores">
                  <div className="score-labels">
                    <span className="score-human-label">Human: {improvedPercents.human}%</span>
                    <span className="score-ai-label">AI: {improvedPercents.ai}%</span>
                  </div>
                  <div className="score-bar">
                    <div
                      className="score-bar-human"
                      style={{ width: `${improvedPercents.human}%` }}
                    />
                    <div
                      className="score-bar-ai"
                      style={{ width: `${improvedPercents.ai}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          <div className="analysis-footer">
            <span className="analysis-action">🔗 Share</span>
            <span className="analysis-action" onClick={() => setIsEditing(true)}>✏️ Edit</span>
            <span className="analysis-action" onClick={() => onDelete(analysis)}>🗑️ Delete</span>
            {isAiGenerated && (
              <span
                className={`analysis-action${isImproving ? ' analysis-action-disabled' : ''}`}
                onClick={() => !isImproving && onImprove && onImprove(analysis)}
              >
                {isImproving ? '⏳ Humanizing & verifying...' : '🪄 Improve'}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Analysis;
