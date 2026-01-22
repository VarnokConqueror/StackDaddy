import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Crown } from 'lucide-react';
import { toast } from 'sonner';
import SocialAuthButtons from '@/components/SocialAuthButtons';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function Register({ setUser }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register`, { name, email, password });
      localStorage.setItem('token', response.data.token);
      setUser(response.data.user);
      toast.success('Welcome to the Court!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Crown className="w-16 h-16 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-cinzel font-black uppercase glow-text mb-2">JOIN THE COURT</h1>
          <p className="text-zinc-400">Begin your nutrition conquest</p>
        </div>

        <div className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8">
          <SocialAuthButtons />

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-zinc-800" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-zinc-950 text-zinc-500">Or continue with email</span>
            </div>
          </div>

          <form onSubmit={handleRegister} className="space-y-6" data-testid="register-form">
            <div>
              <Label htmlFor="name" className="text-zinc-300 mb-2 block">NAME</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-zinc-950 border-zinc-800 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 h-12 text-zinc-100"
                data-testid="register-name-input"
              />
            </div>
            <div>
              <Label htmlFor="email" className="text-zinc-300 mb-2 block">EMAIL</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-zinc-950 border-zinc-800 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 h-12 text-zinc-100"
                data-testid="register-email-input"
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
                data-testid="register-password-input"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white h-12 uppercase tracking-widest font-bold transition-all duration-300 hover:shadow-[0_0_20px_rgba(124,58,237,0.5)]"
              data-testid="register-submit-button"
            >
              {loading ? 'CREATING...' : 'CLAIM YOUR THRONE'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-zinc-400">
              Already a member?{' '}
              <Link to="/login" className="text-neon-pink hover:text-pink-400 font-semibold" data-testid="login-link">
                Enter Court
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;