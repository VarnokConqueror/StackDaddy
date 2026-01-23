import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Package, Plus, Trash2, Edit, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PANTRY_CATEGORIES = [
  'Spices',
  'Oils & Vinegars', 
  'Grains & Pasta',
  'Canned Goods',
  'Condiments',
  'Baking',
  'Other'
];

const COMMON_UNITS = ['tsp', 'tbsp', 'cup', 'oz', 'lb', 'g', 'kg', 'ml', 'l', 'bottle', 'can', 'jar', 'package'];

function Pantry({ user }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  
  // Form state
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('');
  const [category, setCategory] = useState('');
  const [lowStockThreshold, setLowStockThreshold] = useState('');

  useEffect(() => {
    fetchPantry();
  }, []);

  const fetchPantry = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/pantry`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load pantry');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName('');
    setQuantity('');
    setUnit('');
    setCategory('');
    setLowStockThreshold('');
    setEditingItem(null);
  };

  const openAddDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setName(item.name);
    setQuantity(item.quantity.toString());
    setUnit(item.unit);
    setCategory(item.category);
    setLowStockThreshold(item.low_stock_threshold?.toString() || '');
    setDialogOpen(true);
  };

  const saveItem = async () => {
    if (!name || !quantity || !unit || !category) {
      toast.error('Please fill all required fields');
      return;
    }

    const token = localStorage.getItem('token');
    const itemData = {
      name,
      quantity: parseFloat(quantity),
      unit,
      category,
      low_stock_threshold: lowStockThreshold ? parseFloat(lowStockThreshold) : null
    };

    try {
      if (editingItem) {
        await axios.put(`${API}/pantry/${editingItem.id}`, itemData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Pantry item updated');
      } else {
        await axios.post(`${API}/pantry`, itemData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Item added to pantry');
      }
      setDialogOpen(false);
      resetForm();
      fetchPantry();
    } catch (error) {
      toast.error('Failed to save item');
    }
  };

  const deleteItem = async () => {
    if (!itemToDelete) return;
    
    const token = localStorage.getItem('token');
    try {
      await axios.delete(`${API}/pantry/${itemToDelete}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Item removed from pantry');
      setDeleteDialogOpen(false);
      setItemToDelete(null);
      fetchPantry();
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const groupByCategory = (items) => {
    const grouped = {};
    items.forEach(item => {
      if (!grouped[item.category]) {
        grouped[item.category] = [];
      }
      grouped[item.category].push(item);
    });
    return grouped;
  };

  const isLowStock = (item) => {
    return item.low_stock_threshold && item.quantity <= item.low_stock_threshold;
  };

  const groupedItems = groupByCategory(items);

  return (
    <div className="min-h-screen bg-obsidian" data-testid="pantry-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-cinzel font-black uppercase mb-2">ROYAL PANTRY</h1>
            <p className="text-zinc-400 italic">Your kingdom's stores - spices, oils, and sacred provisions</p>
          </div>
          <Button
            onClick={openAddDialog}
            className="bg-violet-600 hover:bg-violet-700"
            data-testid="add-pantry-item-button"
          >
            <Plus className="w-4 h-4 mr-2" />
            ADD PROVISION
          </Button>
        </motion.div>

        {/* Low Stock Alerts */}
        {items.filter(isLowStock).length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-amber-600/10 border border-amber-500/30 p-4 mb-8"
          >
            <h3 className="text-amber-400 font-semibold flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5" />
              PROVISIONS RUNNING LOW
            </h3>
            <p className="text-zinc-500 text-sm mb-2 italic">The Court advises restocking these items:</p>
            <div className="flex flex-wrap gap-2">
              {items.filter(isLowStock).map(item => (
                <span key={item.id} className="bg-amber-600/20 text-amber-300 px-3 py-1 rounded text-sm">
                  {item.name} ({item.quantity} {item.unit} remaining)
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {loading ? (
          <div className="text-center py-12 text-zinc-400 italic">Consulting the royal inventory...</div>
        ) : items.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-24"
          >
            <Package className="w-20 h-20 text-zinc-700 mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold text-zinc-400 mb-2">THE STORES ARE BARE</h2>
            <p className="text-zinc-500 mb-6 italic">Your royal pantry awaits its first provisions</p>
            <Button onClick={openAddDialog} className="bg-violet-600 hover:bg-violet-700">
              <Plus className="w-4 h-4 mr-2" />
              STOCK THE PANTRY
            </Button>
          </motion.div>
        ) : (
          <div className="space-y-8">
            {PANTRY_CATEGORIES.map(category => {
              const categoryItems = groupedItems[category];
              if (!categoryItems || categoryItems.length === 0) return null;
              
              return (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6"
                >
                  <h2 className="text-xl font-cinzel font-semibold mb-4 text-violet-400 flex items-center gap-2">
                    <span className="w-2 h-2 bg-violet-500 rounded-full"></span>
                    {category}
                    <span className="text-sm text-zinc-500 font-normal">({categoryItems.length})</span>
                  </h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryItems.map(item => (
                      <div
                        key={item.id}
                        className={`bg-zinc-900/50 border p-4 relative ${
                          isLowStock(item) ? 'border-amber-500/50' : 'border-zinc-800'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-zinc-100">{item.name}</h3>
                            <p className={`text-lg ${isLowStock(item) ? 'text-amber-400' : 'text-violet-400'}`}>
                              {item.quantity} {item.unit}
                            </p>
                            {item.low_stock_threshold && (
                              <p className="text-xs text-zinc-500 mt-1">
                                Low stock alert at: {item.low_stock_threshold} {item.unit}
                              </p>
                            )}
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => openEditDialog(item)}
                              className="text-zinc-500 hover:text-violet-400 p-1 transition-colors"
                              title="Edit"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                setItemToDelete(item.id);
                                setDeleteDialogOpen(true);
                              }}
                              className="text-zinc-500 hover:text-red-400 p-1 transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        
                        {isLowStock(item) && (
                          <div className="absolute top-2 right-2">
                            <AlertTriangle className="w-4 h-4 text-amber-500" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-xl font-cinzel">
              {editingItem ? 'EDIT PANTRY ITEM' : 'ADD PANTRY ITEM'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300 mb-2 block">Item Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Olive Oil, Cumin, Salt"
                className="bg-zinc-900 border-zinc-800"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300 mb-2 block">Quantity *</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="e.g., 1, 0.5, 16"
                  className="bg-zinc-900 border-zinc-800"
                />
              </div>
              <div>
                <Label className="text-zinc-300 mb-2 block">Unit *</Label>
                <Select value={unit} onValueChange={setUnit}>
                  <SelectTrigger className="bg-zinc-900 border-zinc-800">
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-800">
                    {COMMON_UNITS.map(u => (
                      <SelectItem key={u} value={u}>{u}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-zinc-300 mb-2 block">Category *</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="bg-zinc-900 border-zinc-800">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {PANTRY_CATEGORIES.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-zinc-300 mb-2 block">Low Stock Alert (optional)</Label>
              <Input
                type="number"
                step="0.1"
                value={lowStockThreshold}
                onChange={(e) => setLowStockThreshold(e.target.value)}
                placeholder="Alert me when below this amount"
                className="bg-zinc-900 border-zinc-800"
              />
              <p className="text-xs text-zinc-500 mt-1">
                You'll see a warning when this item falls below this quantity
              </p>
            </div>
            
            <Button
              onClick={saveItem}
              className="w-full bg-violet-600 hover:bg-violet-700"
            >
              {editingItem ? 'UPDATE ITEM' : 'ADD TO PANTRY'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-cinzel text-red-400">
              DISCARD THIS PROVISION?
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <p className="text-zinc-400 mb-6 italic">
              This item shall be struck from your royal inventory. The Court will no longer track it.
            </p>
            <div className="flex gap-3">
              <Button
                onClick={() => setDeleteDialogOpen(false)}
                variant="outline"
                className="flex-1 border-zinc-700 hover:bg-zinc-800"
              >
                KEEP IT
              </Button>
              <Button
                onClick={deleteItem}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                DISCARD
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Pantry;
