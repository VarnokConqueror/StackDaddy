import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar, Plus, Sparkles, Eye, Target } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DIETARY_OPTIONS = ['Meat Eating', 'Poultry Only', 'Fish Only', 'Vegetarian', 'Vegan'];
const COOKING_METHODS = ['Air Fryer', 'Microwave', 'Stovetop', 'Toaster', 'Instant Pot'];
const HEALTH_GOALS = [
  { value: 'lose_weight', label: 'Lose Weight' },
  { value: 'gain_weight', label: 'Gain Weight' },
  { value: 'gain_muscle', label: 'Gain Muscle' },
  { value: 'eat_healthy', label: 'Eat Healthy' },
  { value: 'increase_energy', label: 'Increase Energy' },
  { value: 'improve_digestion', label: 'Improve Digestion' }
];

function MealPlanner({ user }) {
  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  
  const [goal, setGoal] = useState(user?.health_goal || '');
  const [selectedDietary, setSelectedDietary] = useState(user?.dietary_preferences || []);
  const [selectedCooking, setSelectedCooking] = useState(user?.cooking_methods || []);
  const [useAI, setUseAI] = useState(false);

  useEffect(() => {
    fetchMealPlans();
  }, []);

  useEffect(() => {
    // Auto-populate from user profile
    if (user) {
      setSelectedDietary(user.dietary_preferences || []);
      setSelectedCooking(user.cooking_methods || []);
      setGoal(user.health_goal || '');
    }
  }, [user]);

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
        plan_type: 'weekly',
        goal: goal || null,
        dietary_preferences: selectedDietary,
        cooking_methods: selectedCooking,
        generate_with_ai: useAI
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Weekly meal plan created!');
      setDialogOpen(false);
      fetchMealPlans();
    } catch (error) {
      toast.error('Failed to create meal plan');
    } finally {
      setCreating(false);
    }
  };

  const viewPlan = (plan) => {
    setSelectedPlan(plan);
    setViewDialogOpen(true);
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
                NEW WEEKLY PLAN
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-950 border-zinc-800 max-w-2xl" data-testid="create-meal-plan-dialog">
              <DialogHeader>
                <DialogTitle className="text-2xl font-cinzel">CREATE WEEKLY MEAL PLAN</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 mt-4 max-h-[70vh] overflow-y-auto pr-2">
                <div>
                  <label className="text-zinc-300 mb-2 block flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Health Goal
                  </label>
                  <Select value={goal} onValueChange={setGoal}>
                    <SelectTrigger className="bg-zinc-900 border-zinc-800" data-testid="goal-select">
                      <SelectValue placeholder="Select your goal" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      {HEALTH_GOALS.map((g) => (
                        <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-zinc-500 mt-1">AI will optimize meals for your goal</p>
                </div>

                <div>
                  <label className="text-zinc-300 mb-2 block">Dietary Preferences {selectedDietary.length > 0 && <span className="text-xs text-violet-400">(from profile)</span>}</label>
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
                  <label className="text-zinc-300 mb-2 block">Cooking Methods {selectedCooking.length > 0 && <span className="text-xs text-violet-400">(from profile)</span>}</label>
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

                <div className="flex items-center space-x-2 p-4 bg-gradient-to-r from-violet-600/10 to-pink-600/10 border border-violet-500/30">
                  <Checkbox
                    id="useAI"
                    checked={useAI}
                    onCheckedChange={setUseAI}
                    data-testid="use-ai-checkbox"
                  />
                  <label htmlFor="useAI" className="text-zinc-300 cursor-pointer flex items-center gap-2">
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
                  {creating ? 'CREATING...' : 'CREATE WEEKLY PLAN'}
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
            <p className="text-zinc-500 mb-6">Create your first weekly meal plan to start conquering your nutrition</p>
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
                    Weekly Plan
                  </h3>
                  <span className="text-sm text-zinc-500">
                    {new Date(plan.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm mb-4">
                  {plan.goal && (
                    <p className="text-zinc-400">
                      <strong className="text-violet-400">Goal:</strong>{' '}
                      {HEALTH_GOALS.find(g => g.value === plan.goal)?.label || plan.goal}
                    </p>
                  )}
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

                <div className="flex gap-2">
                  <Button 
                    onClick={() => viewPlan(plan)}
                    className="flex-1 bg-violet-600 hover:bg-violet-700" 
                    size="sm"
                    data-testid={`view-plan-${plan.id}`}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Plan
                  </Button>
                </div>
              </motion.div>
            ))}</div>
        )}
      </div>

      {/* View Plan Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 max-w-4xl" data-testid="view-plan-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-cinzel">WEEKLY MEAL PLAN</DialogTitle>
          </DialogHeader>
          
          {selectedPlan && (
            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-2">
              {selectedPlan.goal && (
                <div className="mb-4 p-4 bg-violet-600/20 border border-violet-500/30">
                  <p className="text-violet-300 font-semibold">
                    Goal: {HEALTH_GOALS.find(g => g.value === selectedPlan.goal)?.label || selectedPlan.goal}
                  </p>
                </div>
              )}
              
              <div className="space-y-4">
                {selectedPlan.days.map((day, idx) => (
                  <div key={idx} className="bg-zinc-900/50 border border-zinc-800 p-4">
                    <h3 className="text-lg font-cinzel font-semibold mb-3 text-violet-400">{day.day}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-zinc-500 font-semibold">Breakfast:</p>
                        <p className="text-zinc-300">{day.meals.breakfast || 'Not assigned'}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500 font-semibold">Lunch:</p>
                        <p className="text-zinc-300">{day.meals.lunch || 'Not assigned'}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500 font-semibold">Dinner:</p>
                        <p className="text-zinc-300">{day.meals.dinner || 'Not assigned'}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500 font-semibold">Snack:</p>
                        <p className="text-zinc-300">{day.meals.snack || 'Not assigned'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default MealPlanner;
