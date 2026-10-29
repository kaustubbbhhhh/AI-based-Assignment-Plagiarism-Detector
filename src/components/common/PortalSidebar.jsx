import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function PortalSidebar({ roleLabel, navItems }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const userInitial = (user?.name || roleLabel || 'U').charAt(0).toUpperCase();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const mainItems = navItems.filter((item) => item.section === 'main');
  const settingsItems = navItems.filter((item) => item.section === 'settings');

  return (
    <>
      {/* ── Mobile Top Bar ── */}
      <div className="teacher-mobile-topbar">
        <button className="teacher-hamburger" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>
          Plagiarism<span style={{ color: 'var(--primary-color)' }}>AI</span>
        </span>
        <div style={{ width: '38px' }} />
      </div>

      {/* ── Sidebar Overlay (mobile) ── */}
      <div
        className={`teacher-sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* ── Sidebar ── */}
      <aside className={`teacher-sidebar ${sidebarOpen ? 'open' : ''}`}>
        {/* Brand */}
        <div className="teacher-sidebar-brand">
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%)',
              color: '#ffffff',
              boxShadow: '0 2px 8px rgba(79, 70, 229, 0.25)',
              flexShrink: 0,
            }}
          >
            <ShieldCheck size={18} />
          </div>
          <span>
            Plagiarism<span style={{ color: 'var(--primary-color)' }}>AI</span>
          </span>
        </div>

        {/* User Profile Chip */}
        <div className="teacher-sidebar-profile">
          <div className="teacher-sidebar-profile-chip">
            <div className="teacher-sidebar-avatar">{userInitial}</div>
            <div className="teacher-sidebar-userinfo">
              <div className="teacher-sidebar-username">{user?.name || roleLabel}</div>
              <div className="teacher-sidebar-userrole">{roleLabel}</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="teacher-sidebar-nav">
          {mainItems.length > 0 && <div className="teacher-sidebar-section-label">Main</div>}
          {mainItems.map((item) => (
            <button
              key={item.path}
              type="button"
              className={`teacher-sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => {
                navigate(item.path);
                setSidebarOpen(false);
              }}
            >
              <item.icon size={18} className="nav-icon" />
              <span>{item.label}</span>
            </button>
          ))}

          {settingsItems.length > 0 && (
            <div className="teacher-sidebar-section-label" style={{ marginTop: '0.5rem' }}>
              Settings
            </div>
          )}
          {settingsItems.map((item) => (
            <button
              key={item.path}
              type="button"
              className={`teacher-sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => {
                navigate(item.path);
                setSidebarOpen(false);
              }}
            >
              <item.icon size={18} className="nav-icon" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Logout */}
        <div className="teacher-sidebar-bottom">
          <button type="button" className="teacher-sidebar-logout" onClick={handleLogout}>
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
