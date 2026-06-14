import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MobileLayout from './components/layout/MobileLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProjectDashboard from './pages/ProjectDashboard';
import ApiExplorer from './pages/ApiExplorer';
import Dashboard from './pages/Dashboard';

const App = () => {
  const isAuthenticated = !!localStorage.getItem('omnicore_token');

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route 
          path="/*" 
          element={
            isAuthenticated ? (
              <MobileLayout>
                <Routes>
                  <Route path="/projects" element={<ProjectDashboard />} />
                  <Route path="/explorer" element={<ApiExplorer />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/" element={<Navigate to="/projects" />} />
                </Routes>
              </MobileLayout>
            ) : (
              <Navigate to="/login" />
            )
          } 
        />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
