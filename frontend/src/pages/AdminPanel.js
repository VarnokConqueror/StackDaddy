import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Crown, Plus, Users, Scroll, Copy, Trash2, Shield } from 'lucide-react';
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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [codeToDelete, setCodeToDelete] = useState(null);

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
      toast.error('Failed to summon the royal decrees');
    } finally {
      setLoading(false);
    }
  };

  const createPromoCode = async () => {
    if (!newCode) {
      toast.error('The decree requires a name, Your Majesty');
      return;
    }

    setCreating(true);
    const token = localStorage.getItem('token');

    try {
      await axios.post(`${API}/admin/promo/create?code=${newCode.toUpperCase()}&max_uses=${maxUses}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Royal decree has been inscribed!');
      setNewCode('');
      setMaxUses(0);
      fetchPromoCodes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'The scribes failed to inscribe the decree');
    } finally {
      setCreating(false);
    }
  };

  const revokePromoCode = async () => {
    if (!codeToDelete) return;
    
    const token = localStorage.getItem('token');
    try {
      await axios.delete(`${API}/admin/promo/${codeToDelete}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('The decree has been revoked');
      setDeleteDialogOpen(false);
      setCodeToDelete(null);
      fetchPromoCodes();
    } catch (error) {
      toast.error('Failed to revoke the decree');
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('Decree copied to thy clipboard!');
  };

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-obsidian">
        <Navigation user={user} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
          <Shield className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
          <h1 className="text-3xl font-cinzel font-bold text-zinc-400">THE THRONE ROOM IS SEALED</h1>
          <p className="text-zinc-500 mt-4 italic">Only those of royal blood may enter these chambers</p>
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
            THE THRONE ROOM
          </h1>
          <p className="text-zinc-400 italic">Issue royal decrees to grant premium access to your loyal subjects</p>
        </motion.div>

        {/* Create Promo Code */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-6"
        >
          <h2 className="text-2xl font-cinzel font-semibold mb-2 flex items-center gap-2">
            <Scroll className="w-6 h-6 text-violet-500" />
            INSCRIBE NEW DECREE
          </h2>
          <p className="text-zinc-500 text-sm mb-6 italic">Create a sacred code to bestow premium privileges</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label className="text-zinc-300 mb-2 block">Decree Name</Label>
              <Input
                value={newCode}
                onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                placeholder="ROYAL2024"
                className="bg-zinc-900 border-zinc-800 uppercase font-mono"
                data-testid="new-promo-code-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300 mb-2 block">Blessings Granted (0 = Infinite)</Label>
              <Input
                type="number"
                value={maxUses}
                onChange={(e) => setMaxUses(parseInt(e.target.value) || 0)}
                className="bg-zinc-900 border-zinc-800"
                data-testid="max-uses-input"
              />
              <p className="text-xs text-zinc-600 mt-1">How many subjects may use this decree</p>
            </div>
            <div className="flex items-end">
              <Button
                onClick={createPromoCode}
                disabled={creating || !newCode}
                className="w-full bg-violet-600 hover:bg-violet-700"
                data-testid="create-promo-button"
              >
                {creating ? 'INSCRIBING...' : 'INSCRIBE DECREE'}
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
          <h2 className="text-2xl font-cinzel font-semibold mb-2 flex items-center gap-2">
            <Users className="w-6 h-6 text-neon-pink" />
            ROYAL DECREES
          </h2>
          <p className="text-zinc-500 text-sm mb-6 italic">Active codes that grant premium access to your kingdom</p>
          
          {loading ? (
            <p className="text-zinc-400 italic">Consulting the royal archives...</p>
          ) : promoCodes.length === 0 ? (
            <div className="text-center py-12">
              <Scroll className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-400 italic">No decrees have been inscribed yet</p>
              <p className="text-zinc-600 text-sm mt-2">Create your first decree above to grant access to loyal subjects</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {promoCodes.map((promo, index) => (
                <motion.div
                  key={promo.code}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-zinc-900/50 border border-zinc-800 p-4 hover:border-violet-500/30 transition-colors"
                  data-testid={`promo-code-${promo.code}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-violet-400 font-mono">
                      {promo.code}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs font-bold ${
                        promo.active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {promo.active ? 'BLESSED' : 'REVOKED'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-1 text-sm text-zinc-400 mb-4">
                    <p>
                      <strong className="text-zinc-300">Subjects Blessed:</strong>{' '}
                      {promo.use_count} {promo.max_uses > 0 ? `/ ${promo.max_uses}` : '/ ∞'}
                    </p>
                    <p>
                      <strong className="text-zinc-300">Inscribed:</strong>{' '}
                      {new Date(promo.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      onClick={() => copyCode(promo.code)}
                      variant="outline"
                      size="sm"
                      className="flex-1 border-zinc-700 hover:border-violet-500"
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </Button>
                    <Button
                      onClick={() => {
                        setCodeToDelete(promo.code);
                        setDeleteDialogOpen(true);
                      }}
                      variant="outline"
                      size="sm"
                      className="border-zinc-700 hover:border-red-500 hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Quick Share Section */}
        {promoCodes.filter(p => p.active).length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-6 mt-6"
          >
            <h3 className="text-xl font-cinzel font-bold mb-2">BESTOW UPON YOUR ALLIES</h3>
            <p className="text-zinc-300 text-sm mb-4 italic">
              Click to copy these decrees and share with those worthy of premium access
            </p>
            <div className="flex flex-wrap gap-3">
              {promoCodes.filter(p => p.active).slice(0, 5).map((promo) => (
                <button
                  key={promo.code}
                  onClick={() => copyCode(promo.code)}
                  className="bg-zinc-900 hover:bg-zinc-800 px-4 py-2 font-mono font-bold text-violet-400 border border-zinc-700 hover:border-violet-500 transition-all duration-200 hover:scale-105"
                >
                  {promo.code}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Revoke Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-cinzel text-red-400">
              REVOKE THIS DECREE?
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <p className="text-zinc-400 mb-2">
              The decree <span className="font-mono text-violet-400 font-bold">{codeToDelete}</span> shall be struck from the royal records.
            </p>
            <p className="text-zinc-500 mb-6 italic text-sm">
              Those who have already been blessed shall retain their privileges, but no new subjects may use this code.
            </p>
            <div className="flex gap-3">
              <Button
                onClick={() => setDeleteDialogOpen(false)}
                variant="outline"
                className="flex-1 border-zinc-700 hover:bg-zinc-800"
              >
                SPARE IT
              </Button>
              <Button
                onClick={revokePromoCode}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                REVOKE
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminPanel;
