import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Legacy TeacherPortal wrapper.
 * The portal has been refactored into modular routes and layouts under /teacher/*.
 * This component redirects to the primary route for backward compatibility.
 */
export default function TeacherPortal() {
  return <Navigate to="/teacher/dashboard" replace />;
}
