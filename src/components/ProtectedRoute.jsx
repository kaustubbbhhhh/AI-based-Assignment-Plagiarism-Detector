import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert } from 'lucide-react';

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show clean spinner while session is being verified from HttpOnly cookie
  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '70vh',
          gap: '1rem',
        }}
      >
        <div className="spinner" style={{ width: '36px', height: '36px', borderWidth: '3px' }}></div>
        <p className="text-muted" style={{ fontSize: '0.95rem' }}>
          Verifying security credentials...
        </p>
      </div>
    );
  }

  // Not authenticated -> redirect to login (admin routes redirect to /admin/login)
  if (!isAuthenticated || !user) {
    const loginTarget = location.pathname.startsWith('/admin') ? '/admin/login' : '/login';
    return <Navigate to={loginTarget} state={{ from: location }} replace />;
  }

  // Force password change guard
  if (user.must_change_password && location.pathname !== '/change-password-required') {
    return <Navigate to="/change-password-required" replace />;
  }

  // Role authorization boundary
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = (user.role || '').toLowerCase();
    if (!allowedRoles.includes(userRole) && userRole !== 'admin') {
      return (
        <div className="flex items-center justify-center" style={{ minHeight: '70vh', padding: '2rem' }}>
          <div className="card glass-panel text-center" style={{ maxWidth: '480px', padding: '2.5rem 2rem' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--danger-color)',
                marginBottom: '1.25rem',
              }}
            >
              <ShieldAlert size={36} />
            </div>
            <h3 style={{ marginBottom: '0.5rem', fontWeight: 800 }}>403 — Access Forbidden</h3>
            <p className="text-muted" style={{ marginBottom: '1.5rem', fontSize: '0.925rem' }}>
              Your account ({user.email}) with role <strong style={{ textTransform: 'capitalize' }}>{user.role}</strong> does not have permission to view this academic portal.
            </p>
            <button
              className="btn btn-primary w-full"
              onClick={() => {
                if (user.role === 'student') window.location.href = '/student';
                else if (user.role === 'teacher') window.location.href = '/teacher';
                else if (user.role === 'hod') window.location.href = '/hod';
                else if (user.role === 'admin') window.location.href = '/admin';
                else window.location.href = '/login';
              }}
            >
              Return to My Portal
            </button>
          </div>
        </div>
      );
    }
  }

  return children;
}
