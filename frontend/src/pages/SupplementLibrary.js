import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Pill, Plus, Sparkles, Target } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HEALTH_GOALS_SUPPS = [
  { value: 'lose_weight', label: 'Lose Weight' },
  { value: 'gain_weight', label: 'Gain Weight' },
  { value: 'gain_muscle', label: 'Gain Muscle' },
  { value: 'eat_healthy', label: 'Eat Healthy' },
  { value: 'increase_energy', label: 'Increase Energy' },
  { value: 'improve_digestion', label: 'Improve Digestion' },
  { value: 'better_sleep', label: 'Better Sleep' },
  { value: 'reduce_stress', label: 'Reduce Stress' },
  { value: 'boost_immunity', label: 'Boost Immunity' },
  { value: 'joint_health', label: 'Joint Health' }
];

function SupplementLibrary({ user }) {
  const [supplements, setSupplements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [gettingRecommendations, setGettingRecommendations] = useState(false);
  const [selectedSupplement, setSelectedSupplement] = useState(null);
  const [selectedGoal, setSelectedGoal] = useState(user?.health_goal || '');
  const [aiRecommendations, setAiRecommendations] = useState(null);
  
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

  useEffect(() => {
    if (user?.health_goal) {
      setSelectedGoal(user.health_goal);
    }
  }, [user]);

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

  const getAIRecommendations = async () => {
    if (!selectedGoal) {
      toast.error('Please select a health goal');
      return;
    }

    setGettingRecommendations(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(`${API}/supplements/ai-recommend`,
        { goal: selectedGoal },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      setAiRecommendations(response.data);
      toast.success('AI recommendations generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to get recommendations. Make sure AI is configured in Profile.');
    } finally {
      setGettingRecommendations(false);
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

        {/* AI Recommendations Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-6 mb-8"
        >
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-6 h-6 text-violet-500" />
            <h2 className="text-xl font-cinzel font-semibold">AI-POWERED RECOMMENDATIONS</h2>
          </div>
          <p className="text-zinc-300 text-sm mb-4">
            Get personalized supplement recommendations based on your health goals
          </p>
          <div className="flex gap-3">
            <Select value={selectedGoal} onValueChange={setSelectedGoal}>
              <SelectTrigger className="flex-1 bg-zinc-900 border-zinc-800 max-w-md" data-testid="ai-goal-select">
                <SelectValue placeholder="Select your health goal" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {HEALTH_GOALS_SUPPS.map((g) => (
                  <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={getAIRecommendations}
              disabled={gettingRecommendations || !selectedGoal}
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="get-ai-recommendations-button"
            >
              {gettingRecommendations ? 'ANALYZING...' : 'GET RECOMMENDATIONS'}
            </Button>
            {aiRecommendations && (
              <Button
                onClick={() => setAiDialogOpen(true)}
                variant="outline"
                className="border-violet-500 text-violet-400"
                data-testid="view-recommendations-button"
              >
                <Target className="w-4 h-4 mr-2" />
                View Results
              </Button>
            )}
          </div>
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
                transition={{ delay: index * 0.05 }}
                className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-neon-pink/30 transition-colors duration-300"
                data-testid={`supplement-${supp.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-cinzel font-semibold mb-2">{supp.name}</h3>
                    <p className="text-sm text-zinc-400">{supp.purpose}</p>
                  </div>
                  <Pill className="w-8 h-8 text-neon-pink flex-shrink-0" />
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
                    setFormData({
                      ...formData,
                      custom_dose: supp.typical_dose_min?.toString() || '',
                      dose_unit: supp.dose_unit || 'mg'
                    });
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

      {/* Add Supplement Dialog */}
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

      {/* AI Recommendations Dialog */}
      <Dialog open={aiDialogOpen} onOpenChange={setAiDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 max-w-3xl" data-testid="ai-recommendations-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-cinzel flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-violet-500" />
              AI RECOMMENDATIONS
            </DialogTitle>
          </DialogHeader>
          
          {aiRecommendations && (
            <div className="mt-4 max-h-[60vh] overflow-y-auto pr-2">
              <div className="mb-4 p-4 bg-violet-600/20 border border-violet-500/30">
                <p className="text-violet-300">
                  Goal: <strong>{HEALTH_GOALS_SUPPS.find(g => g.value === aiRecommendations.goal)?.label}</strong>
                </p>
              </div>
              
              <div className="text-zinc-300 whitespace-pre-wrap">
                {typeof aiRecommendations.recommendations === 'string' 
                  ? aiRecommendations.recommendations
                  : JSON.stringify(aiRecommendations.recommendations, null, 2)}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default SupplementLibrary;

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