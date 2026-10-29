import React from 'react';
import { Phone } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function StudentProfilePage() {
  const { user } = useAuth();
  const userInitial = (user?.name || 'S').charAt(0).toUpperCase();

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>My Profile</h2>
        <p>View your student credentials, academic status, and registered contact details.</p>
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
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>{user?.name || 'Student'}</h3>
              <span className="badge badge-accent" style={{ textTransform: 'capitalize', marginTop: '0.35rem', display: 'inline-block' }}>
                Student
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
              <div className="teacher-profile-label">Roll Number</div>
              <div className="teacher-profile-value">{user?.enrollment_no || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Class Section</div>
              <div className="teacher-profile-value">{user?.section || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Branch</div>
              <div className="teacher-profile-value">{user?.branch || user?.department || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Phone</div>
              <div className="teacher-profile-value">{user?.phone || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Session</div>
              <div className="teacher-profile-value">{user?.session || '—'}</div>
            </div>
          </div>
        </div>

        {/* Emergency / Guardian Contacts Card */}
        <div className="card md:col-span-1">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            <Phone size={18} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />
            Guardian Contacts
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Father's Phone</div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', marginTop: '0.2rem' }}>
                {user?.father_phone || 'Not Provided'}
              </div>
            </div>
            <div style={{
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mother's Phone</div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', marginTop: '0.2rem' }}>
                {user?.mother_phone || 'Not Provided'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
