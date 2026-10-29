import React from 'react';
import { Outlet } from 'react-router-dom';
import { LayoutDashboard, BookOpen, User, Lock } from 'lucide-react';
import PortalSidebar from '../components/common/PortalSidebar';

const TEACHER_NAV_ITEMS = [
  { path: '/teacher/dashboard', label: 'Dashboard & Roster', icon: LayoutDashboard, section: 'main' },
  { path: '/teacher/subjects', label: 'Manage Subjects', icon: BookOpen, section: 'main' },
  { path: '/teacher/profile', label: 'My Profile', icon: User, section: 'settings' },
  { path: '/teacher/change-password', label: 'Change Password', icon: Lock, section: 'settings' },
];

export default function TeacherLayout() {
  return (
    <>
      <PortalSidebar roleLabel="Teacher" navItems={TEACHER_NAV_ITEMS} />
      <div className="teacher-content-area">
        <div className="portal-page-container">
          <Outlet />
        </div>
      </div>
    </>
  );
}
