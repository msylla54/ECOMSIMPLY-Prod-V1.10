// ================================================================================
// ECOMSIMPLY - COMPOSANT GUARD POUR PROTECTION DES FONCTIONNALITÉS
// ================================================================================

import React from 'react';
import { useSubscription } from '../hooks/useSubscription';

// ================================================================================
// 🛡️ GARDE PRINCIPAL POUR FONCTIONNALITÉS
// ================================================================================

const SubscriptionGuard = ({ 
  feature = 'premium', 
  children, 
  fallback = null,
  showUpgrade = true,
  customMessage = null
}) => {
  const { 
    canAccessFeature, 
    subscriptionStatus, 
    loading,
    currentPlan,
    isTrialActive,
    getRemainingSheets
  } = useSubscription();

  // Affichage loading
  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
        <span className="ml-2 text-gray-600">Vérification accès...</span>
      </div>
    );
  }

  // Vérifier l'accès à la fonctionnalité
  const hasAccess = canAccessFeature(feature);

  if (hasAccess) {
    return children;
  }

  // Afficher le fallback personnalisé si fourni
  if (fallback) {
    return fallback;
  }

  // Afficher la demande de mise à niveau par défaut
  if (showUpgrade) {
    return (
      <SubscriptionUpgradePrompt 
        feature={feature}
        currentPlan={currentPlan}
        isTrialActive={isTrialActive}
        customMessage={customMessage}
        remainingSheets={getRemainingSheets()}
      />
    );
  }

  // Ne rien afficher
  return null;
};

// ================================================================================
// 🔧 COMPOSANT DEMANDE DE MISE À NIVEAU
// ================================================================================

const SubscriptionUpgradePrompt = ({ 
  feature, 
  currentPlan, 
  isTrialActive, 
  customMessage,
  remainingSheets 
}) => {
  const getFeatureInfo = () => {
    switch (feature) {
      case 'premium':
        return {
          title: '⚡ Fonctionnalité Premium',
          description: 'Cette fonctionnalité nécessite un abonnement Pro ou Premium',
          benefits: [
            'IA avancée GPT-4o',
            'Images haute qualité',
            'Export multi-format',
            'Support prioritaire'
          ]
        };
      
      case 'unlimited':
        return {
          title: '♾️ Fonctionnalité Premium Illimitée',
          description: 'Cette fonctionnalité nécessite un abonnement Premium',
          benefits: [
            'Fiches illimitées',
            'Analytics avancés',
            'Intégrations e-commerce',
            'Support dédié'
          ]
        };
      
      case 'basic':
        return {
          title: '📦 Limite atteinte',
          description: `Vous avez utilisé toutes vos fiches disponibles${remainingSheets === 0 ? ' ce mois' : ''}`,
          benefits: [
            'Plus de fiches mensuelles',
            'Accès aux fonctionnalités premium',
            'Support prioritaire'
          ]
        };
      
      default:
        return {
          title: '🔒 Accès limité',
          description: 'Cette fonctionnalité nécessite un abonnement payant',
          benefits: ['Accès complet à la plateforme']
        };
    }
  };

  const featureInfo = getFeatureInfo();

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 text-center border border-purple-200">
      
      {/* Icône et titre */}
      <div className="mb-4">
        <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          {featureInfo.title}
        </h3>
        
        <p className="text-gray-600">
          {customMessage || featureInfo.description}
        </p>
      </div>

      {/* Statut actuel */}
      <div className="bg-white rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Plan actuel :</span>
          <span className="font-semibold capitalize">{currentPlan}</span>
        </div>
        
        {isTrialActive && (
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">Statut :</span>
            <span className="text-blue-600 font-semibold">🎁 Essai gratuit actif</span>
          </div>
        )}
        
        {remainingSheets !== Infinity && (
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">Fiches restantes :</span>
            <span className={`font-semibold ${remainingSheets === 0 ? 'text-red-600' : 'text-gray-900'}`}>
              {remainingSheets}
            </span>
          </div>
        )}
      </div>

      {/* Avantages */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">Débloquez ces avantages :</h4>
        <ul className="space-y-2">
          {featureInfo.benefits.map((benefit, index) => (
            <li key={index} className="flex items-center justify-center">
              <span className="text-green-500 mr-2">✅</span>
              <span className="text-gray-700">{benefit}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Boutons d'action */}
      <div className="space-y-3">
        <button
          onClick={() => window.location.href = '/subscription'}
          className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          🚀 Choisir un plan
        </button>
        
        <button
          onClick={() => window.location.href = '/plans'}
          className="w-full bg-gray-100 text-gray-700 font-semibold py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
        >
          📋 Voir tous les plans
        </button>
      </div>

    </div>
  );
};

// ================================================================================
// 🎯 GARDES SPÉCIALISÉS
// ================================================================================

// Garde pour les limites de fiches
export const SheetLimitGuard = ({ children, customMessage }) => (
  <SubscriptionGuard 
    feature="basic" 
    customMessage={customMessage}
  >
    {children}
  </SubscriptionGuard>
);

// Garde pour fonctionnalités premium
export const PremiumFeatureGuard = ({ children, customMessage }) => (
  <SubscriptionGuard 
    feature="premium" 
    customMessage={customMessage}
  >
    {children}
  </SubscriptionGuard>
);

// Garde pour fonctionnalités premium illimitées
export const UnlimitedFeatureGuard = ({ children, customMessage }) => (
  <SubscriptionGuard 
    feature="unlimited" 
    customMessage={customMessage}
  >
    {children}
  </SubscriptionGuard>
);

// ================================================================================
// 🔔 COMPOSANT ALERTE ABONNEMENT
// ================================================================================

export const SubscriptionAlert = () => {
  const { 
    subscriptionStatus, 
    needsUpgrade, 
    isNearLimit, 
    getRemainingSheets,
    getUsagePercentage 
  } = useSubscription();

  if (!subscriptionStatus || !needsUpgrade()) return null;

  const remainingSheets = getRemainingSheets();
  const usagePercentage = getUsagePercentage();

  if (subscriptionStatus.payment_failed) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div className="flex items-start">
          <div className="text-red-600 mr-3 mt-0.5">❌</div>
          <div className="flex-1">
            <div className="font-semibold text-red-800">Paiement en échec</div>
            <div className="text-red-700 text-sm mt-1">
              Veuillez mettre à jour votre mode de paiement pour continuer à utiliser les fonctionnalités premium.
            </div>
            <button
              onClick={() => window.open('https://billing.stripe.com', '_blank')}
              className="mt-2 bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 transition-colors"
            >
              💳 Mettre à jour le paiement
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (remainingSheets === 0) {
    return (
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
        <div className="flex items-start">
          <div className="text-orange-600 mr-3 mt-0.5">⚠️</div>
          <div className="flex-1">
            <div className="font-semibold text-orange-800">Limite mensuelle atteinte</div>
            <div className="text-orange-700 text-sm mt-1">
              Vous avez utilisé toutes vos fiches ce mois. Passez à un plan supérieur pour continuer.
            </div>
            <button
              onClick={() => window.location.href = '/subscription'}
              className="mt-2 bg-orange-600 text-white px-4 py-2 rounded text-sm hover:bg-orange-700 transition-colors"
            >
              🚀 Passer à Pro
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isNearLimit() && remainingSheets <= 2) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <div className="flex items-start">
          <div className="text-yellow-600 mr-3 mt-0.5">📊</div>
          <div className="flex-1">
            <div className="font-semibold text-yellow-800">Limite bientôt atteinte</div>
            <div className="text-yellow-700 text-sm mt-1">
              Il vous reste {remainingSheets} fiche{remainingSheets > 1 ? 's' : ''} ce mois ({usagePercentage.toFixed(0)}% utilisé).
            </div>
            <button
              onClick={() => window.location.href = '/subscription'}
              className="mt-2 bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700 transition-colors"
            >
              ⬆️ Améliorer le plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default SubscriptionGuard;