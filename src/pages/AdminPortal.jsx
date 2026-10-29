import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Legacy AdminPortal wrapper.
 * Admin has been modularized into /admin/* using AdminLayout and src/pages/admin/*.
 * This component redirects to the admin dashboard for backward compatibility.
 */
export default function AdminPortal() {
  return <Navigate to="/admin" replace />;
}
