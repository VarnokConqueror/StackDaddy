import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Crown, Calendar, Pill, ShoppingCart, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function Dashboard({ user }) {
  const [mealPlans, setMealPlans] = useState([]);
  const [supplements, setSupplements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      try {
        const [plansRes, suppsRes] = await Promise.all([
          axios.get(`${API}/meal-plans`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/user-supplements`, { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setMealPlans(plansRes.data);
        setSupplements(suppsRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-obsidian" data-testid="dashboard-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-cinzel font-black uppercase mb-2 flex items-center gap-3">
            <Crown className="w-10 h-10 text-violet-500" />
            COMMAND CENTER
          </h1>
          <p className="text-zinc-400 text-lg">Welcome back, {user?.name}. Your nutrition empire awaits.</p>
        </motion.div>

        {/* Subscription Status */}
        {user?.subscription_status === 'inactive' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-6 mb-8"
            data-testid="subscription-prompt"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-cinzel font-bold mb-2 flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-violet-500" />
                  UNLOCK PREMIUM FEATURES
                </h3>
                <p className="text-zinc-300">Subscribe to access AI meal planning, unlimited supplement tracking, and more.</p>
              </div>
              <Link to="/subscription">
                <Button className="bg-neon-pink hover:bg-pink-600 text-white px-6 py-3 uppercase tracking-widest font-bold" data-testid="upgrade-button">
                  UPGRADE NOW
                </Button>
              </Link>
            </div>
          </motion.div>
        )}

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Meal Plans Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="md:col-span-7 bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-violet-500/30 transition-colors duration-300"
            data-testid="meal-plans-card"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-cinzel font-semibold flex items-center gap-2">
                <Calendar className="w-6 h-6 text-violet-500" />
                MEAL PLANS
              </h2>
              <Link to="/meal-planner">
                <Button variant="outline" className="border-zinc-700 hover:border-violet-500" data-testid="view-meal-plans-btn">
                  View All
                </Button>
              </Link>
            </div>
            {loading ? (
              <p className="text-zinc-400">Loading...</p>
            ) : mealPlans.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-zinc-400 mb-4">No meal plans yet. Create your first one!</p>
                <Link to="/meal-planner">
                  <Button className="bg-violet-600 hover:bg-violet-700" data-testid="create-meal-plan-btn">
                    CREATE MEAL PLAN
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {mealPlans.slice(0, 3).map((plan) => (
                  <div key={plan.id} className="bg-zinc-900/50 border border-zinc-800 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-zinc-100">{plan.plan_type.charAt(0).toUpperCase() + plan.plan_type.slice(1)} Plan</h3>
                        <p className="text-sm text-zinc-500">{new Date(plan.created_at).toLocaleDateString()}</p>
                      </div>
                      <Link to="/meal-planner">
                        <Button variant="ghost" size="sm" className="text-violet-500">View</Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Quick Actions Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="md:col-span-5 bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6"
          >
            <h2 className="text-2xl font-cinzel font-semibold mb-6">QUICK ACTIONS</h2>
            <div className="space-y-3">
              <Link to="/meal-planner" className="block">
                <Button className="w-full bg-violet-600 hover:bg-violet-700 justify-start" data-testid="quick-create-meal-plan">
                  <Calendar className="w-5 h-5 mr-2" />
                  New Meal Plan
                </Button>
              </Link>
              <Link to="/shopping-list" className="block">
                <Button className="w-full bg-zinc-800 hover:bg-zinc-700 justify-start" data-testid="quick-shopping-list">
                  <ShoppingCart className="w-5 h-5 mr-2" />
                  Shopping List
                </Button>
              </Link>
              <Link to="/my-supplements" className="block">
                <Button className="w-full bg-zinc-800 hover:bg-zinc-700 justify-start" data-testid="quick-track-supplement">
                  <Pill className="w-5 h-5 mr-2" />
                  Track Supplement
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Supplements Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="md:col-span-12 bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 hover:border-neon-pink/30 transition-colors duration-300"
            data-testid="supplements-card"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-cinzel font-semibold flex items-center gap-2">
                <Pill className="w-6 h-6 text-neon-pink" />
                MY SUPPLEMENTS
              </h2>
              <Link to="/my-supplements">
                <Button variant="outline" className="border-zinc-700 hover:border-neon-pink" data-testid="view-supplements-btn">
                  View All
                </Button>
              </Link>
            </div>
            {loading ? (
              <p className="text-zinc-400">Loading...</p>
            ) : supplements.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-zinc-400 mb-4">No supplements tracked yet. Add your first one!</p>
                <Link to="/supplements">
                  <Button className="bg-neon-pink hover:bg-pink-600" data-testid="add-supplement-btn">
                    ADD SUPPLEMENT
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {supplements.slice(0, 6).map((supp) => (
                  <div key={supp.id} className="bg-zinc-900/50 border border-zinc-800 p-4">
                    <h3 className="font-semibold text-zinc-100 mb-2">{supp.supplement_name}</h3>
                    <p className="text-sm text-zinc-400">{supp.custom_dose} {supp.dose_unit}</p>
                    <p className="text-xs text-zinc-500">{supp.frequency}</p>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;