// ================================================================================
// ECOMSIMPLY - PREMIUM DASHBOARD SHELL AWWWARDS
// Shell moderne avec navigation et layout premium
// ================================================================================

import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { User, Settings, LogOut, Home, Menu, X } from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { DashboardLogo } from './ui/Logo';
import { cn } from '../lib/utils';

const DashboardShell = ({ 
  children, 
  onGoToHome, 
  onLogout, 
  user, 
  activeTab,
  setActiveTab,
  tabs = [] 
}) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const navigate = useNavigate();

  const navigationTabs = tabs.length > 0 ? tabs : [
    {
      id: 'generator',
      label: 'Générateur IA',
      icon: '🤖',
      description: 'Créez des fiches produit automatiquement'
    },
    {
      id: 'history',
      label: 'Historique',
      icon: '📚',
      description: 'Vos fiches générées'
    },
    {
      id: 'seo',
      label: 'SEO Premium',
      icon: '⚡',
      description: 'Optimisations SEO avancées'
    },
    {
      id: 'amazon',
      label: 'Amazon SP-API',
      icon: '🛒',
      description: 'Intégration Amazon Seller Central'
    },
    {
      id: 'shopify',
      label: 'Shopify',
      icon: '🛍️',
      description: 'Intégration Shopify Multi-boutiques'
    },
    {
      id: 'analytics',
      label: 'Analytics Pro',
      icon: '📊',
      description: 'Analyses détaillées'
    },
    {
      id: 'stores',
      label: 'Boutiques',
      icon: '🏪',
      description: 'Connexions e-commerce'
    },
    {
      id: 'subscription',
      label: 'Gestion Abonnement',
      icon: '💳',
      description: 'Gestion de votre plan'
    },
    {
      id: 'account',
      label: 'Gestion de compte',
      icon: '👤',
      description: 'Paramètres utilisateur'
    },
    {
      id: 'admin',
      label: 'Admin',
      icon: '⚙️',
      description: 'Administration et paramètres'
    }
  ];

  return (
    <div className="min-h-screen-safe bg-gradient-to-br from-background to-muted/10">
      {/* Header XXL avec logo ULTRA VISIBLE */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border h-24 md:h-32 lg:h-44">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-full gap-4 md:gap-6">
            
            {/* Left: Logo + Menu Toggle + Badge */}
            <div className="flex items-center gap-3 md:gap-4 flex-shrink-0">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-lg transition-colors duration-200 lg:hidden flex-shrink-0"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              
              <DashboardLogo 
                onClick={onGoToHome}
                className="hover:scale-105 transition-transform duration-300"
              />
              
              <Badge variant="secondary" className="hidden sm:inline-flex bg-primary/10 text-primary text-xs md:text-sm">
                Dashboard
              </Badge>
            </div>

            {/* Right: User Menu */}
            <div className="flex items-center space-x-3">
              {/* User Plan Badge */}
              {user?.subscription_plan && (
                <Badge 
                  variant={user.subscription_plan === 'premium' ? 'default' : 'secondary'}
                  className="hidden sm:inline-flex"
                >
                  {user.subscription_plan.charAt(0).toUpperCase() + user.subscription_plan.slice(1)}
                </Badge>
              )}

              {/* Home Button */}
              <Button 
                variant="ghost" 
                size="sm"
                onClick={onGoToHome}
                className="hidden sm:flex items-center gap-2 text-muted-foreground hover:text-foreground"
              >
                <Home className="w-4 h-4" />
                Accueil
              </Button>

              {/* User Dropdown */}
              <div className="relative group">
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span className="hidden sm:inline">{user?.email?.split('@')[0] || 'Utilisateur'}</span>
                </Button>
                
                {/* Dropdown Menu */}
                <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-soft-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-2 z-50">
                  <div className="p-2 space-y-1">
                    <button 
                      onClick={() => setActiveTab('subscription')}
                      className="flex items-center gap-3 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-md transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      Paramètres
                    </button>
                    <div className="h-px bg-border my-1" />
                    <button 
                      onClick={onLogout}
                      className="flex items-center gap-3 w-full px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Déconnexion
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex min-h-[calc(100vh-4rem)]">
        
        {/* Sidebar Navigation */}
        <motion.aside 
          className={cn(
            "bg-card/50 backdrop-blur-sm border-r border-border transition-all duration-300",
            // Mobile: Hidden by default, only show when sidebarOpen is true
            "lg:w-72 lg:static lg:translate-x-0",
            sidebarOpen 
              ? "fixed inset-y-0 w-72 translate-x-0 top-16 z-50 lg:relative lg:top-0" 
              : "fixed inset-y-0 w-72 -translate-x-full top-16 z-50 lg:relative lg:top-0 lg:translate-x-0",
            // Hide on mobile when not explicitly opened
            "hidden lg:block",
            sidebarOpen && "block"
          )}
          initial={{ x: -288, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
        >
          <div className="p-6 space-y-2">
            {navigationTabs.map((tab, index) => (
              <motion.button
                key={tab.id}
                onClick={() => {
                  if (tab.id === 'amazon') {
                    // Navigation vers route dédiée Amazon
                    navigate('/integrations/amazon');
                  } else if (tab.id === 'shopify') {
                    // Navigation vers route dédiée Shopify
                    navigate('/integrations/shopify');
                  } else {
                    // Navigation normale dans le dashboard
                    setActiveTab(tab.id);
                  }
                  setSidebarOpen(false); // Close mobile sidebar
                }}
                className={cn(
                  "w-full flex items-center gap-4 px-4 py-3 rounded-xl text-left transition-all duration-2 group",
                  activeTab === tab.id
                    ? "bg-primary/10 text-primary shadow-soft-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 + 0.3 }}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="text-2xl">{tab.icon}</div>
                <div className="flex-1">
                  <div className="font-medium text-sm">{tab.label}</div>
                  <div className="text-xs text-muted-foreground line-clamp-1">
                    {tab.description}
                  </div>
                </div>
                
                {activeTab === tab.id && (
                  <motion.div
                    className="w-1 h-1 bg-primary rounded-full"
                    layoutId="activeTab"
                    transition={{ duration: 0.2 }}
                  />
                )}
              </motion.button>
            ))}
          </div>
        </motion.aside>

        {/* Mobile Overlay */}
        {sidebarOpen && (
          <motion.div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        )}

        {/* Main Content */}
        <motion.main 
          className="flex-1 overflow-auto lg:ml-0"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.22, 0.61, 0.36, 1] }}
        >
          <div className="p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </motion.main>
      </div>
    </div>
  );
};

export default DashboardShell;