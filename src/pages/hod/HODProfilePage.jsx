import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function HODProfilePage() {
  const { user } = useAuth();
  const userInitial = (user?.name || 'H').charAt(0).toUpperCase();

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header" style={{ marginBottom: '1.75rem' }}>
        <h2>My Profile</h2>
        <p>View your account details and department assignments.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="card md:col-span-2">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.75rem' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-full)',
              background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '1.4rem',
              flexShrink: 0,
              textTransform: 'uppercase',
            }}>
              {userInitial}
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>{user?.name}</h3>
              <span className="badge badge-primary" style={{ textTransform: 'capitalize', marginTop: '0.35rem', display: 'inline-block' }}>
                Head of Department
              </span>
            </div>
          </div>

          <div className="teacher-profile-card">
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Full Name</div>
              <div className="teacher-profile-value">{user?.name || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Email</div>
              <div className="teacher-profile-value">{user?.email || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">HOD ID</div>
              <div className="teacher-profile-value">{user?.hod_id || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Department</div>
              <div className="teacher-profile-value">{user?.department || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Phone</div>
              <div className="teacher-profile-value">{user?.phone || '—'}</div>
            </div>
          </div>
        </div>

        <div className="card md:col-span-1">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            <ShieldCheck size={18} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />
            Administrative Role
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Scope</div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', marginTop: '0.2rem' }}>
                Department-wide Oversight
              </div>
            </div>
            <div style={{
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Jurisdiction</div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', marginTop: '0.2rem' }}>
                {user?.department || 'Engineering'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
