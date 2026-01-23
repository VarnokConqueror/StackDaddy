import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { useState, useEffect } from 'react';
import axios from 'axios';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';
import MealPlanner from './pages/MealPlanner';
import ShoppingList from './pages/ShoppingList';
import SupplementLibrary from './pages/SupplementLibrary';
import MySupplements from './pages/MySupplements';
import Profile from './pages/Profile';
import Subscription from './pages/Subscription';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import AdminPanel from './pages/AdminPanel';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => {
        setUser(response.data);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem('token');
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  const ProtectedRoute = ({ children }) => {
    if (loading) return <div className="min-h-screen bg-obsidian flex items-center justify-center"><div className="text-zinc-400">Loading...</div></div>;
    return user ? children : <Navigate to="/login" />;
  };

  // Check for OAuth callback during render (not in useEffect to avoid race conditions)
  function AppRouter() {
    const location = useLocation();
    if (location.hash?.includes('session_id=')) {
      return <AuthCallback />;
    }
    
    return (
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Landing />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login setUser={setUser} />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <Register setUser={setUser} />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard user={user} /></ProtectedRoute>} />
        <Route path="/meal-planner" element={<ProtectedRoute><MealPlanner user={user} /></ProtectedRoute>} />
        <Route path="/shopping-list" element={<ProtectedRoute><ShoppingList user={user} /></ProtectedRoute>} />
        <Route path="/supplements" element={<ProtectedRoute><SupplementLibrary user={user} /></ProtectedRoute>} />
        <Route path="/my-supplements" element={<ProtectedRoute><MySupplements user={user} /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile user={user} setUser={setUser} /></ProtectedRoute>} />
        <Route path="/subscription" element={<ProtectedRoute><Subscription user={user} setUser={setUser} /></ProtectedRoute>} />
        <Route path="/subscription/success" element={<ProtectedRoute><SubscriptionSuccess user={user} setUser={setUser} /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><AdminPanel user={user} /></ProtectedRoute>} />
      </Routes>
    );
  }

  if (loading) {
    return <div className="min-h-screen bg-obsidian flex items-center justify-center"><div className="text-zinc-400">Loading...</div></div>;
  }

  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;