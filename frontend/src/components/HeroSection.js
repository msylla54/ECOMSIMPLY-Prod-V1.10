// ================================================================================
// HERO SECTION - OFFRE UNIQUE PREMIUM AVEC CTA DIRECT STRIPE CHECKOUT
// ================================================================================

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Sparkles, ArrowRight, Users, Star, TrendingUp } from 'lucide-react';

const HeroSection = ({ 
  user, 
  currentLanguage, 
  onDirectPremiumCheckout  // Changé: CTA direct vers Stripe Checkout
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const heroStats = [
    { 
      icon: Users, 
      value: '5000+', 
      label: currentLanguage === 'fr' ? 'E-commerçants actifs' : 'Active merchants' 
    },
    { 
      icon: Star, 
      value: '4.9/5', 
      label: currentLanguage === 'fr' ? 'Note moyenne' : 'Average rating' 
    },
    { 
      icon: TrendingUp, 
      value: '85%', 
      label: currentLanguage === 'fr' ? 'Conversion améliorée' : 'Improved conversion' 
    }
  ];

  return (
    <section className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/5 to-background overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-secondary/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '4s' }} />
      </div>

      <div className="container mx-auto px-6 lg:px-8 text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 30 }}
          transition={{ duration: 0.8, ease: [0.22, 0.61, 0.36, 1] }}
          className="max-w-5xl mx-auto"
        >
          {/* Badge */}
          <Badge variant="secondary" className="mb-6 bg-primary/10 text-primary border-primary/20">
            <Sparkles className="w-4 h-4 mr-2" />
            {currentLanguage === 'fr' ? '🚀 IA Révolutionnaire' : '🚀 Revolutionary AI'}
          </Badge>

          {/* Main Headline */}
          <h1 className="text-fluid-4xl lg:text-fluid-6xl font-bold text-foreground mb-6 leading-tight">
            {currentLanguage === 'fr' ? (
              <>
                Créez des fiches produits{' '}
                <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  exceptionnelles
                </span>{' '}
                en quelques clics
              </>
            ) : (
              <>
                Create{' '}
                <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  exceptional
                </span>{' '}
                product sheets in clicks
              </>
            )}
          </h1>

          {/* Subtitle */}
          <p className="text-fluid-lg text-muted-foreground max-w-3xl mx-auto mb-8 leading-relaxed">
            {currentLanguage === 'fr' 
              ? 'Notre IA Premium transforme vos produits en fiches optimisées pour Amazon, Shopify et plus. Automatisation complète, conversion maximisée.' 
              : 'Our Premium AI transforms your products into optimized sheets for Amazon, Shopify and more. Complete automation, maximized conversion.'
            }
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button 
              size="lg" 
              className="w-full sm:w-auto min-w-[240px] bg-primary hover:bg-primary/90 text-primary-foreground shadow-soft-lg transition-all duration-2"
              onClick={onDirectPremiumCheckout}  // CTA DIRECT VERS STRIPE CHECKOUT
            >
              <Sparkles className="w-5 h-5 mr-2" />
              {currentLanguage === 'fr' ? 'Essai Gratuit 3 Jours' : '3-Day Free Trial'}
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            
            <p className="text-sm text-muted-foreground">
              {currentLanguage === 'fr' 
                ? 'Puis 99€/mois • Annulable à tout moment' 
                : 'Then 99€/month • Cancel anytime'
              }
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-2xl mx-auto">
            {heroStats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
                transition={{ 
                  duration: 0.6, 
                  delay: 0.8 + index * 0.1,
                  ease: [0.22, 0.61, 0.36, 1] 
                }}
                className="flex flex-col items-center"
              >
                <stat.icon className="w-8 h-8 text-primary mb-2" />
                <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Bottom Trust Elements */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isVisible ? 1 : 0 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="mt-16 pt-8 border-t border-border/50"
        >
          <p className="text-sm text-muted-foreground mb-4">
            {currentLanguage === 'fr'
              ? '🔒 Données sécurisées • 🎯 IA Premium • 🚀 Résultats garantis'
              : '🔒 Secure data • 🎯 Premium AI • 🚀 Guaranteed results'
            }
          </p>
          <div className="flex items-center justify-center gap-8 opacity-60 text-xs">
            <span>Amazon SP-API</span>
            <span>•</span>
            <span>Shopify {currentLanguage === 'fr' ? 'Intégré' : 'Integrated'}</span>
            <span>•</span>
            <span>GPT-4 {currentLanguage === 'fr' ? 'Optimisé' : 'Optimized'}</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;