import React from 'react';
import { Outlet } from 'react-router-dom';
import { BarChart3, Cpu, User, Lock } from 'lucide-react';
import PortalSidebar from '../components/common/PortalSidebar';

const HOD_NAV_ITEMS = [
  { path: '/hod/overview', label: 'Institutional Overview', icon: BarChart3, section: 'main' },
  { path: '/hod/forensic-ai', label: 'Forensic AI Analytics', icon: Cpu, section: 'main' },
  { path: '/hod/profile', label: 'My Profile', icon: User, section: 'settings' },
  { path: '/hod/change-password', label: 'Change Password', icon: Lock, section: 'settings' },
];

export default function HODLayout() {
  return (
    <>
      <PortalSidebar roleLabel="HOD" navItems={HOD_NAV_ITEMS} />
      <div className="teacher-content-area">
        <div className="portal-page-container">
          <Outlet />
        </div>
      </div>
    </>
  );
}
