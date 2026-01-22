import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar, Plus, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DIETARY_OPTIONS = ['Meat Eating', 'Poultry Only', 'Fish Only', 'Vegetarian', 'Vegan'];
const COOKING_METHODS = ['Air Fryer', 'Microwave', 'Stovetop', 'Toaster', 'Instant Pot'];

function MealPlanner({ user }) {
  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  const [planType, setPlanType] = useState('weekly');
  const [selectedDietary, setSelectedDietary] = useState([]);
  const [selectedCooking, setSelectedCooking] = useState([]);
  const [useAI, setUseAI] = useState(false);

  useEffect(() => {
    fetchMealPlans();
  }, []);

  const fetchMealPlans = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/meal-plans`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMealPlans(response.data);
    } catch (error) {
      toast.error('Failed to load meal plans');
    } finally {
      setLoading(false);
    }
  };

  const createMealPlan = async () => {
    setCreating(true);
    const token = localStorage.getItem('token');
    
    try {
      await axios.post(`${API}/meal-plans`, {
        plan_type: planType,
        dietary_preferences: selectedDietary,
        cooking_methods: selectedCooking,
        generate_with_ai: useAI
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Meal plan created!');
      setDialogOpen(false);
      fetchMealPlans();
    } catch (error) {
      toast.error('Failed to create meal plan');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="meal-planner-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-between mb-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <h1 className="text-4xl font-cinzel font-black uppercase mb-2">MEAL PLANNER</h1>
            <p className="text-zinc-400">Command your nutrition strategy</p>
          </motion.div>
          
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-violet-600 hover:bg-violet-700" data-testid="create-meal-plan-button">
                <Plus className="w-5 h-5 mr-2" />
                NEW PLAN
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-950 border-zinc-800" data-testid="create-meal-plan-dialog">
              <DialogHeader>
                <DialogTitle className="text-2xl font-cinzel">CREATE MEAL PLAN</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 mt-4">
                <div>
                  <label className="text-zinc-300 mb-2 block">Plan Type</label>
                  <Select value={planType} onValueChange={setPlanType}>
                    <SelectTrigger className="bg-zinc-900 border-zinc-800" data-testid="plan-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-zinc-300 mb-2 block">Dietary Preferences</label>
                  <div className="space-y-2">
                    {DIETARY_OPTIONS.map((option) => (
                      <div key={option} className="flex items-center space-x-2">
                        <Checkbox
                          id={option}
                          checked={selectedDietary.includes(option)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedDietary([...selectedDietary, option]);
                            } else {
                              setSelectedDietary(selectedDietary.filter(d => d !== option));
                            }
                          }}
                          data-testid={`dietary-${option.toLowerCase().replace(' ', '-')}`}
                        />
                        <label htmlFor={option} className="text-zinc-400 cursor-pointer">{option}</label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-zinc-300 mb-2 block">Cooking Methods</label>
                  <div className="space-y-2">
                    {COOKING_METHODS.map((method) => (
                      <div key={method} className="flex items-center space-x-2">
                        <Checkbox
                          id={method}
                          checked={selectedCooking.includes(method)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedCooking([...selectedCooking, method]);
                            } else {
                              setSelectedCooking(selectedCooking.filter(m => m !== method));
                            }
                          }}
                          data-testid={`cooking-${method.toLowerCase().replace(' ', '-')}`}
                        />
                        <label htmlFor={method} className="text-zinc-400 cursor-pointer">{method}</label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="useAI"
                    checked={useAI}
                    onCheckedChange={setUseAI}
                    data-testid="use-ai-checkbox"
                  />
                  <label htmlFor="useAI" className="text-zinc-400 cursor-pointer flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-violet-500" />
                    Generate with AI (requires API key in Profile)
                  </label>
                </div>

                <Button
                  onClick={createMealPlan}
                  disabled={creating}
                  className="w-full bg-violet-600 hover:bg-violet-700"
                  data-testid="submit-meal-plan-button"
                >
                  {creating ? 'CREATING...' : 'CREATE PLAN'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="text-center py-12 text-zinc-400">Loading...</div>
        ) : mealPlans.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-24"
          >
            <Calendar className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold text-zinc-400 mb-2">NO MEAL PLANS YET</h2>
            <p className="text-zinc-500 mb-6">Create your first meal plan to start conquering your nutrition</p>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {mealPlans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-violet-500/30 transition-colors duration-300"
                data-testid={`meal-plan-${plan.id}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-cinzel font-semibold">
                    {plan.plan_type.charAt(0).toUpperCase() + plan.plan_type.slice(1)} Plan
                  </h3>
                  <span className="text-sm text-zinc-500">
                    {new Date(plan.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <p className="text-zinc-400">
                    <strong className="text-zinc-300">Dietary:</strong>{' '}
                    {plan.dietary_preferences.join(', ') || 'None'}
                  </p>
                  <p className="text-zinc-400">
                    <strong className="text-zinc-300">Cooking:</strong>{' '}
                    {plan.cooking_methods.join(', ') || 'None'}
                  </p>
                  <p className="text-zinc-400">
                    <strong className="text-zinc-300">Days:</strong> {plan.days.length}
                  </p>
                </div>

                <div className="mt-4 flex gap-2">
                  <Button variant="outline" className="flex-1 border-zinc-700 hover:border-violet-500" size="sm">
                    View Plan
                  </Button>
                  <Button variant="outline" className="flex-1 border-zinc-700 hover:border-neon-pink" size="sm">
                    Edit
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default MealPlanner;