import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Lock, 
  Eye, 
  EyeOff, 
  ShieldAlert, 
  CheckCircle2, 
  LogOut, 
  ArrowRight, 
  AlertCircle 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';

const ChangePasswordRequired = () => {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const validatePassword = (password) => {
    const minLength = 8;
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    return password.length >= minLength && hasLetter && hasNumber;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (formData.newPassword !== formData.confirmPassword) {
      return setError('New passwords do not match');
    }

    if (!validatePassword(formData.newPassword)) {
      return setError('Password does not meet requirements');
    }

    setIsLoading(true);

    try {
      const response = await api.post('/api/auth/change-password', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to change password.');
      }

      setSuccess(true);
      await refreshUser();
      
      // Give the user a moment to see the success message
      setTimeout(() => {
        if (user?.role === 'admin') navigate('/admin');
        else if (user?.role === 'teacher') navigate('/teacher');
        else if (user?.role === 'hod') navigate('/hod');
        else navigate('/student');
      }, 1500);

    } catch (err) {
      setError(err.message || 'Failed to change password. Please check your current password and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      backgroundColor: 'var(--bg-color)'
    }}>
      <div className="card glass-panel" style={{
        maxWidth: '480px',
        width: '100%',
        padding: '2.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        animation: 'fadeIn 0.5s ease-out'
      }}>
        
        <div style={{ textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'var(--warning-light, rgba(245, 158, 11, 0.1))',
            color: 'var(--warning-color, #f59e0b)',
            marginBottom: '1rem'
          }}>
            <ShieldAlert size={32} />
          </div>
          <h1 style={{ 
            fontSize: '1.5rem', 
            fontWeight: '600',
            color: 'var(--text-color)',
            marginBottom: '0.5rem'
          }}>
            Password Change Required
          </h1>
          <p className="text-muted" style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>
            Your password must be changed before you can continue. Please set a new secure password.
          </p>
        </div>

        {error && (
          <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert alert-success" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={20} />
            <span>Password updated successfully! Redirecting...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          <div className="form-group">
            <label className="form-label" htmlFor="currentPassword">Current Password</label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Lock size={18} />
              </div>
              <input
                id="currentPassword"
                name="currentPassword"
                type={showCurrent ? "text" : "password"}
                className="form-input w-full"
                placeholder="Enter current password"
                value={formData.currentPassword}
                onChange={handleChange}
                required
                disabled={isLoading || success}
                style={{ paddingLeft: '2.75rem', paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                style={{
                  position: 'absolute',
                  right: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0'
                }}
                disabled={isLoading || success}
              >
                {showCurrent ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="newPassword">New Password</label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Lock size={18} />
              </div>
              <input
                id="newPassword"
                name="newPassword"
                type={showNew ? "text" : "password"}
                className="form-input w-full"
                placeholder="Enter new password"
                value={formData.newPassword}
                onChange={handleChange}
                required
                disabled={isLoading || success}
                style={{ paddingLeft: '2.75rem', paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                style={{
                  position: 'absolute',
                  right: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0'
                }}
                disabled={isLoading || success}
              >
                {showNew ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.25rem' }}>
              <AlertCircle size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
              Minimum 8 characters with both letters and numbers
            </p>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirmPassword">Confirm New Password</label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Lock size={18} />
              </div>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showConfirm ? "text" : "password"}
                className="form-input w-full"
                placeholder="Confirm new password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                disabled={isLoading || success}
                style={{ paddingLeft: '2.75rem', paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                style={{
                  position: 'absolute',
                  right: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0'
                }}
                disabled={isLoading || success}
              >
                {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary w-full" 
            disabled={isLoading || success}
            style={{ 
              marginTop: '0.5rem',
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              gap: '0.5rem' 
            }}
          >
            {isLoading ? (
              <>
                <div className="spinner spinner-white" style={{ width: '1.25rem', height: '1.25rem' }}></div>
                <span>Updating...</span>
              </>
            ) : (
              <>
                <span>Update Password</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>

        </form>

        <div style={{
          marginTop: '1rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--border-color)',
          textAlign: 'center'
        }}>
          <button 
            onClick={logout}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '0.9rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              cursor: 'pointer',
              transition: 'color var(--transition)'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = 'var(--text-color)'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <LogOut size={16} />
            <span>Cancel & Logout</span>
          </button>
        </div>

      </div>
    </div>
  );
};

export default ChangePasswordRequired;
