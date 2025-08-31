// ================================================================================
// ECOMSIMPLY - BENTO GRID FEATURES AWWWARDS
// Sections premium avec layout bento et micro-interactions
// ================================================================================

import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, Target, Shield, TrendingUp, Globe } from 'lucide-react';
import { Card, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';

const BentoFeatures = () => {
  const features = [
    {
      icon: Brain,
      title: "IA Avancée",
      description: "Analyse sémantique et génération intelligente de contenu e-commerce",
      gradient: "from-purple-500 to-pink-500",
      size: "large", // Prend 2 colonnes
      delay: 0
    },
    {
      icon: Zap,
      title: "Scrapage Ultra-Rapide",
      description: "Données extraites en temps réel depuis vos concurrents",
      gradient: "from-yellow-400 to-orange-500",
      size: "small",
      delay: 0.1
    },
    {
      icon: Target,
      title: "SEO Optimisé",
      description: "Score 98/100 garanti sur tous vos produits",
      gradient: "from-green-400 to-emerald-500",
      size: "small",
      delay: 0.2
    },
    {
      icon: Shield,
      title: "Publication Sécurisée",
      description: "Intégration directe avec + de7+ plateformes e-commerce",
      gradient: "from-blue-400 to-cyan-500",
      size: "medium",
      delay: 0.3
    },
    {
      icon: TrendingUp,
      title: "Analytics Temps Réel",
      description: "Suivi des performances et optimisations automatiques",
      gradient: "from-indigo-400 to-purple-500",
      size: "medium",
      delay: 0.4
    },
    {
      icon: Globe,
      title: "Multi-Plateforme",
      description: "Shopify, WooCommerce, Amazon, eBay et plus",
      gradient: "from-pink-400 to-rose-500",
      size: "large",
      delay: 0.5
    }
  ];

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
    hidden: { opacity: 0, y: 20 },
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
    <section className="py-24 bg-background relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-secondary/10" />
      </div>

      <div className="container mx-auto px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
          viewport={{ once: true }}
        >
          <Badge variant="secondary" className="mb-4 bg-primary/10 text-primary border-primary/20">
            Fonctionnalités Premium
          </Badge>
          
          <h2 className="text-fluid-4xl font-bold text-foreground mb-4">
            Automatisation{' '}
            <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Intelligente
            </span>
          </h2>
          
          <p className="text-fluid-lg text-muted-foreground max-w-2xl mx-auto">
            Notre technologie IA révolutionnaire transforme votre e-commerce avec des fonctionnalités de pointe
          </p>
        </motion.div>

        {/* Bento Grid */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-fr"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            const sizeClasses = {
              small: "md:col-span-1 md:row-span-1",
              medium: "md:col-span-2 md:row-span-1", 
              large: "md:col-span-2 md:row-span-2"
            };

            return (
              <motion.div
                key={index}
                variants={itemVariants}
                className={sizeClasses[feature.size]}
                whileHover={{ y: -5 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="h-full group hover:shadow-soft-lg transition-all duration-3 border-border/50 hover:border-border bg-card/50 backdrop-blur-sm">
                  <CardContent className="p-6 h-full flex flex-col justify-between">
                    <div>
                      {/* Icon with gradient background */}
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-3`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>

                      {/* Content */}
                      <h3 className="text-lg font-semibold text-foreground mb-2">
                        {feature.title}
                      </h3>
                      
                      <p className="text-muted-foreground text-sm leading-relaxed">
                        {feature.description}
                      </p>
                    </div>

                    {/* Decorative element for large cards */}
                    {feature.size === 'large' && (
                      <div className="mt-6">
                        <div className="w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
                        <div className="mt-4 flex items-center text-xs text-muted-foreground">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2" />
                          Actif
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Bottom CTA */}
        <motion.div 
          className="text-center mt-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 0.61, 0.36, 1] }}
          viewport={{ once: true }}
        >
          <p className="text-sm text-muted-foreground">
            Plus de 10,000 fiches produit générées avec un taux de satisfaction de 98%
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default BentoFeatures;