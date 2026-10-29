import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Legacy StudentPortal wrapper.
 * The portal has been refactored into modular routes and layouts under /student/*.
 * This component redirects to the primary route for backward compatibility.
 */
export default function StudentPortal() {
  return <Navigate to="/student/submit" replace />;
}
