import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  BookOpen,
  GraduationCap,
  UserCheck,
  Award,
  Key,
  BookMarked,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../../utils/api';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    students: 0,
    teachers: 0,
    hods: 0,
    admins: 0,
    subjects: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchStats = async () => {
      try {
        const [stuRes, teaRes, hodRes, admRes, subRes] = await Promise.all([
          api.get('/api/admin/users?role=student&limit=1'),
          api.get('/api/admin/users?role=teacher&limit=1'),
          api.get('/api/admin/users?role=hod&limit=1'),
          api.get('/api/admin/users?role=admin&limit=1'),
          api.get('/api/admin/subjects?limit=1'),
        ]);

        const [stuData, teaData, hodData, admData, subData] = await Promise.all([
          stuRes.ok ? stuRes.json() : { total: 0 },
          teaRes.ok ? teaRes.json() : { total: 0 },
          hodRes.ok ? hodRes.json() : { total: 0 },
          admRes.ok ? admRes.json() : { total: 0 },
          subRes.ok ? subRes.json() : { total: 0 },
        ]);

        if (isMounted) {
          setStats({
            students: stuData.total,
            teachers: teaData.total,
            hods: hodData.total,
            admins: admData.total,
            subjects: subData.total,
          });
          setLoading(false);
        }
      } catch {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchStats();
    return () => {
      isMounted = false;
    };
  }, []);

  const statCards = [
    { label: 'Students', value: stats.students, color: '#6366f1', icon: GraduationCap, path: '/admin/users/students' },
    { label: 'Teachers', value: stats.teachers, color: '#10b981', icon: UserCheck, path: '/admin/users/teachers' },
    { label: 'HODs', value: stats.hods, color: '#f59e0b', icon: Award, path: '/admin/users/hods' },
    { label: 'Admins', value: stats.admins, color: '#ef4444', icon: Key, path: null },
    { label: 'Subjects', value: stats.subjects, color: '#8b5cf6', icon: BookMarked, path: '/admin/academic/subjects' },
  ];

  return (
    <div style={{ width: '100%' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.4rem 0' }}>Admin Dashboard</h2>
        <p className="text-muted" style={{ margin: 0, fontSize: '0.95rem' }}>
          Welcome to the administrative management control center.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', marginBottom: '2.25rem' }}>
        {statCards.map(stat => (
          <div
            key={stat.label}
            className="card"
            style={{
              padding: '1.35rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              cursor: stat.path ? 'pointer' : 'default',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            }}
            onClick={() => stat.path && navigate(stat.path)}
          >
            <div style={{
              width: '48px', height: '48px', borderRadius: 'var(--radius-lg)',
              background: `${stat.color}15`, color: stat.color,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <stat.icon size={24} />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: stat.color, lineHeight: 1.2 }}>
                {loading ? '–' : stat.value}
              </div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                {stat.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Navigation Sections */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem' }}>Quick Management Portals</h3>
        <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {/* Student Management */}
          <div
            className="card"
            style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => navigate('/admin/users/students')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.1)', color: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <GraduationCap size={20} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Student Management</h4>
              </div>
              <p className="text-muted" style={{ fontSize: '0.875rem', margin: '0 0 1rem 0' }}>
                Enroll students, manage batches, branches, semesters, and reset credentials.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--primary-color)', fontSize: '0.85rem', fontWeight: 600 }}>
              Manage Students <ArrowRight size={14} />
            </div>
          </div>

          {/* Teacher Management */}
          <div
            className="card"
            style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => navigate('/admin/users/teachers')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserCheck size={20} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Teacher Management</h4>
              </div>
              <p className="text-muted" style={{ fontSize: '0.875rem', margin: '0 0 1rem 0' }}>
                Create faculty accounts, assign employee IDs, departments, and maintain access.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981', fontSize: '0.85rem', fontWeight: 600 }}>
              Manage Teachers <ArrowRight size={14} />
            </div>
          </div>

          {/* HOD Management */}
          <div
            className="card"
            style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => navigate('/admin/users/hods')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Award size={20} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>HOD Management</h4>
              </div>
              <p className="text-muted" style={{ fontSize: '0.875rem', margin: '0 0 1rem 0' }}>
                Manage Heads of Department, assign departments, and oversee department privileges.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f59e0b', fontSize: '0.85rem', fontWeight: 600 }}>
              Manage HODs <ArrowRight size={14} />
            </div>
          </div>

          {/* Subject Management */}
          <div
            className="card"
            style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => navigate('/admin/academic/subjects')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <BookMarked size={20} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Subject Management</h4>
              </div>
              <p className="text-muted" style={{ fontSize: '0.875rem', margin: '0 0 1rem 0' }}>
                Configure academic subjects, branch-semester syllabi, and maintain curriculum.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#8b5cf6', fontSize: '0.85rem', fontWeight: 600 }}>
              Manage Subjects <ArrowRight size={14} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
