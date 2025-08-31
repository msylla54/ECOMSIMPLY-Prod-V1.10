// ================================================================================
// ECOMSIMPLY - HERO SECTION AWWWARDS PREMIUM
// Layout editorial haut de gamme avec grille 12 colonnes
// ================================================================================

import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Zap, Star } from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';

const HeroSection = ({ 
  onShowTrialPlanSelection, 
  currentLanguage = 'fr',
  PLATFORM_CONFIG = {},
  className = '' 
}) => {

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.22, 0.61, 0.36, 1],
      },
    },
  };

  return (
    <div className={cn("relative", className)}>
      {/* Hero Section - Layout Editorial Premium */}
      <section className="min-h-screen-safe bg-gradient-to-br from-background via-background to-muted/20 relative overflow-hidden">
        
        {/* Gradient Mesh Subtil CSS-only */}
        <div className="absolute inset-0 overflow-hidden bg-gradient-mesh"></div>

        {/* Container xl avec grille 12 */}
        <div className="container mx-auto px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-12 gap-6 lg:gap-8 min-h-screen-safe items-center">
            
            {/* Colonne de contenu principal - 8/12 sur desktop */}
            <motion.div 
              className="col-span-12 lg:col-span-8 py-20 lg:py-32"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              
              {/* Badge Premium */}
              <motion.div variants={itemVariants} className="mb-6">
                <Badge 
                  variant="secondary" 
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 transition-all duration-2"
                >
                  <Sparkles className="w-4 h-4" />
                  IA de Surveillance 24h/24
                </Badge>
              </motion.div>

              {/* Titre Principal - Grande typographie */}
              <motion.h1 
                variants={itemVariants}
                className="text-fluid-5xl lg:text-fluid-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6"
              >
                <span className="block">Imaginer une IA qui veille</span>
                <span className="block bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  sur votre boutique 24h/24
                </span>
              </motion.h1>

              {/* Subtitle élégant */}
              <motion.p 
                variants={itemVariants}
                className="text-fluid-lg text-muted-foreground max-w-2xl mb-8 leading-relaxed"
              >
                Elle analyse en continu vos concurrents, optimise les SEO produits et publie les améliorations sur vos boutiques en temps réel grâce à un scraping intelligent et automatique. Cette technologie révolutionnaire vous offre un avantage concurrentiel permanent et automatisé.
              </motion.p>

              {/* Section RÉSULTAT */}
              <motion.div 
                variants={itemVariants}
                className="mb-8 p-6 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl border border-border/50"
              >
                <h2 className="text-fluid-xl font-bold text-primary mb-4">RÉSULTAT</h2>
                <p className="text-fluid-base text-muted-foreground leading-relaxed">
                  Pendant que vous dormez, votre boutique gagne en visibilité, en conversion, et maintient une longueur d'avance permanente sur vos concurrents.
                </p>
              </motion.div>

              {/* Stats rapides */}
              <motion.div 
                variants={itemVariants}
                className="flex flex-wrap items-center gap-6 mb-10"
              >
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-sm text-muted-foreground">+10,000 fiches générées</span>
                </div>
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span className="text-sm text-muted-foreground">98% de satisfaction</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-primary" />
                  <span className="text-sm text-muted-foreground">Génération en 28s</span>
                </div>
              </motion.div>

              {/* CTA Buttons - Même texte, design premium */}
              <motion.div 
                variants={itemVariants}
                className="flex flex-col sm:flex-row gap-4"
              >
                <Button 
                  size="lg"
                  className="group bg-primary hover:bg-primary/90 text-primary-foreground shadow-soft-lg hover:shadow-soft-md transition-all duration-2 px-8 py-4"
                  onClick={() => window.location.href = '/demo'}
                >
                  <span>Lancer la Démo</span>
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform duration-2" />
                </Button>
                
                <Button 
                  variant="outline" 
                  size="lg"
                  className="border-2 hover:bg-accent/50 transition-all duration-2 px-8 py-4"
                  onClick={onShowTrialPlanSelection}
                >
                  Essai Gratuit 7 Jours
                </Button>
              </motion.div>

              {/* Trust indicators */}
              <motion.div 
                variants={itemVariants}
                className="mt-12 pt-8 border-t border-border/50"
              >
                <p className="text-xs text-muted-foreground mb-4">Utilisé par plus de 1000 e-commerçants</p>
                <div className="flex items-center gap-6 opacity-60">
                  <div className="text-sm font-medium">Shopify</div>
                  <div className="text-sm font-medium">WooCommerce</div>
                  <div className="text-sm font-medium">Amazon</div>
                  <div className="text-sm font-medium">eBay</div>
                </div>
              </motion.div>
            </motion.div>

            {/* Colonne visuelle - 4/12 sur desktop */}
            <motion.div 
              className="col-span-12 lg:col-span-4"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.4, ease: [0.22, 0.61, 0.36, 1] }}
            >
              {/* Panneau de démonstration visuel */}
              <div className="relative">
                <div className="bg-card border border-border rounded-2xl shadow-soft-lg p-6 backdrop-blur-sm">
                  <div className="mb-4">
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                      <motion.div 
                        className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full"
                        initial={{ width: '0%' }}
                        animate={{ width: '85%' }}
                        transition={{ duration: 2, delay: 1, ease: 'easeOut' }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">Génération de fiche en cours...</p>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="h-4 bg-muted rounded w-3/4" />
                    <div className="h-4 bg-muted rounded w-1/2" />
                    <div className="h-4 bg-muted rounded w-5/6" />
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-border">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">SEO Score</span>
                      <span className="text-green-600 font-medium">98/100</span>
                    </div>
                  </div>
                </div>
                
                {/* Floating elements */}
                <motion.div 
                  className="absolute -top-4 -right-4 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center"
                  animate={{ y: [-4, 4, -4] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <Zap className="w-4 h-4 text-white" />
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HeroSection;