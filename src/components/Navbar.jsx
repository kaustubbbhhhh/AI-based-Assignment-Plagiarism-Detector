import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLogin = location.pathname === '/login' || location.pathname === '/';

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <nav style={{
      padding: '1.25rem 0',
      borderBottom: '1px solid var(--border-color)',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      <div className="container navbar-row flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 navbar-brand" style={{ color: 'var(--text-main)', fontWeight: 700, fontSize: '1.25rem' }}>
          <ShieldCheck size={28} color="var(--primary-color)" />
          <span>PlagiarismAI</span>
        </Link>

        {!isLogin && (
          <div className="flex items-center gap-2 navbar-actions">
            <span className="hidden-mob navbar-user-text" style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              {user.name} ({user.role})
            </span>
            <button onClick={handleLogout} className="btn btn-outline navbar-logout-btn" style={{ padding: '0.4rem 0.75rem', fontSize: '0.875rem' }}>
              <LogOut size={16} /> <span className="hidden-mob">Logout</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
