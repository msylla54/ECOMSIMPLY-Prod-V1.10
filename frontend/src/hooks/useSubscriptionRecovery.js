// ================================================================================
// ECOMSIMPLY - HOOK REACT RECOVERY ABONNEMENTS - NOUVEAU
// ================================================================================

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ================================================================================
// 🎯 HOOK PRINCIPAL RECOVERY ABONNEMENT
// ================================================================================

export const useSubscriptionRecovery = (user = null) => {
  const [incompleteSubscriptions, setIncompleteSubscriptions] = useState([]);
  const [recoveryStats, setRecoveryStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ================================================================================
  // 📊 CHARGEMENT DES DONNÉES RECOVERY
  // ================================================================================

  const loadRecoveryData = useCallback(async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      // Charger les abonnements incomplets
      const incompleteResponse = await axios.get(`${BACKEND_URL}/subscription/incomplete`, { headers });
      setIncompleteSubscriptions(incompleteResponse.data.incomplete || []);

      // Charger les statistiques de récupération
      const historyResponse = await axios.get(`${BACKEND_URL}/subscription/history`, { headers });
      setRecoveryStats(historyResponse.data.recovery_statistics || {});

    } catch (err) {
      console.error('❌ Erreur chargement recovery:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur chargement recovery');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadRecoveryData();
  }, [loadRecoveryData]);

  // ================================================================================
  // 🔄 ACTIONS RECOVERY
  // ================================================================================

  const retryIncompleteSubscription = useCallback(async (subscriptionId, recoveryType = 'retry') => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentification requise');
      }

      const requestData = {
        subscription_id: subscriptionId,
        recovery_type: recoveryType
      };

      const response = await axios.post(`${BACKEND_URL}/subscription/retry`, requestData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.retry_url) {
        // Sauvegarder l'état avant redirection
        sessionStorage.setItem('recovery_attempt', JSON.stringify({
          subscription_id: subscriptionId,
          recovery_type: recoveryType,
          timestamp: Date.now()
        }));

        // Rediriger vers Stripe
        window.location.href = response.data.retry_url;
        return true;
      } else if (response.data.update_url) {
        // Redirection pour mise à jour paiement
        window.location.href = response.data.update_url;
        return true;
      } else {
        // Succès sans redirection
        await loadRecoveryData();
        return true;
      }

    } catch (err) {
      console.error('❌ Erreur retry subscription:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur retry subscription');
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadRecoveryData]);

  const createNewSubscriptionAfterFailure = useCallback(async (planType) => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentification requise');
      }

      const response = await axios.post(`${BACKEND_URL}/subscription/new-after-failure`, 
        { plan_type: planType },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.checkout_url) {
        // Sauvegarder l'état avant redirection
        sessionStorage.setItem('new_subscription_attempt', JSON.stringify({
          plan_type: planType,
          timestamp: Date.now()
        }));

        // Rediriger vers Stripe Checkout
        window.location.href = response.data.checkout_url;
        return true;
      } else {
        throw new Error(response.data.message || 'Erreur création nouvel abonnement');
      }

    } catch (err) {
      console.error('❌ Erreur nouvel abonnement post-échec:', err);
      setError(err.response?.data?.detail || err.message || 'Erreur nouvel abonnement');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // ================================================================================
  // 📱 GESTION SUCCESS/CANCEL APRÈS RECOVERY
  // ================================================================================

  const handleRecoverySuccess = useCallback(async () => {
    // Nettoyer le sessionStorage
    sessionStorage.removeItem('recovery_attempt');
    sessionStorage.removeItem('new_subscription_attempt');
    
    // Recharger les données
    await loadRecoveryData();
    
    return true;
  }, [loadRecoveryData]);

  const handleRecoveryCancel = useCallback(() => {
    // Nettoyer le sessionStorage
    sessionStorage.removeItem('recovery_attempt');
    sessionStorage.removeItem('new_subscription_attempt');
    
    return true;
  }, []);

  // ================================================================================
  // 🔍 FONCTIONS UTILITAIRES
  // ================================================================================

  const hasIncompleteSubscriptions = useCallback(() => {
    return incompleteSubscriptions.length > 0;
  }, [incompleteSubscriptions]);

  const getRecoverableSubscriptions = useCallback(() => {
    return incompleteSubscriptions.filter(sub => sub.can_retry);
  }, [incompleteSubscriptions]);

  const getTotalFailedAttempts = useCallback(() => {
    return recoveryStats.failed_payment_attempts || 0;
  }, [recoveryStats]);

  const canAttemptRecovery = useCallback(() => {
    const maxAttempts = 5;
    const currentAttempts = recoveryStats.recovery_attempts || 0;
    return currentAttempts < maxAttempts;
  }, [recoveryStats]);

  const getRecoveryRecommendation = useCallback(() => {
    if (!hasIncompleteSubscriptions()) {
      return {
        type: 'none',
        message: 'Aucune récupération nécessaire'
      };
    }

    const recoverableSubs = getRecoverableSubscriptions();
    if (recoverableSubs.length === 0) {
      return {
        type: 'new_subscription',
        message: 'Les abonnements ne peuvent pas être récupérés. Créez un nouvel abonnement.'
      };
    }

    if (!canAttemptRecovery()) {
      return {
        type: 'contact_support',
        message: 'Trop de tentatives de récupération. Contactez le support.'
      };
    }

    return {
      type: 'retry',
      message: 'Vous pouvez relancer vos abonnements incomplets.',
      subscriptions: recoverableSubs
    };
  }, [hasIncompleteSubscriptions, getRecoverableSubscriptions, canAttemptRecovery]);

  // ================================================================================
  // 🎯 RETOUR DU HOOK
  // ================================================================================

  return {
    // État
    incompleteSubscriptions,
    recoveryStats,
    loading,
    error,

    // Actions
    retryIncompleteSubscription,
    createNewSubscriptionAfterFailure,
    loadRecoveryData,

    // Handlers
    handleRecoverySuccess,
    handleRecoveryCancel,

    // Utilitaires
    hasIncompleteSubscriptions,
    getRecoverableSubscriptions,
    getTotalFailedAttempts,
    canAttemptRecovery,
    getRecoveryRecommendation,

    // Raccourcis état
    hasRecoveryOptions: hasIncompleteSubscriptions() || getTotalFailedAttempts() > 0,
    needsRecovery: hasIncompleteSubscriptions(),
    recoveryBlocked: !canAttemptRecovery()
  };
};

// ================================================================================
// 🔧 HOOKS SPÉCIALISÉS
// ================================================================================

// Hook pour notifications de recovery
export const useRecoveryNotifications = () => {
  const [notifications, setNotifications] = useState([]);

  const addRecoveryNotification = useCallback((type, subscription = null) => {
    const messages = {
      'incomplete_detected': 'Abonnement incomplet détecté - Vous pouvez le finaliser',
      'retry_available': 'Une tentative de récupération est disponible',
      'payment_failed': 'Échec de paiement - Mise à jour requise',
      'recovery_success': 'Récupération réussie ! Votre abonnement est maintenant actif',
      'recovery_failed': 'Échec de récupération - Contactez le support si le problème persiste'
    };

    const notification = {
      id: Date.now(),
      type,
      message: messages[type] || 'Notification de récupération',
      subscription,
      timestamp: new Date()
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-suppression après 10 secondes
    setTimeout(() => {
      removeRecoveryNotification(notification.id);
    }, 10000);
  }, []);

  const removeRecoveryNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearRecoveryNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    recoveryNotifications: notifications,
    addRecoveryNotification,
    removeRecoveryNotification,
    clearRecoveryNotifications
  };
};

// Hook pour monitoring recovery
export const useRecoveryMonitoring = (user) => {
  const [monitoringData, setMonitoringData] = useState({
    totalAttempts: 0,
    successRate: 0,
    lastAttempt: null,
    commonFailureReasons: []
  });

  useEffect(() => {
    const calculateMonitoringData = () => {
      if (!user?.payment_attempts) return;

      const attempts = user.payment_attempts;
      const totalAttempts = attempts.length;
      const successfulAttempts = attempts.filter(a => a.status === 'succeeded').length;
      const successRate = totalAttempts > 0 ? (successfulAttempts / totalAttempts) * 100 : 0;
      const lastAttempt = attempts.length > 0 ? attempts[attempts.length - 1] : null;

      // Analyser les raisons d'échec les plus communes
      const failureReasons = attempts
        .filter(a => a.status === 'failed' && a.failure_reason)
        .reduce((acc, a) => {
          acc[a.failure_reason] = (acc[a.failure_reason] || 0) + 1;
          return acc;
        }, {});

      const commonFailureReasons = Object.entries(failureReasons)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 3)
        .map(([reason, count]) => ({ reason, count }));

      setMonitoringData({
        totalAttempts,
        successRate: Math.round(successRate),
        lastAttempt,
        commonFailureReasons
      });
    };

    calculateMonitoringData();
  }, [user]);

  return monitoringData;
};

export default useSubscriptionRecovery;