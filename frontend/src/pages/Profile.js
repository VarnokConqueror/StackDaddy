import { useEffect, useState } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { User, Settings, Sparkles, Crown } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

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

function Profile({ user, setUser }) {
  const [aiConfig, setAiConfig] = useState(null);
  const [dietary, setDietary] = useState([]);
  const [cooking, setCooking] = useState([]);
  const [aiProvider, setAiProvider] = useState('openai');
  const [aiModel, setAiModel] = useState('gpt-5.2');
  const [aiKey, setAiKey] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAiConfig();
    if (user) {
      setDietary(user.dietary_preferences || []);
      setCooking(user.cooking_methods || []);
    }
  }, [user]);

  const fetchAiConfig = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/ai-config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiConfig(response.data);
      setAiProvider(response.data.provider || 'openai');
      setAiModel(response.data.model || 'gpt-5.2');
      if (response.data.api_key) {
        setAiKey('********');
      }
    } catch (error) {
      console.error('Failed to load AI config');
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    const token = localStorage.getItem('token');
    
    try {
      await axios.put(`${API}/auth/preferences`, {
        dietary_preferences: dietary,
        cooking_methods: cooking
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Preferences saved!');
      
      const userRes = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(userRes.data);
    } catch (error) {
      toast.error('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const saveAiConfig = async () => {
    setSaving(true);
    const token = localStorage.getItem('token');
    
    try {
      await axios.put(`${API}/ai-config`, {
        provider: aiProvider,
        model: aiModel,
        api_key: aiKey === '********' ? null : aiKey
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('AI configuration saved!');
      fetchAiConfig();
    } catch (error) {
      toast.error('Failed to save AI config');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="profile-page">
      <Navigation user={user} />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-cinzel font-black uppercase mb-2">PROFILE</h1>
          <p className="text-zinc-400">Manage your preferences and settings</p>
        </motion.div>

        {/* User Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-6"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-violet-600 to-pink-600 rounded-full flex items-center justify-center">
              <User className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-cinzel font-semibold">{user?.name}</h2>
              <p className="text-zinc-400">{user?.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {user?.subscription_status === 'active' ? (
              <div className="flex items-center gap-2 text-green-400">
                <Crown className="w-5 h-5" />
                <span className="font-semibold">PREMIUM MEMBER</span>
                {user?.subscription_end_date && (
                  <span className="text-sm text-zinc-500 ml-2">
                    Until {new Date(user.subscription_end_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            ) : (
              <div>
                <p className="text-zinc-400 mb-2">Free Plan</p>
                <Link to="/subscription">
                  <Button className="bg-neon-pink hover:bg-pink-600" size="sm" data-testid="upgrade-subscription-btn">
                    UPGRADE TO PREMIUM
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </motion.div>

        {/* Dietary Preferences */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6 mb-6"
        >
          <h2 className="text-xl font-cinzel font-semibold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-violet-500" />
            DIETARY PREFERENCES
          </h2>
          <div className="space-y-2 mb-4">
            {DIETARY_OPTIONS.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <Checkbox
                  id={`pref-${option}`}
                  checked={dietary.includes(option)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setDietary([...dietary, option]);
                    } else {
                      setDietary(dietary.filter(d => d !== option));
                    }
                  }}
                  data-testid={`dietary-pref-${option.toLowerCase().replace(' ', '-')}`}
                />
                <label htmlFor={`pref-${option}`} className="text-zinc-400 cursor-pointer">{option}</label>
              </div>
            ))}
          </div>

          <h3 className="text-lg font-cinzel font-semibold mb-4 mt-6">COOKING METHODS</h3>
          <div className="space-y-2 mb-4">
            {COOKING_METHODS.map((method) => (
              <div key={method} className="flex items-center space-x-2">
                <Checkbox
                  id={`cook-${method}`}
                  checked={cooking.includes(method)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setCooking([...cooking, method]);
                    } else {
                      setCooking(cooking.filter(m => m !== method));
                    }
                  }}
                  data-testid={`cooking-pref-${method.toLowerCase().replace(' ', '-')}`}
                />
                <label htmlFor={`cook-${method}`} className="text-zinc-400 cursor-pointer">{method}</label>
              </div>
            ))}
          </div>

          <Button
            onClick={savePreferences}
            disabled={saving}
            className="bg-violet-600 hover:bg-violet-700"
            data-testid="save-preferences-button"
          >
            {saving ? 'SAVING...' : 'SAVE PREFERENCES'}
          </Button>
        </motion.div>

        {/* AI Configuration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-6"
        >
          <h2 className="text-xl font-cinzel font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-500" />
            AI CONFIGURATION
          </h2>
          <p className="text-zinc-400 text-sm mb-6">
            Configure AI providers for meal plan generation. Leave API key empty to disable AI features.
          </p>

          <div className="space-y-4">
            <div>
              <Label className="text-zinc-300 mb-2 block">Provider</Label>
              <Select value={aiProvider} onValueChange={setAiProvider}>
                <SelectTrigger className="bg-zinc-900 border-zinc-800" data-testid="ai-provider-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Claude (Anthropic)</SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-zinc-300 mb-2 block">Model</Label>
              <Input
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
                placeholder="e.g., gpt-5.2, claude-sonnet-4-5, gemini-3-pro"
                className="bg-zinc-900 border-zinc-800"
                data-testid="ai-model-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300 mb-2 block">API Key</Label>
              <Input
                type="password"
                value={aiKey}
                onChange={(e) => setAiKey(e.target.value)}
                placeholder="Enter your API key"
                className="bg-zinc-900 border-zinc-800"
                data-testid="ai-key-input"
              />
            </div>

            <Button
              onClick={saveAiConfig}
              disabled={saving}
              className="bg-neon-pink hover:bg-pink-600"
              data-testid="save-ai-config-button"
            >
              {saving ? 'SAVING...' : 'SAVE AI CONFIG'}
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default Profile;