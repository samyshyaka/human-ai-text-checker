import React, { useState } from 'react';
import './App.css';
import PostList from './components/PostList';
import CreatePost from './components/CreatePost';
import Sidebar from './components/Sidebar';

function App() {
  const [posts, setPosts] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [nextId, setNextId] = useState(1);

  const handleCreatePost = (post) => {
    // Mock analysis: random percentages
    const humanPercent = Math.floor(Math.random() * 51) + 50; // 50-100
    const aiPercent = 100 - humanPercent;
    setPosts([
      {
        ...post,
        humanPercent,
        aiPercent,
        id: nextId,
      },
      ...posts,
    ]);
    setNextId(nextId + 1);
    setShowCreate(false);
  };

  const handleDeletePost = (postToDelete) => {
    setPosts(posts.filter(post => post.id !== postToDelete.id));
  };

  const handleEditPost = (editedPost) => {
    setPosts(posts.map(post => post.id === editedPost.id ? { ...post, ...editedPost } : post));
  };

  // Filter posts by search
  const filteredPosts = posts.filter(post =>
    post.title.toLowerCase().includes(search.toLowerCase()) ||
    post.content.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-left">
          <h1>Human|AI Score</h1>
        </div>
        <div className="header-center">
          <input
            className="search-bar"
            type="text"
            placeholder="Search posts..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="header-right">
          <button className="create-btn" onClick={() => setShowCreate(true)}>Create</button>
          <span className="header-icon notification-icon" title="Notifications">🔔</span>
          <span className="header-icon profile-icon" title="Profile">👤</span>
        </div>
      </header>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          {showCreate && (
            <CreatePost onCreatePost={handleCreatePost} />
          )}
          <PostList posts={filteredPosts} onDeletePost={handleDeletePost} onEditPost={handleEditPost} />
        </main>
      </div>
    </div>
  );
}

export default App;
