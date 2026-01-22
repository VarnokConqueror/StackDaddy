import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Crown, Utensils, Pill, ShoppingCart, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

function Landing() {
  return (
    <div className="min-h-screen bg-obsidian text-zinc-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-violet-600/10 via-transparent to-transparent" />
        <div className="absolute inset-0" style={{
          backgroundImage: `url(https://images.unsplash.com/photo-1633786207050-e1e183d06217)`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          opacity: 0.15
        }} />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <div className="flex items-center justify-center mb-6">
              <Crown className="w-16 h-16 text-violet-500" />
            </div>
            <h1 className="text-5xl md:text-7xl font-black font-cinzel tracking-tighter uppercase mb-6 glow-text">
              CONQUEROR'S COURT
            </h1>
            <p className="text-xl md:text-2xl text-zinc-400 mb-8 max-w-3xl mx-auto leading-relaxed">
              Master your nutrition kingdom. Command your meal plans. Track your supplements with royal precision.
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/register" data-testid="get-started-btn">
                <Button className="bg-violet-600 hover:bg-violet-700 text-white px-8 py-6 text-lg uppercase tracking-widest font-bold transition-all duration-300 hover:shadow-[0_0_20px_rgba(124,58,237,0.5)]">
                  BEGIN YOUR REIGN
                </Button>
              </Link>
              <Link to="/login" data-testid="login-btn">
                <Button variant="outline" className="bg-transparent border-2 border-zinc-700 hover:border-neon-pink text-zinc-300 hover:text-neon-pink px-8 py-6 text-lg uppercase tracking-widest transition-all duration-300">
                  ENTER COURT
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8 hover:border-violet-500/30 transition-colors duration-300"
          >
            <Utensils className="w-12 h-12 text-violet-500 mb-4" />
            <h3 className="text-2xl font-cinzel font-semibold mb-3">AI-Powered Meal Plans</h3>
            <p className="text-zinc-400 leading-relaxed">
              Generate personalized weekly or monthly meal plans based on your dietary preferences and cooking methods.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8 hover:border-neon-pink/30 transition-colors duration-300"
          >
            <Pill className="w-12 h-12 text-neon-pink mb-4" />
            <h3 className="text-2xl font-cinzel font-semibold mb-3">Supplement Mastery</h3>
            <p className="text-zinc-400 leading-relaxed">
              Track your supplement inventory, dosages, timing, and expiration dates with precision.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-zinc-950/50 backdrop-blur-xl border border-zinc-800/50 p-8 hover:border-violet-500/30 transition-colors duration-300"
          >
            <ShoppingCart className="w-12 h-12 text-violet-500 mb-4" />
            <h3 className="text-2xl font-cinzel font-semibold mb-3">Smart Shopping Lists</h3>
            <p className="text-zinc-400 leading-relaxed">
              Automatically generate organized shopping lists from your meal plans.
            </p>
          </motion.div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-violet-600/20 to-pink-600/20 border border-violet-500/30 p-12 text-center"
        >
          <Sparkles className="w-16 h-16 text-violet-500 mx-auto mb-6" />
          <h2 className="text-4xl md:text-5xl font-cinzel font-bold mb-4 uppercase">COMMAND YOUR NUTRITION</h2>
          <p className="text-xl text-zinc-400 mb-8 max-w-2xl mx-auto">
            Join the elite and transform your nutrition tracking into a strategic advantage.
          </p>
          <Link to="/register">
            <Button className="bg-neon-pink hover:bg-pink-600 text-white px-8 py-6 text-lg uppercase tracking-widest font-bold transition-all duration-300 hover:shadow-[0_0_20px_rgba(219,39,119,0.5)]">
              CLAIM YOUR THRONE
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="border-t border-zinc-800 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-zinc-600">
          <p>&copy; 2024 Conqueror's Court. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

export default Landing;