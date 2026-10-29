import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Public & Auth Pages
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import AdminLogin from './pages/AdminLogin';
import ChangePasswordRequired from './pages/ChangePasswordRequired';
import Navbar from './components/Navbar';

// Admin Architecture
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import StudentManagement from './pages/admin/StudentManagement';
import TeacherManagement from './pages/admin/TeacherManagement';
import HODManagement from './pages/admin/HODManagement';
import SubjectManagement from './pages/admin/SubjectManagement';

// HOD Architecture
import HODLayout from './layouts/HODLayout';
import HODOverviewPage from './pages/hod/HODOverviewPage';
import HODForensicAIPage from './pages/hod/HODForensicAIPage';
import HODProfilePage from './pages/hod/HODProfilePage';
import HODChangePasswordPage from './pages/hod/HODChangePasswordPage';

// Teacher Architecture
import TeacherLayout from './layouts/TeacherLayout';
import TeacherDashboardPage from './pages/teacher/TeacherDashboardPage';
import TeacherSubjectsPage from './pages/teacher/TeacherSubjectsPage';
import TeacherProfilePage from './pages/teacher/TeacherProfilePage';
import TeacherChangePasswordPage from './pages/teacher/TeacherChangePasswordPage';

// Student Architecture
import StudentLayout from './layouts/StudentLayout';
import StudentSubmitAssignmentPage from './pages/student/StudentSubmitAssignmentPage';
import StudentSubmissionsPage from './pages/student/StudentSubmissionsPage';
import StudentProfilePage from './pages/student/StudentProfilePage';
import StudentChangePasswordPage from './pages/student/StudentChangePasswordPage';

function PublicAuthRoute({ children }) {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ minHeight: '60vh' }}>
        <div className="spinner" style={{ width: '32px', height: '32px' }}></div>
      </div>
    );
  }

  // If already authenticated, redirect directly to user's academic portal
  if (isAuthenticated && user?.role) {
    if (user.must_change_password) return <Navigate to="/change-password-required" replace />;
    if (user.role === 'student') return <Navigate to="/student" replace />;
    if (user.role === 'teacher') return <Navigate to="/teacher" replace />;
    if (user.role === 'hod') return <Navigate to="/hod" replace />;
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
  }

  return children;
}

function AppContent() {
  const location = useLocation();
  const isTeacherRoute = location.pathname.startsWith('/teacher');
  const isStudentRoute = location.pathname.startsWith('/student');
  const isHODRoute = location.pathname.startsWith('/hod');
  const isAdminRoute = location.pathname.startsWith('/admin') && location.pathname !== '/admin/login';
  const isPortalRoute = isTeacherRoute || isStudentRoute || isHODRoute || isAdminRoute;

  return (
    <div className={`min-h-screen app-shell ${isPortalRoute ? 'teacher-layout' : ''}`}>
      <div className="bg-shape-1"></div>
      <div className="bg-shape-2"></div>
      {!isPortalRoute && <Navbar />}
      {isPortalRoute ? (
        <>
          {isTeacherRoute && (
            <ProtectedRoute allowedRoles={['teacher']}>
              <Routes>
                <Route path="/teacher" element={<TeacherLayout />}>
                  <Route index element={<Navigate to="/teacher/dashboard" replace />} />
                  <Route path="dashboard" element={<TeacherDashboardPage />} />
                  <Route path="subjects" element={<TeacherSubjectsPage />} />
                  <Route path="profile" element={<TeacherProfilePage />} />
                  <Route path="change-password" element={<TeacherChangePasswordPage />} />
                  <Route path="*" element={<Navigate to="/teacher/dashboard" replace />} />
                </Route>
              </Routes>
            </ProtectedRoute>
          )}

          {isStudentRoute && (
            <ProtectedRoute allowedRoles={['student']}>
              <Routes>
                <Route path="/student" element={<StudentLayout />}>
                  <Route index element={<Navigate to="/student/submit" replace />} />
                  <Route path="submit" element={<StudentSubmitAssignmentPage />} />
                  <Route path="submissions" element={<StudentSubmissionsPage />} />
                  <Route path="profile" element={<StudentProfilePage />} />
                  <Route path="change-password" element={<StudentChangePasswordPage />} />
                  <Route path="*" element={<Navigate to="/student/submit" replace />} />
                </Route>
              </Routes>
            </ProtectedRoute>
          )}

          {isHODRoute && (
            <ProtectedRoute allowedRoles={['hod']}>
              <Routes>
                <Route path="/hod" element={<HODLayout />}>
                  <Route index element={<Navigate to="/hod/overview" replace />} />
                  <Route path="overview" element={<HODOverviewPage />} />
                  <Route path="forensic-ai" element={<HODForensicAIPage />} />
                  <Route path="profile" element={<HODProfilePage />} />
                  <Route path="change-password" element={<HODChangePasswordPage />} />
                  <Route path="*" element={<Navigate to="/hod/overview" replace />} />
                </Route>
              </Routes>
            </ProtectedRoute>
          )}

          {isAdminRoute && (
            <ProtectedRoute allowedRoles={['admin']}>
              <Routes>
                <Route path="/admin" element={<AdminLayout />}>
                  <Route index element={<AdminDashboard />} />
                  <Route path="dashboard" element={<Navigate to="/admin" replace />} />
                  <Route path="users" element={<Navigate to="/admin/users/students" replace />} />
                  <Route path="users/students" element={<StudentManagement />} />
                  <Route path="users/teachers" element={<TeacherManagement />} />
                  <Route path="users/hods" element={<HODManagement />} />
                  <Route path="academic/subjects" element={<SubjectManagement />} />
                  <Route path="subjects" element={<Navigate to="/admin/academic/subjects" replace />} />
                  <Route path="*" element={<Navigate to="/admin" replace />} />
                </Route>
              </Routes>
            </ProtectedRoute>
          )}
        </>
      ) : (
        <main className="container app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route
              path="/login"
              element={
                <PublicAuthRoute>
                  <Login />
                </PublicAuthRoute>
              }
            />
            <Route
              path="/admin/login"
              element={<AdminLogin />}
            />
            <Route
              path="/change-password-required"
              element={<ChangePasswordRequired />}
            />
            <Route
              path="/register"
              element={<Navigate to="/login" replace />}
            />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
          </Routes>
        </main>
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/*" element={<AppContent />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
