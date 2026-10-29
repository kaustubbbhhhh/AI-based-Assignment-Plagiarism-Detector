import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, ArrowRight, AlertCircle, Lock, Mail, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AdminLogin() {
  const navigate = useNavigate();
  const { login, logout } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email, password);
      
      if (!user) {
        throw new Error('Login failed. Please check your credentials.');
      }

      if (user.role !== 'admin') {
        await logout();
        setError('This login is for administrators only.');
        return;
      }

      if (user.must_change_password) {
        navigate('/change-password-required');
      } else {
        navigate('/admin');
      }
    } catch (err) {
      console.error('Admin login error:', err);
      setError(err.message || 'Failed to login. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)', padding: '1rem 0' }}>
      <div className="card glass-panel w-full-mob" style={{ maxWidth: '460px', width: '100%', padding: '2.5rem 2rem' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'var(--surface-color, rgba(255, 255, 255, 0.05))',
            color: 'var(--primary-color)',
            border: '1px solid var(--border-color)',
            marginBottom: '1rem'
          }}>
            <ShieldCheck size={32} />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-color)', marginBottom: '0.5rem' }}>
            Admin Access
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Secure login for system administrators
          </p>
        </div>

        {error && (
          <div className="alert alert-danger flex items-center gap-2" style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', borderRadius: '8px' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.9rem' }}>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="form-group">
            <label className="form-label" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.9rem' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Mail size={18} />
              </div>
              <input
                type="email"
                className="form-input w-full"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                style={{ paddingLeft: '2.5rem' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.9rem' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Lock size={18} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input w-full"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{ paddingLeft: '2.5rem', paddingRight: '2.5rem' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ 
                  position: 'absolute', 
                  right: '12px', 
                  top: '50%', 
                  transform: 'translateY(-50%)', 
                  color: 'var(--text-muted)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex'
                }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full flex items-center justify-center gap-2"
            disabled={loading}
            style={{ marginTop: '0.5rem' }}
          >
            {loading ? (
              <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
            ) : (
              <>
                Login to Dashboard
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <Link 
            to="/login" 
            style={{ 
              color: 'var(--text-muted)', 
              fontSize: '0.9rem', 
              textDecoration: 'none',
              transition: 'color 0.2s',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem'
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>&larr;</span> Back to main login
          </Link>
        </div>
      </div>
    </div>
  );
}
