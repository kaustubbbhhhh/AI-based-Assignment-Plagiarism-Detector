import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, BookOpen, GraduationCap, ArrowRight } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [role, setRole] = useState('student');
  const [email, setEmail] = useState('student@demo.edu');
  const [password, setPassword] = useState('pass123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRoleChange = (selectedRole) => {
    setRole(selectedRole);
    if (selectedRole === 'student') setEmail('student@demo.edu');
    else if (selectedRole === 'teacher') setEmail('teacher@demo.edu');
    else if (selectedRole === 'hod') setEmail('hod@demo.edu');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();

      // Store token and user info
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Enforce role matching
      const userRole = data.user.role;
      if (userRole !== role) {
        throw new Error(`Unauthorized `);
      }

      if (userRole === 'student') navigate('/student');
      else if (userRole === 'teacher') navigate('/teacher');
      else if (userRole === 'hod') navigate('/hod');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center p-4" style={{ minHeight: 'calc(100vh - 150px)', padding: '0 1rem' }}>
      <div className="card glass-panel w-full-mob" style={{ maxWidth: '450px', width: '100%', padding: '2.5rem' }}>
        <div className="text-center" style={{ marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '0.5rem' }}>Welcome Back</h2>
          <p className="text-muted">Select your portal to continue viewing assignment analytics.</p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Select Role</label>
            <div className="grid grid-cols-3 gap-2" style={{ marginBottom: '1.5rem' }}>
              <RoleOption icon={<User size={20} />} label="Student" selected={role === 'student'} onClick={() => handleRoleChange('student')} />
              <RoleOption icon={<BookOpen size={20} />} label="Teacher" selected={role === 'teacher'} onClick={() => handleRoleChange('teacher')} />
              <RoleOption icon={<GraduationCap size={20} />} label="HOD" selected={role === 'hod'} onClick={() => handleRoleChange('hod')} />
            </div>
          </div>

          {error && (
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.875rem', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              className="form-input"
              placeholder="name@institute.edu"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary w-full" disabled={loading} style={{ marginTop: '1rem', padding: '0.875rem' }}>
            {loading ? (
              <div className="spinner" style={{ width: '20px', height: '20px' }}></div>
            ) : (
              <div className="flex items-center gap-2">Enter Portal <ArrowRight size={18} /></div>
            )}
          </button>

          <p className="text-center text-muted" style={{ marginTop: '1.5rem', fontSize: '0.875rem' }}>
            Don't have an account? <Link to="/register" style={{ color: 'var(--primary-color)', fontWeight: 600 }}>Register here</Link>
          </p>
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
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem 0.5rem',
        border: `2px solid ${selected ? 'var(--primary-color)' : 'var(--border-color)'}`,
        backgroundColor: selected ? 'rgba(79, 70, 229, 0.05)' : 'var(--bg-color)',
        borderRadius: 'var(--radius-md)', color: selected ? 'var(--primary-color)' : 'var(--text-muted)',
        transition: 'all 0.2s', cursor: 'pointer'
      }}
    >
      {icon}
      <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>
    </button>
  );
}
