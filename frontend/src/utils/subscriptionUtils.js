// ================================================================================
// ECOMSIMPLY - UTILITAIRES POUR GESTION ABONNEMENTS
// ================================================================================

// ================================================================================
// 🎯 CONSTANTES
// ================================================================================

export const PLAN_TYPES = {
  GRATUIT: 'gratuit',
  PRO: 'pro',
  PREMIUM: 'premium'
};

export const SUBSCRIPTION_STATUS = {
  ACTIVE: 'active',
  TRIALING: 'trialing',
  PAST_DUE: 'past_due',
  CANCELED: 'canceled',
  UNPAID: 'unpaid',
  INCOMPLETE: 'incomplete'
};

export const FEATURES = {
  BASIC: 'basic',
  PREMIUM: 'premium',
  UNLIMITED: 'unlimited',
  TRIAL: 'trial'
};

// ================================================================================
// 💰 CONFIGURATION DES PLANS
// ================================================================================

export const PLAN_CONFIG = {
  [PLAN_TYPES.GRATUIT]: {
    name: 'Gratuit',
    price: 0,
    currency: 'EUR',
    features: [
      '1 fiche par mois',
      'IA basique',
      'Export CSV',
      'Support communautaire'
    ],
    limits: {
      sheets_per_month: 1,
      ai_level: 'basic',
      export_formats: ['csv'],
      support_level: 'community'
    },
    color: 'gray',
    icon: '📦'
  },
  
  [PLAN_TYPES.PRO]: {
    name: 'Pro',
    price: 29,
    currency: 'EUR',
    features: [
      '100 fiches par mois',
      'IA avancée GPT-4o',
      'Images haute qualité',
      'Export multi-format',
      'Support prioritaire'
    ],
    limits: {
      sheets_per_month: 100,
      ai_level: 'advanced',
      export_formats: ['csv', 'pdf', 'json', 'xlsx'],
      support_level: 'priority'
    },
    color: 'purple',
    icon: '⚡',
    recommended: true,
    trial_available: true
  },
  
  [PLAN_TYPES.PREMIUM]: {
    name: 'Premium',
    price: 99,
    currency: 'EUR',
    features: [
      'Fiches illimitées',
      'Toutes fonctionnalités Pro',
      'Analytics avancés',
      'Intégrations e-commerce',
      'Support dédié'
    ],
    limits: {
      sheets_per_month: Infinity,
      ai_level: 'premium',
      export_formats: ['csv', 'pdf', 'json', 'xlsx', 'shopify', 'woocommerce'],
      support_level: 'dedicated'
    },
    color: 'yellow',
    icon: '🏆',
    trial_available: true
  }
};

// ================================================================================
// 🔍 FONCTIONS UTILITAIRES
// ================================================================================

/**
 * Vérifie si un plan est payant
 */
export const isPaidPlan = (planType) => {
  return planType !== PLAN_TYPES.GRATUIT;
};

/**
 * Vérifie si un plan supporte l'essai gratuit
 */
export const supportsTrial = (planType) => {
  return PLAN_CONFIG[planType]?.trial_available || false;
};

/**
 * Obtient la configuration d'un plan
 */
export const getPlanConfig = (planType) => {
  return PLAN_CONFIG[planType] || PLAN_CONFIG[PLAN_TYPES.GRATUIT];
};

/**
 * Obtient la couleur associée à un plan
 */
export const getPlanColor = (planType) => {
  return getPlanConfig(planType).color;
};

/**
 * Obtient l'icône associée à un plan
 */
export const getPlanIcon = (planType) => {
  return getPlanConfig(planType).icon;
};

/**
 * Vérifie si un plan peut accéder à une fonctionnalité
 */
export const canAccessFeature = (planType, feature, trialActive = false) => {
  const config = getPlanConfig(planType);
  
  switch (feature) {
    case FEATURES.BASIC:
      return true; // Tous les plans
      
    case FEATURES.PREMIUM:
      return isPaidPlan(planType) || trialActive;
      
    case FEATURES.UNLIMITED:
      return planType === PLAN_TYPES.PREMIUM || trialActive;
      
    case FEATURES.TRIAL:
      return supportsTrial(planType);
      
    default:
      return false;
  }
};

/**
 * Calcule l'utilisation en pourcentage
 */
export const calculateUsagePercentage = (used, limit) => {
  if (limit === Infinity) return 0;
  if (limit === 0) return 100;
  return Math.min((used / limit) * 100, 100);
};

/**
 * Détermine si l'utilisateur approche de sa limite
 */
export const isNearLimit = (used, limit, threshold = 0.8) => {
  if (limit === Infinity) return false;
  return (used / limit) >= threshold;
};

/**
 * Formate le prix d'un plan
 */
export const formatPrice = (price, currency = 'EUR') => {
  if (price === 0) return 'Gratuit';
  
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
};

/**
 * Formate la limite mensuelle
 */
export const formatLimit = (limit) => {
  if (limit === Infinity) return 'Illimitées';
  if (limit === 1) return '1 fiche';
  return `${limit} fiches`;
};

/**
 * Détermine le prochain plan recommandé
 */
export const getNextPlan = (currentPlan) => {
  switch (currentPlan) {
    case PLAN_TYPES.GRATUIT:
      return PLAN_TYPES.PRO;
    case PLAN_TYPES.PRO:
      return PLAN_TYPES.PREMIUM;
    default:
      return null;
  }
};

/**
 * Vérifie si un abonnement est actif
 */
export const isSubscriptionActive = (status, trialActive = false) => {
  const activeStatuses = [
    SUBSCRIPTION_STATUS.ACTIVE,
    SUBSCRIPTION_STATUS.TRIALING
  ];
  
  return activeStatuses.includes(status) || trialActive;
};

/**
 * Calcule les jours restants d'un essai
 */
export const getTrialDaysRemaining = (trialEndDate) => {
  if (!trialEndDate) return 0;
  
  const end = new Date(trialEndDate);
  const now = new Date();
  const diffTime = end - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return Math.max(0, diffDays);
};

/**
 * Génère un message de statut personnalisé
 */
export const getStatusMessage = (subscriptionStatus) => {
  if (!subscriptionStatus) return 'Chargement...';
  
  const { 
    plan_type, 
    trial_active, 
    trial_end_date, 
    payment_failed, 
    requires_action 
  } = subscriptionStatus;
  
  if (payment_failed) {
    return '❌ Paiement en échec - Action requise';
  }
  
  if (trial_active) {
    const daysLeft = getTrialDaysRemaining(trial_end_date);
    return `🎁 Essai gratuit - ${daysLeft} jour${daysLeft > 1 ? 's' : ''} restant${daysLeft > 1 ? 's' : ''}`;
  }
  
  if (requires_action) {
    return '⚠️ Action requise';
  }
  
  const config = getPlanConfig(plan_type);
  return `${config.icon} Plan ${config.name} actif`;
};

/**
 * Valide les données d'abonnement
 */
export const validateSubscriptionData = (data) => {
  const errors = [];
  
  if (!data.plan_type || !Object.values(PLAN_TYPES).includes(data.plan_type)) {
    errors.push('Type de plan invalide');
  }
  
  if (typeof data.monthly_used !== 'number' || data.monthly_used < 0) {
    errors.push('Utilisation mensuelle invalide');
  }
  
  if (typeof data.monthly_limit !== 'number' || data.monthly_limit < 0) {
    errors.push('Limite mensuelle invalide');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// ================================================================================
// 📊 ANALYTICS ET TRACKING
// ================================================================================

/**
 * Track les événements d'abonnement
 */
export const trackSubscriptionEvent = (event, data = {}) => {
  // Intégration avec analytics (GA, Mixpanel, etc.)
  if (window.gtag) {
    window.gtag('event', event, {
      event_category: 'subscription',
      ...data
    });
  }
  
  if (window.posthog) {
    window.posthog.capture(event, data);
  }
  
  console.log('📊 Subscription Event:', event, data);
};

/**
 * Track les conversions d'abonnement
 */
export const trackConversion = (planType, withTrial = false) => {
  trackSubscriptionEvent('subscription_conversion', {
    plan_type: planType,
    with_trial: withTrial,
    timestamp: Date.now()
  });
};

/**
 * Track les annulations
 */
export const trackCancellation = (planType, reason = 'user_initiated') => {
  trackSubscriptionEvent('subscription_cancellation', {
    plan_type: planType,
    reason: reason,
    timestamp: Date.now()
  });
};

// ================================================================================
// 🔧 HELPERS POUR COMPOSANTS
// ================================================================================

/**
 * Génère les props pour un badge de plan
 */
export const getPlanBadgeProps = (planType, isActive = false) => {
  const config = getPlanConfig(planType);
  const colors = {
    gray: isActive ? 'bg-gray-200 text-gray-800' : 'bg-gray-100 text-gray-600',
    purple: isActive ? 'bg-purple-200 text-purple-800' : 'bg-purple-100 text-purple-600',
    yellow: isActive ? 'bg-yellow-200 text-yellow-800' : 'bg-yellow-100 text-yellow-600'
  };
  
  return {
    className: `inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colors[config.color]}`,
    children: `${config.icon} ${config.name}`
  };
};

/**
 * Génère les props pour un bouton de plan
 */
export const getPlanButtonProps = (planType, variant = 'primary') => {
  const config = getPlanConfig(planType);
  
  const variants = {
    primary: {
      gray: 'bg-gray-600 hover:bg-gray-700 text-white',
      purple: 'bg-purple-600 hover:bg-purple-700 text-white',
      yellow: 'bg-yellow-600 hover:bg-yellow-700 text-white'
    },
    outline: {
      gray: 'border-gray-300 text-gray-700 hover:bg-gray-50',
      purple: 'border-purple-300 text-purple-700 hover:bg-purple-50',
      yellow: 'border-yellow-300 text-yellow-700 hover:bg-yellow-50'
    }
  };
  
  return {
    className: `px-6 py-3 rounded-lg font-medium transition-colors ${variants[variant][config.color]}`,
    children: `${config.icon} Choisir ${config.name}`
  };
};

export default {
  PLAN_TYPES,
  SUBSCRIPTION_STATUS,
  FEATURES,
  PLAN_CONFIG,
  isPaidPlan,
  supportsTrial,
  getPlanConfig,
  canAccessFeature,
  calculateUsagePercentage,
  formatPrice,
  formatLimit,
  getStatusMessage,
  trackSubscriptionEvent
};