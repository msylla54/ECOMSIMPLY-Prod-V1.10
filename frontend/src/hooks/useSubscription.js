// ================================================================================
// ECOMSIMPLY - HOOK REACT PERSONNALISÉ POUR GESTION ABONNEMENTS
// ================================================================================

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ================================================================================
// 🎯 HOOK PRINCIPAL GESTION ABONNEMENT
// ================================================================================

export const useSubscription = (user = null) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [availablePlans, setAvailablePlans] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ================================================================================
  // 📊 CHARGEMENT DES DONNÉES
  // ================================================================================

  const loadSubscriptionData = useCallback(async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      // Charger les plans disponibles
      const plansResponse = await axios.get(`${BACKEND_URL}/subscription/plans`);
      setAvailablePlans(plansResponse.data.plans || {});

      // Charger le statut de l'abonnement
      if (token) {
        const statusResponse = await axios.get(`${BACKEND_URL}/subscription/status`, { headers });
        setSubscriptionStatus(statusResponse.data);
      }

    } catch (err) {
      console.error('❌ Erreur chargement abonnement:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur chargement abonnement');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadSubscriptionData();
  }, [loadSubscriptionData]);

  // ================================================================================
  // 💳 ACTIONS ABONNEMENT
  // ================================================================================

  const createSubscription = useCallback(async (planType, withTrial = false) => {
    try {
      setLoading(true);
      setError(null);

      const planConfig = availablePlans[planType];
      if (!planConfig) {
        throw new Error('Plan invalide');
      }

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentification requise');
      }

      const requestData = {
        plan_type: planType,
        price_id: planConfig.stripe_price_id,
        success_url: `${window.location.origin}/subscription/success`,
        cancel_url: `${window.location.origin}/subscription/cancel`,
        with_trial: withTrial
      };

      const response = await axios.post(`${BACKEND_URL}/subscription/create`, requestData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.checkout_url) {
        // Sauvegarder l'état avant redirection
        sessionStorage.setItem('subscription_attempt', JSON.stringify({
          plan_type: planType,
          with_trial: withTrial,
          timestamp: Date.now()
        }));

        // Rediriger vers Stripe Checkout
        window.location.href = response.data.checkout_url;
        return true;
      } else {
        throw new Error(response.data.message || 'Erreur création abonnement');
      }

    } catch (err) {
      console.error('❌ Erreur création abonnement:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur création abonnement');
      return false;
    } finally {
      setLoading(false);
    }
  }, [availablePlans]);

  const cancelSubscription = useCallback(async (immediate = false) => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentification requise');
      }

      await axios.post(`${BACKEND_URL}/subscription/cancel`, 
        { immediate },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Recharger les données
      await loadSubscriptionData();
      return true;

    } catch (err) {
      console.error('❌ Erreur annulation:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur annulation');
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadSubscriptionData]);

  const reactivateSubscription = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentification requise');
      }

      await axios.post(`${BACKEND_URL}/subscription/reactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Recharger les données
      await loadSubscriptionData();
      return true;

    } catch (err) {
      console.error('❌ Erreur réactivation:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur réactivation');
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadSubscriptionData]);

  // ================================================================================
  // 🔍 FONCTIONS UTILITAIRES
  // ================================================================================

  const canAccessFeature = useCallback((feature) => {
    if (!subscriptionStatus) return false;

    switch (feature) {
      case 'basic':
        return true; // Tous les utilisateurs

      case 'premium':
        return subscriptionStatus.can_access_features && 
               (subscriptionStatus.plan_type === 'pro' || 
                subscriptionStatus.plan_type === 'premium' ||
                subscriptionStatus.trial_active);

      case 'unlimited':
        return subscriptionStatus.can_access_features && 
               subscriptionStatus.plan_type === 'premium';

      case 'trial':
        return subscriptionStatus.can_start_trial;

      default:
        return false;
    }
  }, [subscriptionStatus]);

  const getRemainingSheets = useCallback(() => {
    if (!subscriptionStatus) return 0;
    
    if (subscriptionStatus.monthly_limit === Infinity) {
      return Infinity;
    }

    return Math.max(0, subscriptionStatus.monthly_limit - subscriptionStatus.monthly_used);
  }, [subscriptionStatus]);

  const getUsagePercentage = useCallback(() => {
    if (!subscriptionStatus) return 0;
    
    if (subscriptionStatus.monthly_limit === Infinity) {
      return 0;
    }

    return (subscriptionStatus.monthly_used / subscriptionStatus.monthly_limit) * 100;
  }, [subscriptionStatus]);

  const isNearLimit = useCallback(() => {
    return getUsagePercentage() > 80;
  }, [getUsagePercentage]);

  const needsUpgrade = useCallback(() => {
    return subscriptionStatus?.requires_action || 
           subscriptionStatus?.payment_failed || 
           getRemainingSheets() === 0;
  }, [subscriptionStatus, getRemainingSheets]);

  // ================================================================================
  // 📱 GESTION SUCCESS/CANCEL APRÈS STRIPE
  // ================================================================================

  const handleSubscriptionSuccess = useCallback(async () => {
    // Nettoyer le sessionStorage
    sessionStorage.removeItem('subscription_attempt');
    
    // Recharger les données
    await loadSubscriptionData();
    
    // Optionnel : afficher un message de succès
    return true;
  }, [loadSubscriptionData]);

  const handleSubscriptionCancel = useCallback(() => {
    // Nettoyer le sessionStorage
    sessionStorage.removeItem('subscription_attempt');
    
    // Optionnel : afficher un message d'annulation
    return true;
  }, []);

  // ================================================================================
  // 🎯 RETOUR DU HOOK
  // ================================================================================

  return {
    // État
    subscriptionStatus,
    availablePlans,
    loading,
    error,

    // Actions
    createSubscription,
    cancelSubscription,
    reactivateSubscription,
    loadSubscriptionData,

    // Utilitaires
    canAccessFeature,
    getRemainingSheets,
    getUsagePercentage,
    isNearLimit,
    needsUpgrade,

    // Handlers
    handleSubscriptionSuccess,
    handleSubscriptionCancel,

    // Raccourcis état
    isTrialActive: subscriptionStatus?.trial_active || false,
    canStartTrial: subscriptionStatus?.can_start_trial || false,
    currentPlan: subscriptionStatus?.plan_type || 'gratuit',
    hasSubscription: subscriptionStatus?.plan_type !== 'gratuit'
  };
};

// ================================================================================
// 🔧 HOOKS SPÉCIALISÉS
// ================================================================================

// Hook pour vérifier les limites avant une action
export const useSubscriptionLimits = () => {
  const checkLimits = useCallback(async (action) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return { allowed: false, reason: 'auth_required' };

      // Cette fonction pourrait appeler un endpoint spécifique pour vérifier les limites
      // Pour l'instant, on simule
      return { allowed: true };
      
    } catch (err) {
      return { allowed: false, reason: 'error', message: err.message };
    }
  }, []);

  return { checkLimits };
};

// Hook pour les notifications d'abonnement
export const useSubscriptionNotifications = () => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((notification) => {
    setNotifications(prev => [...prev, { ...notification, id: Date.now() }]);
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications
  };
};

export default useSubscription;