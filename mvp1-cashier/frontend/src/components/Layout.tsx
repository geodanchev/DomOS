import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/toaster';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Wallet, LogOut, User, Building2 } from 'lucide-react';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: 'Табло', icon: LayoutDashboard },
    { path: '/apartments', label: 'Домова книга', icon: Building2 },
    { path: '/payments', label: 'Плащания', icon: Wallet },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-primary">🏠 DomOS Касиер</h1>
            </div>

            {/* Navigation */}
            <nav className="flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive(item.path) ? 'secondary' : 'ghost'}
                      className={cn(
                        'gap-2',
                        isActive(item.path) && 'bg-primary/10 text-primary'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
            </nav>

            {/* User info and actions */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <User className="h-4 w-4" />
                {user?.display_name}
              </span>
              <ThemeToggle />
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Изход
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
};

export default Layout;
