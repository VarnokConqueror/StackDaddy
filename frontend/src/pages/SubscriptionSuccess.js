import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { CheckCircle, Crown } from 'lucide-react';
import { motion } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SubscriptionSuccess({ user, setUser }) {
  const [searchParams] = useSearchParams();
  const [checking, setChecking] = useState(true);
  const [status, setStatus] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (!sessionId) {
      navigate('/subscription');
      return;
    }

    checkPaymentStatus(sessionId);
  }, []);

  const checkPaymentStatus = async (sessionId) => {
    const token = localStorage.getItem('token');
    let attempts = 0;
    const maxAttempts = 5;

    const poll = async () => {
      try {
        const response = await axios.get(`${API}/subscriptions/status/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.data.payment_status === 'paid') {
          setStatus('success');
          setChecking(false);
          
          // Refresh user data
          const userRes = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(userRes.data);
        } else if (response.data.status === 'expired') {
          setStatus('failed');
          setChecking(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setStatus('timeout');
          setChecking(false);
        }
      } catch (error) {
        setStatus('error');
        setChecking(false);
      }
    };

    poll();
  };

  return (
    <div className="min-h-screen bg-obsidian" data-testid="subscription-success-page">
      <Navigation user={user} />
      
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        {checking ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="w-16 h-16 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-2xl font-cinzel font-bold mb-2">PROCESSING YOUR PAYMENT</h2>
            <p className="text-zinc-400">Please wait while we confirm your subscription...</p>
          </motion.div>
        ) : status === 'success' ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
            data-testid="payment-success"
          >
            <div className="w-24 h-24 bg-gradient-to-br from-violet-600 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-cinzel font-black uppercase mb-4">WELCOME TO THE ELITE</h1>
            <p className="text-xl text-zinc-400 mb-8">
              Your subscription is now active. Enjoy all premium features!
            </p>
            
            <div className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8 mb-8">
              <Crown className="w-12 h-12 text-violet-500 mx-auto mb-4" />
              <h3 className="text-xl font-cinzel font-semibold mb-4">PREMIUM FEATURES UNLOCKED</h3>
              <ul className="text-left space-y-2 max-w-md mx-auto text-zinc-300">
                <li>✓ AI-powered meal planning</li>
                <li>✓ Unlimited meal plans</li>
                <li>✓ Unlimited supplement tracking</li>
                <li>✓ Smart shopping lists</li>
                <li>✓ Priority support</li>
              </ul>
            </div>

            <Button
              onClick={() => navigate('/dashboard')}
              className="bg-violet-600 hover:bg-violet-700 px-8 py-6 text-lg"
              data-testid="go-to-dashboard-button"
            >
              GO TO DASHBOARD
            </Button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
            data-testid="payment-failed"
          >
            <h2 className="text-3xl font-cinzel font-bold mb-4">PAYMENT VERIFICATION ISSUE</h2>
            <p className="text-zinc-400 mb-8">
              {status === 'timeout' && 'Payment verification timed out. Please check your email for confirmation.'}
              {status === 'failed' && 'Payment was not completed. Please try again.'}
              {status === 'error' && 'An error occurred. Please contact support.'}
            </p>
            <Button
              onClick={() => navigate('/subscription')}
              className="bg-zinc-700 hover:bg-zinc-600"
            >
              BACK TO SUBSCRIPTION
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default SubscriptionSuccess;