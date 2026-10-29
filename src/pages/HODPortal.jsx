import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Legacy HODPortal wrapper.
 * The portal has been refactored into modular routes and layouts under /hod/*.
 * This component redirects to the primary route for backward compatibility.
 */
export default function HODPortal() {
  return <Navigate to="/hod/overview" replace />;
}
