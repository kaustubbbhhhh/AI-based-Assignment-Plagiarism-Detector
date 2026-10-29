import React from 'react';
import { Outlet } from 'react-router-dom';
import { UploadCloud, Clock, User, Lock } from 'lucide-react';
import PortalSidebar from '../components/common/PortalSidebar';

const STUDENT_NAV_ITEMS = [
  { path: '/student/submit', label: 'Submit Assignment', icon: UploadCloud, section: 'main' },
  { path: '/student/submissions', label: 'My Submissions', icon: Clock, section: 'main' },
  { path: '/student/profile', label: 'My Profile', icon: User, section: 'settings' },
  { path: '/student/change-password', label: 'Change Password', icon: Lock, section: 'settings' },
];

export default function StudentLayout() {
  return (
    <>
      <PortalSidebar roleLabel="Student" navItems={STUDENT_NAV_ITEMS} />
      <main className="teacher-content-area">
        <div className="portal-page-container">
          <Outlet />
        </div>
      </main>
    </>
  );
}
