import React from 'react';

function Sidebar({ onNavigateHome }) {
  return (
    <aside className="sidebar">
      <nav>
        <ul className="sidebar-main">
          <li className="sidebar-item active" onClick={onNavigateHome}>
            Home
          </li>
          <li className="sidebar-item">
            About
          </li>
          <li className="sidebar-item">
            Dashboard
          </li>
        </ul>
        
        <div className="sidebar-section">
          <div className="sidebar-section-title">RECENT ANALYSES</div>
          <div className="sidebar-link">Last analysis: 2 hours ago</div>
          <div className="sidebar-link">Total analyses: 47</div>
        </div>
        
        <div className="sidebar-section">
          <div className="sidebar-section-title">TOOLS</div>
          <div className="sidebar-link">⚙️ Settings</div>
          <div className="sidebar-link">❓ Help</div>
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar; 