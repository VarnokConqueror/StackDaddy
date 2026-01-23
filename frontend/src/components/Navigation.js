import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Crown, LayoutDashboard, Utensils, ShoppingCart, Package, Pill, Heart, User, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

function Navigation({ user }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-obsidian-light border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/dashboard" className="flex items-center gap-2" data-testid="logo-link">
            <Crown className="w-8 h-8 text-violet-500" />
            <span className="text-xl font-cinzel font-bold text-zinc-50">CONQUEROR'S COURT</span>
          </Link>

          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/dashboard"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/dashboard') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-dashboard"
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Dashboard</span>
            </Link>
            <Link
              to="/meal-planner"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/meal-planner') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-meal-planner"
            >
              <Utensils className="w-4 h-4" />
              <span>Meals</span>
            </Link>
            <Link
              to="/shopping-list"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/shopping-list') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-shopping-list"
            >
              <ShoppingCart className="w-4 h-4" />
              <span>Shopping</span>
            </Link>
            <Link
              to="/pantry"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/pantry') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-pantry"
            >
              <Package className="w-4 h-4" />
              <span>Pantry</span>
            </Link>
            <Link
              to="/supplements"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/supplements') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-supplements"
            >
              <Pill className="w-4 h-4" />
              <span>Supps</span>
            </Link>
            <Link
              to="/profile"
              className={`flex items-center gap-1.5 px-2 py-2 transition-colors text-sm ${
                isActive('/profile') ? 'text-violet-500' : 'text-zinc-400 hover:text-zinc-50'
              }`}
              data-testid="nav-profile"
            >
              <User className="w-4 h-4" />
              <span>Profile</span>
            </Link>
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="text-zinc-400 hover:text-red-400"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;