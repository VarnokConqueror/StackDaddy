import { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Gift, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function PromoCodeSection({ user, setUser }) {
  const [promoCode, setPromoCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);

  const redeemPromo = async () => {
    if (!promoCode) {
      toast.error('Please enter a promo code');
      return;
    }

    setRedeeming(true);
    const token = localStorage.getItem('token');

    try {
      const response = await axios.post(`${API}/promo/redeem`, 
        { code: promoCode },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      toast.success(response.data.message);
      setPromoCode('');

      // Refresh user data
      const userRes = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(userRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid promo code');
    } finally {
      setRedeeming(false);
    }
  };

  if (user?.subscription_status === 'active') {
    return null; // Don't show if already premium
  }

  return (
    <div className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Gift className="w-6 h-6 text-violet-500" />
        <h3 className="text-xl font-cinzel font-semibold">HAVE A PROMO CODE?</h3>
      </div>
      <p className="text-zinc-400 text-sm mb-4">
        Redeem a promo code to unlock lifetime premium access
      </p>
      <div className="flex gap-3">
        <Input
          value={promoCode}
          onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
          placeholder="Enter promo code"
          className="flex-1 bg-zinc-900 border-zinc-800 uppercase"
          data-testid="promo-code-input"
        />
        <Button
          onClick={redeemPromo}
          disabled={redeeming || !promoCode}
          className="bg-violet-600 hover:bg-violet-700"
          data-testid="redeem-promo-button"
        >
          {redeeming ? 'REDEEMING...' : 'REDEEM'}
        </Button>
      </div>
    </div>
  );
}

export default PromoCodeSection;
