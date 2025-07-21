import React, { useState } from 'react';

function CreatePost({ onCreatePost }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    onCreatePost({ title, content });
    setTitle('');
    setContent('');
  };

  return (
    <form className="create-post" onSubmit={handleSubmit}>
      <h2>Create a Post</h2>
      <input
        type="text"
        placeholder="Title"
        value={title}
        onChange={e => setTitle(e.target.value)}
        required
      />
      <textarea
        placeholder="Content"
        value={content}
        onChange={e => setContent(e.target.value)}
        required
      />
      <button type="submit">Post</button>
    </form>
  );
}

export default CreatePost; 