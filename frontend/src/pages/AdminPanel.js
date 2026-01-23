import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Crown, Plus, Users } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminPanel({ user }) {
  const [promoCodes, setPromoCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newCode, setNewCode] = useState('');
  const [maxUses, setMaxUses] = useState(0);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchPromoCodes();
    }
  }, [user]);

  const fetchPromoCodes = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/admin/promo/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPromoCodes(response.data);
    } catch (error) {
      toast.error('Failed to load promo codes');
    } finally {
      setLoading(false);
    }
  };

  const createPromoCode = async () => {
    if (!newCode) {
      toast.error('Please enter a promo code');
      return;
    }

    setCreating(true);
    const token = localStorage.getItem('token');

    try {
      await axios.post(`${API}/admin/promo/create?code=${newCode.toUpperCase()}&max_uses=${maxUses}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Promo code created!');
      setNewCode('');
      setMaxUses(0);
      fetchPromoCodes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create promo code');
    } finally {
      setCreating(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-obsidian">
        <Navigation user={user} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
          <h1 className="text-3xl font-cinzel font-bold text-zinc-400">ACCESS DENIED</h1>
          <p className="text-zinc-500 mt-4">Admin access required</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-obsidian" data-testid="admin-panel">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2 flex items-center gap-3">
            <Crown className="w-10 h-10 text-violet-500" />
            ADMIN CONTROL CENTER
          </h1>
          <p className="text-zinc-400">Manage promo codes and premium access</p>
        </motion.div>

        {/* Create Promo Code */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-6"
        >
          <h2 className="text-2xl font-cinzel font-semibold mb-6 flex items-center gap-2">
            <Plus className="w-6 h-6 text-violet-500" />
            CREATE PROMO CODE
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label className="text-zinc-300 mb-2 block">Code</Label>
              <Input
                value={newCode}
                onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                placeholder="SPECIAL2024"
                className="bg-zinc-900 border-zinc-800 uppercase"
                data-testid="new-promo-code-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300 mb-2 block">Max Uses (0 = unlimited)</Label>
              <Input
                type="number"
                value={maxUses}
                onChange={(e) => setMaxUses(parseInt(e.target.value) || 0)}
                className="bg-zinc-900 border-zinc-800"
                data-testid="max-uses-input"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={createPromoCode}
                disabled={creating || !newCode}
                className="w-full bg-violet-600 hover:bg-violet-700"
                data-testid="create-promo-button"
              >
                {creating ? 'CREATING...' : 'CREATE CODE'}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Existing Promo Codes */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6"
        >
          <h2 className="text-2xl font-cinzel font-semibold mb-6 flex items-center gap-2">
            <Users className="w-6 h-6 text-neon-pink" />
            ACTIVE PROMO CODES
          </h2>
          
          {loading ? (
            <p className="text-zinc-400">Loading...</p>
          ) : promoCodes.length === 0 ? (
            <p className="text-zinc-400">No promo codes yet</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {promoCodes.map((promo, index) => (
                <div
                  key={index}
                  className="bg-zinc-900/50 border border-zinc-800 p-4"
                  data-testid={`promo-code-${promo.code}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-violet-400 font-mono">
                      {promo.code}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-bold ${
                      promo.active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {promo.active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm text-zinc-400">
                    <p>
                      <strong className="text-zinc-300">Uses:</strong>{' '}
                      {promo.use_count} {promo.max_uses > 0 ? `/ ${promo.max_uses}` : '/ ∞'}
                    </p>
                    <p>
                      <strong className="text-zinc-300">Created:</strong>{' '}
                      {new Date(promo.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Quick Copy Codes */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-6 mt-6"
        >
          <h3 className="text-xl font-cinzel font-bold mb-3">SHARE WITH FRIENDS</h3>
          <p className="text-zinc-300 text-sm mb-4">
            Give these codes to friends for lifetime premium access:
          </p>
          <div className="flex flex-wrap gap-3">
            {promoCodes.filter(p => p.active).slice(0, 3).map((promo) => (
              <button
                key={promo.code}
                onClick={() => {
                  navigator.clipboard.writeText(promo.code);
                  toast.success('Copied to clipboard!');
                }}
                className="bg-zinc-900 hover:bg-zinc-800 px-4 py-2 font-mono font-bold text-violet-400 border border-zinc-700 hover:border-violet-500 transition-colors"
              >
                {promo.code}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default AdminPanel;
