// ================================================================================
// ECOMSIMPLY - PREMIUM PRICING UNIQUE AVEC ESSAI 3 JOURS - CTA DIRECT STRIPE
// ================================================================================

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Crown, Zap } from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

const PremiumPricing = ({ 
  dynamicPricing, 
  t, 
  currentLanguage,
  onDirectPremiumCheckout  // CTA DIRECT VERS STRIPE CHECKOUT
}) => {
  const [loading, setLoading] = useState(false);

  // Configuration unique Premium avec essai 3 jours
  const premiumPlan = {
    id: 'premium',
    name: 'Premium',
    description: currentLanguage === 'fr' ? 'Solution complète pour votre e-commerce' : 'Complete e-commerce solution',
    price: dynamicPricing?.premium?.price ?? 99,
    popular: true,
    icon: Crown,
    gradient: 'from-yellow-400 to-orange-500',
    trialDays: 3,
    features: currentLanguage === 'fr' ? [
      'Fiches produits illimitées',
      'IA Premium + Automation complète',
      'Publication multi-plateformes',
      'Analytics avancées + exports',
      'Support prioritaire 24/7',
      'API accès complet',
      'Intégrations personnalisées'
    ] : [
      'Unlimited product sheets',
      'Premium AI + Complete automation',
      'Multi-platform publishing', 
      'Advanced analytics + exports',
      'Priority 24/7 support',
      'Full API access',
      'Custom integrations'
    ]
  };

  const handleStartTrial = () => {
    setLoading(true);
    try {
      // Appel direct à la fonction Premium Checkout
      onDirectPremiumCheckout();
    } catch (error) {
      console.error('Error starting trial:', error);
      setLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        ease: [0.22, 0.61, 0.36, 1],
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
            💎 {currentLanguage === 'fr' ? 'Offre Premium' : 'Premium Offer'}
          </Badge>
          
          <h2 className="text-fluid-4xl lg:text-fluid-5xl font-bold text-foreground mb-4">
            {currentLanguage === 'fr' ? 'Solution' : 'Solution'}{' '}
            <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              {currentLanguage === 'fr' ? 'Premium' : 'Premium'}
            </span>
          </h2>
          
          <p className="text-fluid-lg text-muted-foreground max-w-2xl mx-auto">
            {currentLanguage === 'fr' 
              ? 'Transformez votre e-commerce avec notre solution Premium complète. Essai gratuit 3 jours inclus.' 
              : 'Transform your e-commerce with our complete Premium solution. 3-day free trial included.'
            }
          </p>
        </motion.div>

        {/* Premium Card Unique */}
        <motion.div 
          className="max-w-md mx-auto"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.div variants={itemVariants} className="relative">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20">
              <Badge className="bg-primary text-primary-foreground px-4 py-1 shadow-soft-md">
                ⭐ {currentLanguage === 'fr' ? 'Recommandé' : 'Recommended'}
              </Badge>
            </div>

            <Card className="h-full transition-all duration-3 hover:shadow-soft-lg border-primary/50 shadow-soft-md bg-card/80 backdrop-blur-sm">
              <CardHeader className="text-center pb-6">
                {/* Icon */}
                <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${premiumPlan.gradient} flex items-center justify-center shadow-soft-sm`}>
                  <Crown className="w-8 h-8 text-white" />
                </div>

                {/* Plan Info */}
                <CardTitle className="text-2xl font-bold">{premiumPlan.name}</CardTitle>
                <p className="text-muted-foreground text-sm">{premiumPlan.description}</p>

                {/* Price */}
                <div className="mt-4">
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-foreground">{premiumPlan.price}€</span>
                    <span className="text-muted-foreground ml-2">
                      {currentLanguage === 'fr' ? '/mois' : '/month'}
                    </span>
                  </div>
                  <p className="text-sm text-green-600 mt-1 font-medium">
                    {currentLanguage === 'fr' 
                      ? '3 jours d\'essai gratuit inclus' 
                      : '3-day free trial included'
                    }
                  </p>
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                {/* Features */}
                <ul className="space-y-3 mb-8">
                  {premiumPlan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center text-sm">
                      <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                      <span className="text-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button - DIRECT STRIPE CHECKOUT */}
                <Button 
                  className="w-full transition-all duration-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-soft-md"
                  size="lg"
                  onClick={handleStartTrial}
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <Zap className="w-4 h-4 mr-2 animate-spin" />
                      {currentLanguage === 'fr' ? 'Création...' : 'Creating...'}
                    </div>
                  ) : (
                    currentLanguage === 'fr' 
                      ? 'Commencer essai 3 jours' 
                      : 'Start 3-day trial'
                  )}
                </Button>

                {/* Trial info */}
                <p className="text-xs text-muted-foreground text-center mt-3">
                  {currentLanguage === 'fr'
                    ? `Puis ${premiumPlan.price}€/mois • Annulable à tout moment`
                    : `Then ${premiumPlan.price}€/month • Cancel anytime`
                  }
                </p>
              </CardContent>
            </Card>
          </motion.div>
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
            {currentLanguage === 'fr'
              ? '💳 Paiement sécurisé • 🔄 Annulation simple • 📞 Support français'
              : '💳 Secure payment • 🔄 Easy cancellation • 📞 French support'
            }
          </p>
          <div className="flex items-center justify-center gap-8 opacity-60 text-xs">
            <span>Stripe</span>
            <span>•</span>
            <span>SSL {currentLanguage === 'fr' ? 'Sécurisé' : 'Secured'}</span>
            <span>•</span>
            <span>RGPD {currentLanguage === 'fr' ? 'Conforme' : 'Compliant'}</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default PremiumPricing;