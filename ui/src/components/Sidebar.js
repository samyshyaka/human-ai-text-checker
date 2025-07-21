import React from 'react';

function Sidebar() {
  return (
    <aside className="sidebar">
      <nav>
        <ul className="sidebar-main">
          <li className="sidebar-item active">Home</li>
          <li className="sidebar-item">Popular</li>
          <li className="sidebar-item">Answers <span className="beta">BETA</span></li>
          <li className="sidebar-item">Explore</li>
          <li className="sidebar-item">All</li>
        </ul>
        <div className="sidebar-section">
          <div className="sidebar-section-title">CUSTOM FEEDS</div>
          <div className="sidebar-link">+ Create a custom feed</div>
        </div>
        <div className="sidebar-section">
          <div className="sidebar-section-title">RECENT</div>
          <div className="sidebar-link">r/outlier_ai</div>
          <div className="sidebar-link">r/alignerr</div>
        </div>
        <div className="sidebar-section">
          <div className="sidebar-section-title">COMMUNITIES</div>
          <div className="sidebar-link">+ Create a community</div>
          <div className="sidebar-link">Manage communities</div>
        </div>
        <div className="sidebar-section">
          <div className="sidebar-section-title">RESOURCES</div>
          <div className="sidebar-link">About Reddit</div>
          <div className="sidebar-link">Advertise</div>
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar; 