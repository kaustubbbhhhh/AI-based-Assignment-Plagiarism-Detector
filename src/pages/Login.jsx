import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, BookOpen, GraduationCap, ArrowRight, AlertCircle, Lock, Mail, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [role, setRole] = useState('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRoleChange = (selectedRole) => {
    setRole(selectedRole);
  };

  const fillDemoCredentials = (demoRole) => {
    setRole(demoRole);
    if (demoRole === 'student') {
      setEmail('student@demo.edu');
      setPassword('Password123');
    } else if (demoRole === 'teacher') {
      setEmail('teacher@demo.edu');
      setPassword('Password123');
    } else if (demoRole === 'hod') {
      setEmail('hod@demo.edu');
      setPassword('Password123');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const loggedUser = await login(email, password);

      // Verify selected role matches account role
      const userRole = (loggedUser.role || '').toLowerCase();
      if (userRole !== role.toLowerCase()) {
        throw new Error(`Your account role is '${userRole}', but '${role}' portal was selected.`);
      }

      if (userRole === 'student') navigate('/student');
      else if (userRole === 'teacher') navigate('/teacher');
      else if (userRole === 'hod') navigate('/hod');
    } catch (err) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)', padding: '1rem 0' }}>
      <div className="card glass-panel w-full-mob" style={{ maxWidth: '460px', width: '100%', padding: '2.5rem 2rem' }}>
        <div className="text-center" style={{ marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '0.5rem', fontWeight: 800 }}>Welcome Back</h2>
          <p className="text-muted" style={{ fontSize: '0.925rem' }}>
            Select your role to access your academic dashboard.
          </p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">Select Your Role</label>
            <div className="grid grid-cols-3 gap-2">
              <RoleOption
                icon={<User size={20} />}
                label="Student"
                selected={role === 'student'}
                onClick={() => handleRoleChange('student')}
              />
              <RoleOption
                icon={<BookOpen size={20} />}
                label="Teacher"
                selected={role === 'teacher'}
                onClick={() => handleRoleChange('teacher')}
              />
              <RoleOption
                icon={<GraduationCap size={20} />}
                label="HOD"
                selected={role === 'hod'}
                onClick={() => handleRoleChange('hod')}
              />
            </div>
          </div>

          {error && (
            <div className="alert alert-danger">
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                className="form-input"
                placeholder="name@institute.edu"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ paddingLeft: '2.5rem' }}
              />
              <Mail
                size={18}
                style={{
                  position: 'absolute',
                  left: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-subtle)',
                  pointerEvents: 'none'
                }}
              />
            </div>
          </div>

          <div className="form-group">
            <div className="flex items-center justify-between" style={{ marginBottom: '0.45rem' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
              <Link to="/forgot-password" style={{ fontSize: '0.825rem', color: 'var(--primary-color)', fontWeight: 600 }}>
                Forgot password?
              </Link>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: '2.5rem', paddingRight: '2.5rem' }}
              />
              <Lock
                size={18}
                style={{
                  position: 'absolute',
                  left: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-subtle)',
                  pointerEvents: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.2rem'
                }}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
            style={{ marginTop: '1.25rem', padding: '0.8rem 1rem', fontSize: '0.975rem' }}
          >
            {loading ? (
              <>
                <div className="spinner spinner-white" style={{ width: '18px', height: '18px' }}></div>
                <span>Signing In...</span>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <span>Enter Portal</span>
                <ArrowRight size={18} />
              </div>
            )}
          </button>

          <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px dashed var(--border-color)', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quick Fill Demo Accounts
            </span>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
                onClick={() => fillDemoCredentials('student')}
              >
                Student Demo
              </button>
              <button
                type="button"
                className="btn btn-outline"
                style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
                onClick={() => fillDemoCredentials('teacher')}
              >
                Teacher Demo
              </button>
              <button
                type="button"
                className="btn btn-outline"
                style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
                onClick={() => fillDemoCredentials('hod')}
              >
                HOD Demo
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

function RoleOption({ icon, label, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.85rem 0.5rem',
        border: `2px solid ${selected ? 'var(--primary-color)' : 'var(--border-color)'}`,
        backgroundColor: selected ? 'var(--primary-light)' : 'var(--surface-color)',
        borderRadius: 'var(--radius-md)',
        color: selected ? 'var(--primary-color)' : 'var(--text-muted)',
        fontWeight: selected ? 600 : 500,
        boxShadow: selected ? '0 0 0 1px var(--primary-color)' : 'none',
        transition: 'var(--transition)',
        cursor: 'pointer',
        width: '100%'
      }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: selected ? 'var(--primary-color)' : 'var(--text-muted)'
      }}>
        {icon}
      </div>
      <span style={{ fontSize: '0.85rem' }}>{label}</span>
    </button>
  );
}

