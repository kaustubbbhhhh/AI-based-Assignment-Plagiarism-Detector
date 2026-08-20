import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, User } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const authRoutes = ['/login', '/', '/register', '/forgot-password', '/reset-password'];
  const isAuthPage = authRoutes.includes(location.pathname);

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const token = localStorage.getItem('token');
  const isLoggedIn = token && user && user.name && !isAuthPage;

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const getRoleBadgeClass = (role) => {
    const r = (role || '').toLowerCase();
    if (r === 'hod') return 'badge-danger';
    if (r === 'teacher') return 'badge-primary';
    if (r === 'student') return 'badge-accent';
    return 'badge-neutral';
  };

  return (
    <nav className="navbar-shell">
      <div className="container navbar-row">
        <Link to="/" className="navbar-brand">
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%)',
            color: '#ffffff',
            boxShadow: '0 2px 8px rgba(79, 70, 229, 0.25)',
            flexShrink: 0
          }}>
            <ShieldCheck size={22} />
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.025em' }}>
            Plagiarism<span style={{ color: 'var(--primary-color)' }}>AI</span>
          </span>
        </Link>

        {isLoggedIn && (
          <div className="navbar-actions">
            <div className="navbar-user-chip hidden-mob">
              <User size={15} style={{ color: 'var(--text-muted)' }} />
              <span className="navbar-user-text">{user.name}</span>
              {user.role && (
                <span className={`badge ${getRoleBadgeClass(user.role)}`} style={{ textTransform: 'capitalize' }}>
                  {user.role}
                </span>
              )}
            </div>

            <button
              onClick={handleLogout}
              className="btn btn-outline navbar-logout-btn"
              title="Log out of account"
              aria-label="Logout"
            >
              <LogOut size={15} />
              <span className="hidden-mob">Logout</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}

