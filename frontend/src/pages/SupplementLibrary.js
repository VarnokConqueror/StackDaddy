import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Pill, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SupplementLibrary({ user }) {
  const [supplements, setSupplements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [selectedSupplement, setSelectedSupplement] = useState(null);
  
  const [formData, setFormData] = useState({
    custom_dose: '',
    dose_unit: 'mg',
    frequency: 'daily',
    timing: [],
    stock_quantity: 30,
    reminder_enabled: true
  });

  useEffect(() => {
    fetchSupplements();
  }, []);

  const fetchSupplements = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/supplements`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSupplements(response.data);
    } catch (error) {
      toast.error('Failed to load supplements');
    } finally {
      setLoading(false);
    }
  };

  const addToMySupplements = async () => {
    if (!selectedSupplement || !formData.custom_dose) {
      toast.error('Please fill in all required fields');
      return;
    }

    setAdding(true);
    const token = localStorage.getItem('token');
    
    try {
      await axios.post(`${API}/user-supplements`, {
        supplement_id: selectedSupplement.id,
        custom_dose: parseFloat(formData.custom_dose),
        dose_unit: formData.dose_unit,
        frequency: formData.frequency,
        timing: formData.timing,
        stock_quantity: parseInt(formData.stock_quantity),
        reminder_enabled: formData.reminder_enabled
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Supplement added to your inventory!');
      setDialogOpen(false);
      setSelectedSupplement(null);
      setFormData({
        custom_dose: '',
        dose_unit: 'mg',
        frequency: 'daily',
        timing: [],
        stock_quantity: 30,
        reminder_enabled: true
      });
    } catch (error) {
      toast.error('Failed to add supplement');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="supplement-library-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2">SUPPLEMENT LIBRARY</h1>
          <p className="text-zinc-400">Browse and add supplements to your inventory</p>
        </motion.div>

        {loading ? (
          <div className="text-center py-12 text-zinc-400">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {supplements.map((supp, index) => (
              <motion.div
                key={supp.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-neon-pink/30 transition-colors duration-300"
                data-testid={`supplement-${supp.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-cinzel font-semibold mb-2">{supp.name}</h3>
                    <p className="text-sm text-zinc-400">{supp.purpose}</p>
                  </div>
                  <Pill className="w-8 h-8 text-neon-pink" />
                </div>

                {supp.typical_dose_min && (
                  <div className="mb-3 text-sm">
                    <p className="text-zinc-500">Typical Dose: {supp.typical_dose_min}-{supp.typical_dose_max} {supp.dose_unit}</p>
                  </div>
                )}

                {supp.warnings && (
                  <div className="mb-3">
                    <p className="text-xs text-amber-500/80">⚠️ {supp.warnings}</p>
                  </div>
                )}

                <Button
                  onClick={() => {
                    setSelectedSupplement(supp);
                    setDialogOpen(true);
                  }}
                  className="w-full bg-neon-pink hover:bg-pink-600 mt-4"
                  data-testid={`add-supplement-${supp.id}-button`}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  ADD TO MY SUPPLEMENTS
                </Button>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800" data-testid="add-supplement-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-cinzel">ADD {selectedSupplement?.name.toUpperCase()}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Your Dose</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  type="number"
                  value={formData.custom_dose}
                  onChange={(e) => setFormData({...formData, custom_dose: e.target.value})}
                  className="flex-1 bg-zinc-900 border-zinc-800"
                  data-testid="dose-input"
                />
                <Input
                  value={formData.dose_unit}
                  onChange={(e) => setFormData({...formData, dose_unit: e.target.value})}
                  className="w-20 bg-zinc-900 border-zinc-800"
                  data-testid="dose-unit-input"
                />
              </div>
            </div>

            <div>
              <Label className="text-zinc-300">Frequency</Label>
              <Input
                value={formData.frequency}
                onChange={(e) => setFormData({...formData, frequency: e.target.value})}
                className="mt-2 bg-zinc-900 border-zinc-800"
                placeholder="e.g., daily, twice daily"
                data-testid="frequency-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Stock Quantity</Label>
              <Input
                type="number"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({...formData, stock_quantity: e.target.value})}
                className="mt-2 bg-zinc-900 border-zinc-800"
                data-testid="stock-input"
              />
            </div>

            <Button
              onClick={addToMySupplements}
              disabled={adding}
              className="w-full bg-neon-pink hover:bg-pink-600"
              data-testid="submit-add-supplement-button"
            >
              {adding ? 'ADDING...' : 'ADD TO INVENTORY'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default SupplementLibrary;