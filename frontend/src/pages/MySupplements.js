import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Heart, Trash2, Edit, Check } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function MySupplements({ user }) {
  const [supplements, setSupplements] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logDialogOpen, setLogDialogOpen] = useState(false);
  const [selectedSupplement, setSelectedSupplement] = useState(null);
  const [logData, setLogData] = useState({ dose_taken: '', notes: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem('token');
    try {
      const [suppsRes, logsRes] = await Promise.all([
        axios.get(`${API}/user-supplements`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/supplement-logs`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setSupplements(suppsRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      toast.error('Failed to load supplements');
    } finally {
      setLoading(false);
    }
  };

  const logSupplement = async () => {
    if (!logData.dose_taken) {
      toast.error('Please enter dose taken');
      return;
    }

    const token = localStorage.getItem('token');
    
    try {
      await axios.post(`${API}/supplement-logs`, {
        user_supplement_id: selectedSupplement.id,
        dose_taken: parseFloat(logData.dose_taken),
        notes: logData.notes
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Supplement logged!');
      setLogDialogOpen(false);
      setLogData({ dose_taken: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to log supplement');
    }
  };

  const deleteSupplement = async (suppId) => {
    const token = localStorage.getItem('token');
    
    try {
      await axios.delete(`${API}/user-supplements/${suppId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Supplement removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove supplement');
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="my-supplements-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2">MY SUPPLEMENTS</h1>
          <p className="text-zinc-400">Track your supplement inventory and dosage</p>
        </motion.div>

        {loading ? (
          <div className="text-center py-12 text-zinc-400">Loading...</div>
        ) : supplements.length === 0 ? (
          <div className="text-center py-24">
            <Heart className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold text-zinc-400 mb-2">NO SUPPLEMENTS YET</h2>
            <p className="text-zinc-500 mb-6">Add supplements from the library to start tracking</p>
            <Button
              onClick={() => window.location.href = '/supplements'}
              className="bg-neon-pink hover:bg-pink-600"
            >
              BROWSE SUPPLEMENTS
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {supplements.map((supp, index) => (
                <motion.div
                  key={supp.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-neon-pink/30 transition-colors duration-300"
                  data-testid={`user-supplement-${supp.id}`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-cinzel font-semibold mb-2">{supp.supplement_name}</h3>
                      <p className="text-sm text-zinc-400">{supp.custom_dose} {supp.dose_unit}</p>
                      <p className="text-sm text-zinc-500">{supp.frequency}</p>
                    </div>
                    <Heart className="w-6 h-6 text-neon-pink" />
                  </div>

                  <div className="space-y-2 mb-4 text-sm">
                    <p className="text-zinc-400">
                      <strong className="text-zinc-300">Stock:</strong> {supp.stock_quantity} doses
                    </p>
                    {supp.expiration_date && (
                      <p className="text-zinc-400">
                        <strong className="text-zinc-300">Expires:</strong> {new Date(supp.expiration_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => {
                        setSelectedSupplement(supp);
                        setLogData({ dose_taken: supp.custom_dose.toString(), notes: '' });
                        setLogDialogOpen(true);
                      }}
                      className="flex-1 bg-violet-600 hover:bg-violet-700"
                      size="sm"
                      data-testid={`log-supplement-${supp.id}-button`}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Log
                    </Button>
                    <Button
                      onClick={() => deleteSupplement(supp.id)}
                      variant="outline"
                      className="border-zinc-700 hover:border-red-500 text-red-400"
                      size="sm"
                      data-testid={`delete-supplement-${supp.id}-button`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Recent Logs */}
            <div className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6">
              <h2 className="text-2xl font-cinzel font-semibold mb-6">RECENT LOGS</h2>
              {logs.length === 0 ? (
                <p className="text-zinc-400 text-center py-8">No logs yet</p>
              ) : (
                <div className="space-y-3">
                  {logs.slice(0, 10).map((log, index) => {
                    const supp = supplements.find(s => s.id === log.user_supplement_id);
                    return (
                      <div key={log.id} className="flex items-center justify-between p-3 bg-zinc-900/50 border border-zinc-800">
                        <div>
                          <p className="text-zinc-100 font-medium">{supp?.supplement_name || 'Unknown'}</p>
                          <p className="text-sm text-zinc-500">{log.dose_taken} {supp?.dose_unit}</p>
                        </div>
                        <p className="text-sm text-zinc-500">{new Date(log.taken_at).toLocaleString()}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Dialog open={logDialogOpen} onOpenChange={setLogDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800" data-testid="log-supplement-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-cinzel">LOG {selectedSupplement?.supplement_name.toUpperCase()}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Dose Taken ({selectedSupplement?.dose_unit})</Label>
              <Input
                type="number"
                value={logData.dose_taken}
                onChange={(e) => setLogData({...logData, dose_taken: e.target.value})}
                className="mt-2 bg-zinc-900 border-zinc-800"
                data-testid="log-dose-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Notes (Optional)</Label>
              <Input
                value={logData.notes}
                onChange={(e) => setLogData({...logData, notes: e.target.value})}
                className="mt-2 bg-zinc-900 border-zinc-800"
                placeholder="Any notes..."
                data-testid="log-notes-input"
              />
            </div>

            <Button
              onClick={logSupplement}
              className="w-full bg-violet-600 hover:bg-violet-700"
              data-testid="submit-log-button"
            >
              LOG SUPPLEMENT
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default MySupplements;