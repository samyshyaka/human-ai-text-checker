import React from 'react';
import Post from './Post';

function PostList({ posts, onDeletePost, onEditPost }) {
  return (
    <div className="post-list">
      {posts.length === 0 ? (
        <p>No posts yet.</p>
      ) : (
        posts.map((post, idx) => (
          <Post key={idx} post={post} onDelete={onDeletePost} onEdit={onEditPost} />
        ))
      )}
    </div>
  );
}

export default PostList; 