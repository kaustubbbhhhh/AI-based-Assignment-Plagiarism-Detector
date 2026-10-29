import React, { useMemo } from 'react';
import { BookOpen } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function TeacherProfilePage() {
  const { user } = useAuth();
  const userInitial = (user?.name || 'T').charAt(0).toUpperCase();

  const teacherSubjectsSections = useMemo(
    () => user?.subjects_sections || [],
    [user?.subjects_sections]
  );

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>My Profile</h2>
        <p>View your account details and teaching assignments.</p>
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
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>{user?.name || 'Teacher'}</h3>
              <span className="badge badge-primary" style={{ textTransform: 'capitalize', marginTop: '0.35rem', display: 'inline-block' }}>
                Teacher
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
              <div className="teacher-profile-label">Teacher ID</div>
              <div className="teacher-profile-value">{user?.teacher_id || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Phone</div>
              <div className="teacher-profile-value">{user?.phone || '—'}</div>
            </div>
            <div className="teacher-profile-row">
              <div className="teacher-profile-label">Department</div>
              <div className="teacher-profile-value">{user?.department || user?.branch || '—'}</div>
            </div>
          </div>
        </div>

        {/* Subjects summary card */}
        <div className="card md:col-span-1">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            <BookOpen size={18} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />
            Teaching Assignments
          </h3>
          {teacherSubjectsSections.length === 0 ? (
            <p className="text-muted" style={{ fontSize: '0.875rem' }}>No subjects assigned yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {teacherSubjectsSections.map((ss, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.7rem 0.9rem',
                    backgroundColor: 'var(--surface-subtle)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-main)' }}>{ss.subject}</div>
                  <div style={{ fontSize: '0.775rem', color: 'var(--primary-color)', fontWeight: 600, marginTop: '0.1rem' }}>
                    Section: {ss.section}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
