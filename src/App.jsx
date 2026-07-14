import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import StudentPortal from './pages/StudentPortal';
import TeacherPortal from './pages/TeacherPortal';
import HODPortal from './pages/HODPortal';
import Navbar from './components/Navbar';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen app-shell">
        <div className="bg-shape-1"></div>
        <div className="bg-shape-2"></div>
        <Navbar />
        <main className="container app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/student/*" element={<StudentPortal />} />
            <Route path="/teacher/*" element={<TeacherPortal />} />
            <Route path="/hod/*" element={<HODPortal />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
