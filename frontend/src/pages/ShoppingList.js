import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { ShoppingCart, Check, Trash2, RefreshCw, Calendar, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Category order for display
const CATEGORY_ORDER = [
  'Produce',
  'Proteins', 
  'Dairy',
  'Grains & Bread',
  'Pantry',
  'Nuts & Seeds',
  'Other'
];

// Capitalize first letter of each word
const capitalize = (str) => {
  if (!str) return '';
  return str.split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ');
};

function ShoppingList({ user }) {
  const [mealPlans, setMealPlans] = useState([]);
  const [shoppingLists, setShoppingLists] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [checkedItems, setCheckedItems] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [listToDelete, setListToDelete] = useState(null);
  const [expandedList, setExpandedList] = useState(null);

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
      
      // Auto-expand the first list if there's only one
      if (listsRes.data.length === 1) {
        setExpandedList(listsRes.data[0].id);
      }
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

    // Check if plan has recipes
    const plan = mealPlans.find(p => p.id === selectedPlan);
    const hasRecipes = plan?.days?.some(day => 
      day.recipes && Object.keys(day.recipes).length > 0
    );
    
    if (!hasRecipes) {
      toast.error('This meal plan has no recipes. Generate meals with AI first!');
      return;
    }

    setGenerating(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(`${API}/shopping-lists?meal_plan_id=${selectedPlan}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Shopping list generated!');
      setSelectedPlan('');
      setExpandedList(response.data.id); // Auto-expand the new list
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate shopping list');
    } finally {
      setGenerating(false);
    }
  };

  const deleteList = async () => {
    if (!listToDelete) return;
    
    const token = localStorage.getItem('token');
    try {
      await axios.delete(`${API}/shopping-lists/${listToDelete}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Shopping list deleted');
      setDeleteDialogOpen(false);
      setListToDelete(null);
      if (expandedList === listToDelete) {
        setExpandedList(null);
      }
      fetchData();
    } catch (error) {
      toast.error('Failed to delete shopping list');
    }
  };

  const toggleItem = (listId, itemIndex) => {
    const key = `${listId}-${itemIndex}`;
    setCheckedItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const getCheckedCount = (listId, items) => {
    return items.filter((_, idx) => checkedItems[`${listId}-${idx}`]).length;
  };

  const toggleExpand = (listId) => {
    setExpandedList(expandedList === listId ? null : listId);
  };

  const groupByCategory = (items) => {
    const grouped = {};
    items.forEach((item, idx) => {
      const category = item.category || 'Other';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push({ ...item, originalIndex: idx });
    });
    
    // Sort by category order
    const sortedGrouped = {};
    CATEGORY_ORDER.forEach(cat => {
      if (grouped[cat]) {
        sortedGrouped[cat] = grouped[cat];
      }
    });
    // Add any remaining categories
    Object.keys(grouped).forEach(cat => {
      if (!sortedGrouped[cat]) {
        sortedGrouped[cat] = grouped[cat];
      }
    });
    
    return sortedGrouped;
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
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2">ROYAL PROVISIONS</h1>
          <p className="text-zinc-400 italic">The sacred scrolls of ingredients for your conquests in the kitchen</p>
        </motion.div>

        {/* Generate New List Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-8"
        >
          <h2 className="text-xl font-cinzel font-semibold mb-4 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-violet-500" />
            SUMMON NEW PROVISIONS
          </h2>
          <p className="text-zinc-500 text-sm mb-4 italic">
            Select a meal plan blessed with recipes to conjure your shopping scroll
          </p>
          <div className="flex gap-4">
            <Select value={selectedPlan} onValueChange={setSelectedPlan}>
              <SelectTrigger className="flex-1 bg-zinc-900 border-zinc-800" data-testid="select-meal-plan">
                <SelectValue placeholder="Select a meal plan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {mealPlans.map((plan) => {
                  const hasRecipes = plan.days?.some(day => 
                    day.recipes && Object.keys(day.recipes).length > 0
                  );
                  return (
                    <SelectItem key={plan.id} value={plan.id}>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Week of {new Date(plan.created_at).toLocaleDateString()}</span>
                        {hasRecipes ? (
                          <span className="text-xs bg-green-600/20 text-green-400 px-2 py-0.5 rounded">Has Recipes</span>
                        ) : (
                          <span className="text-xs bg-zinc-700 text-zinc-400 px-2 py-0.5 rounded">No Recipes</span>
                        )}
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            <Button
              onClick={generateList}
              disabled={generating || !selectedPlan}
              className="bg-violet-600 hover:bg-violet-700 min-w-[160px]"
              data-testid="generate-shopping-list-button"
            >
              {generating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  CONJURING...
                </>
              ) : (
                'SUMMON LIST'
              )}
            </Button>
          </div>
        </motion.div>

        {/* Shopping Lists */}
        {loading ? (
          <div className="text-center py-12 text-zinc-400 italic">Consulting the royal scrolls...</div>
        ) : shoppingLists.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-24"
          >
            <ShoppingCart className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold text-zinc-400 mb-2">NO SCROLLS YET</h2>
            <p className="text-zinc-500 mb-6 italic">Your provision scrolls await their first summoning</p>
            <p className="text-zinc-600 text-sm max-w-md mx-auto">
              First, forge a meal plan blessed with AI-generated recipes. Then return to summon your shopping scroll with precise quantities!
            </p>
          </motion.div>
        ) : (
          <div className="space-y-4">
            {shoppingLists.map((list, index) => {
              const groupedItems = groupByCategory(list.items);
              const checkedCount = getCheckedCount(list.id, list.items);
              const progress = list.items.length > 0 ? (checkedCount / list.items.length) * 100 : 0;
              const isExpanded = expandedList === list.id;
              
              return (
                <motion.div
                  key={list.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 overflow-hidden"
                  data-testid={`shopping-list-${list.id}`}
                >
                  {/* Clickable Header */}
                  <div 
                    onClick={() => toggleExpand(list.id)}
                    className="p-6 cursor-pointer hover:bg-zinc-900/30 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div>
                          <h3 className="text-xl font-cinzel font-semibold flex items-center gap-2">
                            <ShoppingCart className="w-5 h-5 text-violet-500" />
                            Shopping List
                          </h3>
                          <p className="text-sm text-zinc-500 mt-1">
                            Created {new Date(list.created_at).toLocaleDateString()} • {list.items.length} Items
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setListToDelete(list.id);
                            setDeleteDialogOpen(true);
                          }}
                          className="text-zinc-600 hover:text-red-400 transition-colors p-2"
                          title="Delete shopping list"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                        {isExpanded ? (
                          <ChevronUp className="w-6 h-6 text-violet-400" />
                        ) : (
                          <ChevronDown className="w-6 h-6 text-zinc-500" />
                        )}
                      </div>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="flex items-center gap-4">
                      <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-violet-600 to-pink-600 transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-zinc-400 min-w-[80px] text-right">
                        {checkedCount} / {list.items.length}
                      </span>
                    </div>
                  </div>

                  {/* Expandable Content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6 border-t border-zinc-800">
                          {list.items.length === 0 ? (
                            <p className="text-zinc-500 text-center py-8 italic">
                              This scroll is empty. Ensure your meal plan bears AI-blessed recipes!
                            </p>
                          ) : (
                            <div className="space-y-6 pt-6">
                              {Object.entries(groupedItems).map(([category, items]) => (
                                <div key={category}>
                                  <h4 className="text-lg font-semibold text-violet-400 mb-3 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-2 h-2 bg-violet-500 rounded-full"></span>
                                    {category}
                                    <span className="text-xs text-zinc-500 font-normal lowercase">
                                      ({items.length} items)
                                    </span>
                                  </h4>
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {items.map((item) => {
                                      const checkKey = `${list.id}-${item.originalIndex}`;
                                      const isChecked = checkedItems[checkKey] || false;
                                      
                                      return (
                                        <div 
                                          key={item.originalIndex}
                                          onClick={() => toggleItem(list.id, item.originalIndex)}
                                          className={`flex items-center space-x-3 p-4 bg-zinc-900/50 border cursor-pointer transition-all duration-200 hover:bg-zinc-800/50 ${
                                            isChecked ? 'border-green-500/50 bg-green-900/10' : 'border-zinc-800'
                                          }`}
                                        >
                                          <Checkbox 
                                            checked={isChecked}
                                            onCheckedChange={() => toggleItem(list.id, item.originalIndex)}
                                            className={isChecked ? 'border-green-500 data-[state=checked]:bg-green-600' : ''}
                                            data-testid={`item-checkbox-${item.originalIndex}`}
                                          />
                                          <div className="flex-1 min-w-0">
                                            <p className={`text-zinc-100 font-medium truncate ${isChecked ? 'line-through text-zinc-500' : ''}`}>
                                              {capitalize(item.name)}
                                            </p>
                                            <p className={`text-sm ${isChecked ? 'text-zinc-600' : 'text-violet-400'}`}>
                                              {item.quantity} {item.unit}
                                            </p>
                                          </div>
                                          {isChecked && (
                                            <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-cinzel text-red-400">
              BURN THIS SCROLL?
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <p className="text-zinc-400 mb-6 italic">
              This provision list shall be cast into the flames, never to return. This decree cannot be undone.
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
                onClick={deleteList}
                className="flex-1 bg-red-600 hover:bg-red-700"
                data-testid="confirm-delete-list-btn"
              >
                BURN IT
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ShoppingList;
