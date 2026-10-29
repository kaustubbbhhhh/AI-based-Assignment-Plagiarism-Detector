import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  UserCheck,
  Award,
  BookOpen,
  ChevronRight,
  ShieldCheck,
  LogOut,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Auto-expand User Management when visiting child routes
  const isUserMgmtActive = location.pathname.startsWith('/admin/users');
  const [userMgmtOpen, setUserMgmtOpen] = useState(isUserMgmtActive || true);

  const isAcademicMgmtActive = location.pathname.startsWith('/admin/academic') || location.pathname === '/admin/subjects';
  const [academicMgmtOpen, setAcademicMgmtOpen] = useState(isAcademicMgmtActive || true);

  // Keep dropdowns expanded when navigating to an active child route
  const [prevPath, setPrevPath] = useState(location.pathname);
  if (location.pathname !== prevPath) {
    setPrevPath(location.pathname);
    if (isUserMgmtActive && !userMgmtOpen) setUserMgmtOpen(true);
    if (isAcademicMgmtActive && !academicMgmtOpen) setAcademicMgmtOpen(true);
  }

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  const userInitial = (user?.name || 'A').charAt(0).toUpperCase();

  // Generate breadcrumb items from pathname
  const getBreadcrumbs = () => {
    const p = location.pathname;
    if (p === '/admin' || p === '/admin/dashboard') {
      return [{ label: 'Admin', path: '/admin' }, { label: 'Dashboard' }];
    }
    if (p === '/admin/users/students') {
      return [
        { label: 'Admin', path: '/admin' },
        { label: 'User Management', path: '/admin/users/students' },
        { label: 'Student Management' },
      ];
    }
    if (p === '/admin/users/teachers') {
      return [
        { label: 'Admin', path: '/admin' },
        { label: 'User Management', path: '/admin/users/students' },
        { label: 'Teacher Management' },
      ];
    }
    if (p === '/admin/users/hods') {
      return [
        { label: 'Admin', path: '/admin' },
        { label: 'User Management', path: '/admin/users/students' },
        { label: 'HOD Management' },
      ];
    }
    if (p === '/admin/academic/subjects' || p === '/admin/subjects') {
      return [
        { label: 'Admin', path: '/admin' },
        { label: 'Academic Management', path: '/admin/academic/subjects' },
        { label: 'Subject Management' },
      ];
    }
    return [{ label: 'Admin', path: '/admin' }];
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <div style={{ display: 'flex', width: '100%', minWidth: 0, flex: 1, minHeight: '100vh', background: 'var(--bg-color)' }}>
      {/* ── Sidebar ── */}
      <aside
        className={`sidebar-panel ${sidebarOpen ? 'sidebar-open' : ''}`}
        style={{
          width: '260px', minWidth: '260px', background: 'var(--surface-color)',
          borderRight: '1px solid var(--border-color)', display: 'flex',
          flexDirection: 'column', position: 'fixed', top: 0, left: 0, bottom: 0,
          zIndex: 100, transform: sidebarOpen ? 'translateX(0)' : undefined,
          transition: 'transform 0.2s ease',
        }}
      >
        {/* Brand */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
            color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1rem' }}>Admin Panel</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PlagiarismAI</div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="btn" style={{ marginLeft: 'auto', padding: '0.25rem', display: 'none' }} aria-label="Close sidebar">
            <X size={18} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav style={{ flex: 1, padding: '1rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', overflowY: 'auto' }}>
          {/* Dashboard */}
          <button
            onClick={() => { navigate('/admin'); setSidebarOpen(false); }}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              padding: '0.7rem 1rem', borderRadius: 'var(--radius-md)',
              border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left',
              fontSize: '0.9rem',
              fontWeight: location.pathname === '/admin' || location.pathname === '/admin/dashboard' ? 700 : 500,
              background: (location.pathname === '/admin' || location.pathname === '/admin/dashboard') ? 'var(--primary-light)' : 'transparent',
              color: (location.pathname === '/admin' || location.pathname === '/admin/dashboard') ? 'var(--primary-color)' : 'var(--text-main)',
              transition: 'var(--transition)',
              marginBottom: '0.35rem',
            }}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </button>

          {/* User Management (Collapsible) */}
          <div className="sidebar-nav-group">
            <button
              type="button"
              className={`sidebar-nav-header ${isUserMgmtActive ? 'parent-active' : ''}`}
              onClick={() => setUserMgmtOpen(!userMgmtOpen)}
              aria-expanded={userMgmtOpen}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Users size={18} style={{ color: isUserMgmtActive ? 'var(--primary-color)' : 'inherit' }} />
                <span>User Management</span>
              </span>
              <ChevronRight size={16} className={`sidebar-chevron ${userMgmtOpen ? 'expanded' : ''}`} />
            </button>

            {/* Collapsible Submenu */}
            <div className={`sidebar-submenu ${userMgmtOpen ? 'expanded' : ''}`}>
              <div className="sidebar-submenu-inner">
                <button
                  type="button"
                  className={`sidebar-subitem ${location.pathname === '/admin/users/students' ? 'active' : ''}`}
                  onClick={() => { navigate('/admin/users/students'); setSidebarOpen(false); }}
                >
                  <GraduationCap size={15} />
                  <span>Student Management</span>
                </button>

                <button
                  type="button"
                  className={`sidebar-subitem ${location.pathname === '/admin/users/teachers' ? 'active' : ''}`}
                  onClick={() => { navigate('/admin/users/teachers'); setSidebarOpen(false); }}
                >
                  <UserCheck size={15} />
                  <span>Teacher Management</span>
                </button>

                <button
                  type="button"
                  className={`sidebar-subitem ${location.pathname === '/admin/users/hods' ? 'active' : ''}`}
                  onClick={() => { navigate('/admin/users/hods'); setSidebarOpen(false); }}
                >
                  <Award size={15} />
                  <span>HOD Management</span>
                </button>
              </div>
            </div>
          </div>

          {/* Academic Management (Collapsible) */}
          <div className="sidebar-nav-group">
            <button
              type="button"
              className={`sidebar-nav-header ${isAcademicMgmtActive ? 'parent-active' : ''}`}
              onClick={() => setAcademicMgmtOpen(!academicMgmtOpen)}
              aria-expanded={academicMgmtOpen}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <BookOpen size={18} style={{ color: isAcademicMgmtActive ? 'var(--primary-color)' : 'inherit' }} />
                <span>Academic Management</span>
              </span>
              <ChevronRight size={16} className={`sidebar-chevron ${academicMgmtOpen ? 'expanded' : ''}`} />
            </button>

            {/* Collapsible Submenu */}
            <div className={`sidebar-submenu ${academicMgmtOpen ? 'expanded' : ''}`}>
              <div className="sidebar-submenu-inner">
                <button
                  type="button"
                  className={`sidebar-subitem ${location.pathname === '/admin/academic/subjects' || location.pathname === '/admin/subjects' ? 'active' : ''}`}
                  onClick={() => { navigate('/admin/academic/subjects'); setSidebarOpen(false); }}
                >
                  <BookOpen size={15} />
                  <span>Subject Management</span>
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* User Info & Logout */}
        <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: 'var(--radius-full)',
              background: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
              color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700, fontSize: '0.95rem', flexShrink: 0,
            }}>
              {userInitial}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name || 'Admin'}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{user?.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="btn btn-outline w-full" style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}>
            <LogOut size={14} /> Logout
          </button>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <main className="teacher-content-area admin-main-area">
        <div className="portal-page-container">
          {/* Mobile Header */}
          <div style={{ display: 'none', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }} className="mobile-header">
            <button onClick={() => setSidebarOpen(true)} className="btn btn-outline" style={{ padding: '0.5rem' }}>
              <Menu size={20} />
            </button>
            <span style={{ fontWeight: 700 }}>Admin Panel</span>
            <div style={{ width: '36px' }} />
          </div>

          {/* Breadcrumb Navigation */}
          <div className="admin-breadcrumbs">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span className="crumb-separator">/</span>}
                {crumb.path ? (
                  <Link to={crumb.path} className="crumb-link">{crumb.label}</Link>
                ) : (
                  <span className="crumb-active">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Nested Route View */}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
