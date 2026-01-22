import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Crown } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function Login({ setUser }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      localStorage.setItem('token', response.data.token);
      setUser(response.data.user);
      toast.success('Welcome back to the Court!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Crown className="w-16 h-16 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-cinzel font-black uppercase glow-text mb-2">RETURN TO COURT</h1>
          <p className="text-zinc-400">Enter your credentials to continue</p>
        </div>

        <div className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8">
          <form onSubmit={handleLogin} className="space-y-6" data-testid="login-form">
            <div>
              <Label htmlFor="email" className="text-zinc-300 mb-2 block">EMAIL</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-zinc-950 border-zinc-800 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 h-12 text-zinc-100"
                data-testid="login-email-input"
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-zinc-300 mb-2 block">PASSWORD</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-zinc-950 border-zinc-800 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 h-12 text-zinc-100"
                data-testid="login-password-input"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white h-12 uppercase tracking-widest font-bold transition-all duration-300 hover:shadow-[0_0_20px_rgba(124,58,237,0.5)]"
              data-testid="login-submit-button"
            >
              {loading ? 'ENTERING...' : 'ENTER COURT'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-zinc-400">
              New to the Court?{' '}
              <Link to="/register" className="text-neon-pink hover:text-pink-400 font-semibold" data-testid="register-link">
                Begin Your Reign
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;