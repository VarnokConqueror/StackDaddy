import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { ShoppingCart, Download } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function ShoppingList({ user }) {
  const [mealPlans, setMealPlans] = useState([]);
  const [shoppingLists, setShoppingLists] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem('token');
    try {
      const [plansRes, listsRes] = await Promise.all([
        axios.get(`${API}/meal-plans`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/shopping-lists`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setMealPlans(plansRes.data);
      setShoppingLists(listsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const generateList = async () => {
    if (!selectedPlan) {
      toast.error('Please select a meal plan');
      return;
    }

    setGenerating(true);
    const token = localStorage.getItem('token');
    
    try {
      await axios.post(`${API}/shopping-lists?meal_plan_id=${selectedPlan}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Shopping list generated!');
      fetchData();
    } catch (error) {
      toast.error('Failed to generate shopping list');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="shopping-list-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2">SHOPPING LIST</h1>
          <p className="text-zinc-400">Generate shopping lists from your meal plans</p>
        </motion.div>

        <div className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-6">
          <h2 className="text-xl font-cinzel font-semibold mb-4">GENERATE NEW LIST</h2>
          <div className="flex gap-4">
            <Select value={selectedPlan} onValueChange={setSelectedPlan}>
              <SelectTrigger className="flex-1 bg-zinc-900 border-zinc-800" data-testid="select-meal-plan">
                <SelectValue placeholder="Select a meal plan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {mealPlans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>
                    {plan.plan_type.charAt(0).toUpperCase() + plan.plan_type.slice(1)} Plan - {new Date(plan.created_at).toLocaleDateString()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={generateList}
              disabled={generating || !selectedPlan}
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="generate-shopping-list-button"
            >
              {generating ? 'GENERATING...' : 'GENERATE'}
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-zinc-400">Loading...</div>
        ) : shoppingLists.length === 0 ? (
          <div className="text-center py-24">
            <ShoppingCart className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold text-zinc-400 mb-2">NO SHOPPING LISTS YET</h2>
            <p className="text-zinc-500">Generate your first shopping list from a meal plan</p>
          </div>
        ) : (
          <div className="space-y-6">
            {shoppingLists.map((list, index) => (
              <motion.div
                key={list.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6"
                data-testid={`shopping-list-${list.id}`}
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-xl font-cinzel font-semibold">Shopping List</h3>
                    <p className="text-sm text-zinc-500">{new Date(list.created_at).toLocaleDateString()}</p>
                  </div>
                  <Button variant="outline" className="border-zinc-700 hover:border-violet-500">
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {list.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="flex items-center space-x-3 p-3 bg-zinc-900/50 border border-zinc-800">
                      <Checkbox data-testid={`item-checkbox-${itemIndex}`} />
                      <div className="flex-1">
                        <p className="text-zinc-100 font-medium">{item.name}</p>
                        <p className="text-sm text-zinc-500">{item.quantity} {item.unit}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ShoppingList;