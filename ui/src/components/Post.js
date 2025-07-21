import React, { useState } from 'react';

function Post({ post, onDelete, onEdit }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(post.title);
  const [editContent, setEditContent] = useState(post.content);

  const handleEditSubmit = (e) => {
    e.preventDefault();
    onEdit({ ...post, title: editTitle, content: editContent });
    setIsEditing(false);
  };

  return (
    <div className="post">
      {isEditing ? (
        <form className="create-post" onSubmit={handleEditSubmit}>
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
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button type="submit">Save</button>
            <button type="button" onClick={() => setIsEditing(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <>
          <h3>{post.title}</h3>
          <p>{post.content}</p>
          {post.humanPercent !== undefined && post.aiPercent !== undefined && (
            <div className="post-analysis">
              <div className="score-labels">
                <span className="score-human-label">Human: {post.humanPercent}%</span>
                <span className="score-ai-label">AI: {post.aiPercent}%</span>
              </div>
              <div className="score-bar">
                <div
                  className="score-bar-human"
                  style={{ width: `${post.humanPercent}%` }}
                />
                <div
                  className="score-bar-ai"
                  style={{ width: `${post.aiPercent}%` }}
                />
              </div>
            </div>
          )}
          <div className="post-footer">
            <span className="post-action">⬆️ 194</span>
            <span className="post-action">💬 7</span>
            <span className="post-action">🔖</span>
            <span className="post-action">🔗 Share</span>
            <span className="post-action" onClick={() => setIsEditing(true)}>✏️ Edit</span>
            <span className="post-action" onClick={() => onDelete(post)}>🗑️ Delete</span>
          </div>
        </>
      )}
    </div>
  );
}

export default Post; 