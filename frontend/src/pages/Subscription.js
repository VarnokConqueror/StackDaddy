import { useState, useEffect } from 'react';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import PromoCodeSection from '@/components/PromoCodeSection';
import { Button } from '@/components/ui/button';
import { Crown, Check, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function Subscription({ user, setUser }) {
  const [processing, setProcessing] = useState(false);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (user?.subscription_status === 'active') {
      fetchSubscriptionDetails();
    }
  }, [user]);

  // Check for session_id in URL (returning from Stripe)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    if (sessionId) {
      pollPaymentStatus(sessionId);
    }
  }, []);

  const fetchSubscriptionDetails = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await axios.get(`${API}/subscriptions/details`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscriptionDetails(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription details');
    }
  };

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const token = localStorage.getItem('token');

    if (attempts >= maxAttempts) {
      toast.info('Payment status check timed out. Please refresh the page.');
      return;
    }

    try {
      const response = await axios.get(`${API}/subscriptions/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.payment_status === 'paid') {
        toast.success('Payment successful! Welcome to Premium!');
        // Refresh user data
        const userRes = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(userRes.data);
        // Clean up URL
        window.history.replaceState({}, '', '/subscription');
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
    } catch (error) {
      console.error('Error checking payment status');
    }
  };

  const handleSubscribe = async (packageId) => {
    setProcessing(true);
    const token = localStorage.getItem('token');
    const originUrl = window.location.origin;
    
    try {
      const response = await axios.post(`${API}/subscriptions/checkout`, {
        package_id: packageId,
        origin_url: originUrl
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initiate checkout');
      setProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.')) {
      return;
    }

    setCancelling(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(`${API}/subscriptions/cancel`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(response.data.message);
      fetchSubscriptionDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel subscription');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="subscription-page">
      <Navigation user={user} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <Crown className="w-16 h-16 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl md:text-5xl font-cinzel font-black uppercase mb-4">CLAIM YOUR THRONE</h1>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            Unlock premium features and take full control of your nutrition empire
          </p>
        </motion.div>

        {user?.subscription_status === 'active' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-8 text-center mb-12"
            data-testid="premium-status-banner"
          >
            <h2 className="text-2xl font-cinzel font-bold mb-2">YOU ARE A PREMIUM MEMBER</h2>
            <p className="text-zinc-300 mb-4">
              Your subscription is active until {user.subscription_end_date && new Date(user.subscription_end_date).toLocaleDateString()}
            </p>
            
            {subscriptionDetails && (
              <div className="mt-4 space-y-2">
                {subscriptionDetails.cancel_at_period_end ? (
                  <div className="flex items-center justify-center gap-2 text-amber-400">
                    <AlertCircle className="w-5 h-5" />
                    <span>Your subscription will end on {new Date(subscriptionDetails.current_period_end).toLocaleDateString()}</span>
                  </div>
                ) : subscriptionDetails.plan && (
                  <Button
                    onClick={handleCancelSubscription}
                    disabled={cancelling}
                    variant="outline"
                    className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                    data-testid="cancel-subscription-button"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    {cancelling ? 'CANCELLING...' : 'CANCEL SUBSCRIPTION'}
                  </Button>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Promo Code Section */}
        {user?.subscription_status !== 'active' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="max-w-2xl mx-auto mb-12"
          >
            <PromoCodeSection user={user} setUser={setUser} />
          </motion.div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Monthly Plan */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8 hover:border-violet-500/30 transition-colors duration-300"
            data-testid="monthly-plan-card"
          >
            <h3 className="text-2xl font-cinzel font-bold mb-2">MONTHLY</h3>
            <div className="mb-6">
              <span className="text-4xl font-black text-violet-500">$9.99</span>
              <span className="text-zinc-400">/month</span>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-violet-500" />
                AI-powered meal planning
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-violet-500" />
                Unlimited meal plans
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-violet-500" />
                Unlimited supplement tracking
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-violet-500" />
                Smart shopping lists
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-violet-500" />
                Priority support
              </li>
            </ul>

            <Button
              onClick={() => handleSubscribe('monthly')}
              disabled={processing || user?.subscription_status === 'active'}
              className="w-full bg-violet-600 hover:bg-violet-700 h-12 text-lg"
              data-testid="subscribe-monthly-button"
            >
              {processing ? 'PROCESSING...' : 'SUBSCRIBE MONTHLY'}
            </Button>
          </motion.div>

          {/* Yearly Plan */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-violet-600/20 to-pink-600/20 border-2 border-neon-pink/50 p-8 relative"
            data-testid="yearly-plan-card"
          >
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-neon-pink px-4 py-1 text-sm font-bold uppercase">
              BEST VALUE
            </div>

            <h3 className="text-2xl font-cinzel font-bold mb-2">YEARLY</h3>
            <div className="mb-6">
              <span className="text-4xl font-black text-neon-pink">$99.99</span>
              <span className="text-zinc-400">/year</span>
              <p className="text-sm text-zinc-400 mt-1">Save $20 compared to monthly</p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-neon-pink" />
                AI-powered meal planning
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-neon-pink" />
                Unlimited meal plans
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-neon-pink" />
                Unlimited supplement tracking
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-neon-pink" />
                Smart shopping lists
              </li>
              <li className="flex items-center gap-2 text-zinc-300">
                <Check className="w-5 h-5 text-neon-pink" />
                Priority support
              </li>
              <li className="flex items-center gap-2 text-neon-pink font-semibold">
                <Check className="w-5 h-5" />
                2 months FREE
              </li>
            </ul>

            <Button
              onClick={() => handleSubscribe('yearly')}
              disabled={processing || user?.subscription_status === 'active'}
              className="w-full bg-neon-pink hover:bg-pink-600 h-12 text-lg"
              data-testid="subscribe-yearly-button"
            >
              {processing ? 'PROCESSING...' : 'SUBSCRIBE YEARLY'}
            </Button>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center mt-12 text-zinc-500 text-sm"
        >
          <p>Secure payment processing powered by Stripe</p>
          <p className="mt-2">Cancel anytime. No questions asked.</p>
        </motion.div>
      </div>
    </div>
  );
}

export default Subscription;