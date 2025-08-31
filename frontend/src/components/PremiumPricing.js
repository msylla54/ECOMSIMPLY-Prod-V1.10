// ================================================================================
// ECOMSIMPLY - PREMIUM PRICING SECTION AWWWARDS
// Section tarification haut de gamme avec design system cohérent
// ================================================================================

import React from 'react';
import { motion } from 'framer-motion';
import { Check, Star, Zap, Crown } from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

const PremiumPricing = ({ 
  dynamicPricing, 
  t, 
  currentLanguage, 
  onShowTrialPlanSelection,
  setActiveModalTab,
  setShowLogin 
}) => {

  const plans = [
    {
      id: 'gratuit',
      name: t('planFree') || 'Gratuit',
      description: t('testWithoutCommitment') || 'Parfait pour commencer',
      price: dynamicPricing?.gratuit?.price ?? 0,
      popular: false,
      icon: Zap,
      gradient: 'from-slate-500 to-slate-600',
      features: [
        t('oneSheetPerMonth') || '1 fiche par mois',
        t('basicAiGeneration') || 'Génération IA basique',
        t('emailSupport') || 'Support email',
        'Export CSV'
      ]
    },
    {
      id: 'pro',
      name: 'Pro',
      description: 'Pour les professionnels',
      price: dynamicPricing?.pro?.price ?? 29,
      popular: true,
      icon: Star,
      gradient: 'from-purple-500 to-pink-500',
      features: [
        '100 fiches par mois',
        'IA Premium + SEO avancé',
        'Prix vérifié multi-sources',
        'Publication multi-plateformes',
        'Analytics détaillées',
        'Support prioritaire'
      ]
    },
    {
      id: 'premium',
      name: 'Premium',
      description: 'Solution entreprise',
      price: dynamicPricing?.premium?.price ?? 99,
      popular: false,
      icon: Crown,
      gradient: 'from-yellow-400 to-orange-500',
      features: [
        'Fiches illimitées',
        'IA Premium + Automation',
        'API accès complet',
        'Intégration personnalisée',
        'Analytics Pro + exports',
        'Support dédié 24/7',
        'Affiliation 15% commission'
      ]
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
    <section className="py-24 bg-gradient-to-br from-background via-muted/5 to-background relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
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
            💎 Tarification Premium
          </Badge>
          
          <h2 className="text-fluid-4xl lg:text-fluid-5xl font-bold text-foreground mb-4">
            Plans{' '}
            <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Adaptés
            </span>
          </h2>
          
          <p className="text-fluid-lg text-muted-foreground max-w-2xl mx-auto">
            {currentLanguage === 'fr' 
              ? 'Choisissez la solution parfaite pour transformer votre e-commerce avec notre technologie IA de pointe' 
              : 'Choose the perfect solution to transform your e-commerce with our cutting-edge AI technology'
            }
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {plans.map((plan, index) => {
            const Icon = plan.icon;
            
            return (
              <motion.div
                key={plan.id}
                variants={itemVariants}
                className={`relative ${plan.popular ? 'md:scale-105 z-10' : ''}`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20">
                    <Badge className="bg-primary text-primary-foreground px-4 py-1 shadow-soft-md">
                      ⭐ Plus Populaire
                    </Badge>
                  </div>
                )}

                <Card className={`h-full transition-all duration-3 hover:shadow-soft-lg ${plan.popular ? 'border-primary/50 shadow-soft-md' : 'border-border/50'} bg-card/80 backdrop-blur-sm`}>
                  <CardHeader className="text-center pb-6">
                    {/* Icon */}
                    <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center shadow-soft-sm`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>

                    {/* Plan Info */}
                    <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                    <p className="text-muted-foreground text-sm">{plan.description}</p>

                    {/* Price */}
                    <div className="mt-4">
                      <div className="flex items-baseline justify-center">
                        <span className="text-4xl font-bold text-foreground">{plan.price}€</span>
                        <span className="text-muted-foreground ml-2">/mois</span>
                      </div>
                      {plan.id === 'gratuit' && (
                        <p className="text-sm text-green-600 mt-1">Parfait pour commencer</p>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="pt-0">
                    {/* Features */}
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center text-sm">
                          <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                            <Check className="w-3 h-3 text-white" />
                          </div>
                          <span className="text-foreground">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA Button */}
                    <Button 
                      className={`w-full transition-all duration-2 ${
                        plan.popular 
                          ? 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-soft-md' 
                          : 'variant-outline hover:bg-accent/50'
                      }`}
                      size="lg"
                      onClick={() => {
                        if (plan.id === 'gratuit') {
                          setActiveModalTab('register');
                          setShowLogin(true);
                        } else {
                          onShowTrialPlanSelection();
                        }
                      }}
                    >
                      {plan.id === 'gratuit' ? 'Commencer Gratuitement' : `Essai Gratuit 7 Jours`}
                    </Button>

                    {/* Trial info */}
                    {plan.id !== 'gratuit' && (
                      <p className="text-xs text-muted-foreground text-center mt-3">
                        Puis {plan.price}€/mois • Annulable à tout moment
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Bottom Trust Elements */}
        <motion.div 
          className="text-center mt-16 pt-8 border-t border-border/50"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.22, 0.61, 0.36, 1] }}
          viewport={{ once: true }}
        >
          <p className="text-sm text-muted-foreground mb-4">
            💳 Paiement sécurisé • 🔄 Annulation simple • 📞 Support français
          </p>
          <div className="flex items-center justify-center gap-8 opacity-60 text-xs">
            <span>Stripe</span>
            <span>•</span>
            <span>SSL Sécurisé</span>
            <span>•</span>
            <span>RGPD Conforme</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default PremiumPricing;