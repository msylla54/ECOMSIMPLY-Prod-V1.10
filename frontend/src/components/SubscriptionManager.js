// ================================================================================
// ECOMSIMPLY - COMPOSANT REACT COMPLET GESTION ABONNEMENTS - VERSION ROBUSTE
// ================================================================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
console.log('🔍 BACKEND_URL utilisée:', BACKEND_URL);

// ================================================================================
// 🎯 COMPOSANT PRINCIPAL GESTION ABONNEMENT
// ================================================================================

const SubscriptionManager = ({ user, onSubscriptionChange }) => {
  const [loading, setLoading] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [availablePlans, setAvailablePlans] = useState({});
  const [incompleteSubscriptions, setIncompleteSubscriptions] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // ================================================================================
  // 📊 CHARGEMENT DES DONNÉES
  // ================================================================================

  useEffect(() => {
    if (user) {
      loadSubscriptionData();
    }
  }, [user]);

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);
      
      // Charger les plans disponibles
      console.log('🔍 Début chargement plans - URL:', `${BACKEND_URL}/api/subscription/plans`);
      const plansResponse = await axios.get(`${BACKEND_URL}/api/subscription/plans`);
      console.log('📊 Plans reçus:', plansResponse.data);
      
      // ✅ CORRECTION: Transformer le tableau de plans en objet
      let plans = {};
      if (plansResponse.data && plansResponse.data.plans) {
        // Transformer le tableau en objet avec id comme clé
        plans = plansResponse.data.plans.reduce((acc, plan) => {
          acc[plan.id] = plan;
          return acc;
        }, {});
      }
      
      console.log('📊 Plans transformés:', plans);
      console.log('📊 Nombre de plans:', Object.keys(plans).length);
      setAvailablePlans(plans);
      
      // Charger le statut de l'abonnement
      const statusResponse = await axios.get(`${BACKEND_URL}/api/subscription/status`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setSubscriptionStatus(statusResponse.data);

      // ✅ NOUVEAU: Charger les abonnements incomplets
      try {
        const incompleteResponse = await axios.get(`${BACKEND_URL}/api/subscription/incomplete`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setIncompleteSubscriptions(incompleteResponse.data.incomplete || []);
      } catch (err) {
        console.log('Pas d\'abonnements incomplets');
      }
      
    } catch (error) {
      console.error('❌ Erreur chargement données abonnement:', error);
      setError('Erreur lors du chargement des informations d\'abonnement');
    } finally {
      setLoading(false);
    }
  };

  // ================================================================================
  // 🎯 VÉRIFICATION ÉLIGIBILITÉ ESSAI - SERVER-SIDE SOURCE OF TRUTH
  // ================================================================================

  const checkTrialEligibility = async (planType) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return { eligible: false, reason: 'auth_required' };

      const response = await axios.get(`${BACKEND_URL}/api/subscription/trial-eligibility`, {
        params: { plan: planType },
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('🔍 Trial eligibility check:', response.data);
      return response.data;
      
    } catch (error) {
      console.error('❌ Error checking trial eligibility:', error);
      // En cas d'erreur, être conservateur et refuser l'essai
      return { 
        eligible: false, 
        reason: 'eligibility_check_failed',
        message: 'Erreur lors de la vérification. Souscription directe disponible.'
      };
    }
  };

  // ================================================================================
  // 💳 GESTION ABONNEMENTS AVEC VÉRIFICATION ÉLIGIBILITÉ
  // ================================================================================

  const createSubscription = async (planType, withTrial = false) => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const planConfig = availablePlans[planType];
      if (!planConfig) {
        throw new Error('Plan invalide');
      }

      // ✅ NOUVEAU: Vérification éligibilité côté serveur avant création
      let actualWithTrial = withTrial;
      if (withTrial) {
        const eligibilityCheck = await checkTrialEligibility(planType);
        actualWithTrial = eligibilityCheck.eligible;
        
        if (!actualWithTrial) {
          console.log('⚠️ Trial requested but not eligible:', eligibilityCheck.reason);
          setError(`Essai non disponible: ${eligibilityCheck.message}`);
          
          // Proposer abonnement direct
          const confirmDirect = window.confirm(
            `${eligibilityCheck.message}\n\nVoulez-vous souscrire directement à ce plan ?`
          );
          
          if (!confirmDirect) {
            return false;
          }
          
          actualWithTrial = false;
        }
      }

      const requestData = {
        plan_type: planType,
        price_id: planConfig.stripe_price_id,
        success_url: `${window.location.origin}/subscription/success`,
        cancel_url: `${window.location.origin}/subscription/cancel`,
        with_trial: actualWithTrial  // ✅ Utiliser la valeur validée
      };

      console.log('🛒 Creating subscription:', { 
        ...requestData, 
        original_with_trial: withTrial,
        actual_with_trial: actualWithTrial 
      });

      const response = await axios.post(`${BACKEND_URL}/api/subscription/create`, requestData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.data.checkout_url) {
        // Sauvegarder l'intention pour analytics
        sessionStorage.setItem('subscription_attempt', JSON.stringify({
          plan_type: planType,
          with_trial: actualWithTrial,
          trial_requested: withTrial,
          timestamp: Date.now()
        }));

        // Rediriger vers Stripe Checkout
        window.location.href = response.data.checkout_url;
      } else {
        throw new Error(response.data.message || 'Erreur création abonnement');
      }

    } catch (error) {
      console.error('❌ Erreur création abonnement:', error);
      setError(error.response?.data?.detail || error.message || 'Erreur lors de la création de l\'abonnement');
    } finally {
      setLoading(false);
    }
  };

  // ✅ NOUVEAU: Créer nouvel abonnement après échec
  const createNewSubscriptionAfterFailure = async (planType) => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const response = await axios.post(`${BACKEND_URL}/subscription/new-after-failure`, 
        { plan_type: planType },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        throw new Error(response.data.message || 'Erreur création nouvel abonnement');
      }

    } catch (error) {
      console.error('❌ Erreur nouvel abonnement post-échec:', error);
      setError(error.response?.data?.detail || error.message || 'Erreur lors de la création du nouvel abonnement');
    } finally {
      setLoading(false);
    }
  };

  // ✅ NOUVEAU: Retry abonnement incomplet
  const retryIncompleteSubscription = async (subscriptionId) => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${BACKEND_URL}/subscription/retry`, 
        { 
          subscription_id: subscriptionId,
          recovery_type: 'retry'
        },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      if (response.data.retry_url) {
        window.location.href = response.data.retry_url;
      } else if (response.data.update_url) {
        window.location.href = response.data.update_url;
      } else {
        setSuccess('Récupération initiée avec succès');
        await loadSubscriptionData();
      }

    } catch (error) {
      console.error('❌ Erreur retry abonnement:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la relance de l\'abonnement');
    } finally {
      setLoading(false);
    }
  };

  const cancelSubscription = async (immediate = false) => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${BACKEND_URL}/subscription/cancel`, 
        { immediate },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      if (response.data.success) {
        setSuccess('Abonnement annulé avec succès');
        await loadSubscriptionData(); // Recharger les données
        if (onSubscriptionChange) onSubscriptionChange();
      }

    } catch (error) {
      console.error('❌ Erreur annulation:', error);
      setError(error.response?.data?.detail || 'Erreur lors de l\'annulation');
    } finally {
      setLoading(false);
    }
  };

  const reactivateSubscription = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${BACKEND_URL}/subscription/reactivate`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.data.success) {
        setSuccess('Abonnement réactivé avec succès');
        await loadSubscriptionData();
        if (onSubscriptionChange) onSubscriptionChange();
      }

    } catch (error) {
      console.error('❌ Erreur réactivation:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la réactivation');
    } finally {
      setLoading(false);
    }
  };

  // ================================================================================
  // 🎨 RENDU INTERFACE
  // ================================================================================

  if (loading && !subscriptionStatus) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        <span className="ml-3 text-gray-600">Chargement...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      
      {/* Messages d'état */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="text-red-600">❌</div>
            <div className="ml-3 text-red-700">{error}</div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <div className="text-green-600">✅</div>
            <div className="ml-3 text-green-700">{success}</div>
          </div>
        </div>
      )}

      {/* ✅ NOUVEAU: Abonnements incomplets */}
      {incompleteSubscriptions.length > 0 && (
        <IncompleteSubscriptionsAlert 
          incompleteSubscriptions={incompleteSubscriptions}
          onRetry={retryIncompleteSubscription}
          loading={loading}
        />
      )}

      {/* Statut actuel */}
      {subscriptionStatus && (
        <CurrentSubscriptionStatus 
          status={subscriptionStatus}
          onCancel={cancelSubscription}
          onReactivate={reactivateSubscription}
          loading={loading}
        />
      )}

      {/* Plans disponibles */}
      <AvailablePlans
        plans={availablePlans}
        currentStatus={subscriptionStatus}
        onCreate={createSubscription}
        onCreateNewAfterFailure={createNewSubscriptionAfterFailure}
        loading={loading}
      />

    </div>
  );
};

// ================================================================================
// 🚨 COMPOSANT ALERTE ABONNEMENTS INCOMPLETS - NOUVEAU
// ================================================================================

const IncompleteSubscriptionsAlert = ({ incompleteSubscriptions, onRetry, loading }) => {
  return (
    <div className="mb-8 bg-orange-50 border border-orange-200 rounded-xl p-6">
      <div className="flex items-start mb-4">
        <div className="text-orange-600 mr-3 mt-1">⚠️</div>
        <div>
          <h3 className="font-bold text-orange-900 mb-2">Abonnements en attente de finalisation</h3>
          <p className="text-orange-700 text-sm">
            Vous avez des abonnements qui n'ont pas pu être finalisés. Vous pouvez les relancer ci-dessous.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {incompleteSubscriptions.map((sub, index) => (
          <div key={index} className="bg-white rounded-lg p-4 border border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">{sub.plan_name}</div>
                <div className="text-sm text-gray-600">
                  {sub.amount}€/{sub.currency === 'eur' ? 'mois' : sub.currency}
                  {sub.failure_reason && ` • ${sub.failure_reason}`}
                </div>
                <div className="text-xs text-gray-500">
                  Créé le {new Date(sub.created_at).toLocaleDateString('fr-FR')}
                </div>
              </div>
              <div className="flex gap-2">
                {sub.can_retry && (
                  <button
                    onClick={() => onRetry(sub.id)}
                    disabled={loading}
                    className="px-3 py-2 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition-colors disabled:opacity-50"
                  >
                    {loading ? '⏳' : '🔄'} Relancer
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ================================================================================
// 📊 COMPOSANT STATUT ABONNEMENT ACTUEL
// ================================================================================

const CurrentSubscriptionStatus = ({ status, onCancel, onReactivate, loading }) => {
  const getStatusBadge = () => {
    if (status.trial_active) {
      return <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">🎁 Essai gratuit actif</span>;
    }

    switch (status.plan_type) {
      case 'gratuit':
        return <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">📦 Plan gratuit</span>;
      case 'pro':
        return <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">⚡ Plan Pro</span>;
      case 'premium':
        return <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">🏆 Plan Premium</span>;
      default:
        return <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">Plan inconnu</span>;
    }
  };

  const getUsageBar = () => {
    if (status.monthly_limit === Infinity) {
      return (
        <div className="text-sm text-green-600 font-medium">
          ♾️ Fiches illimitées
        </div>
      );
    }

    const percentage = (status.monthly_used / status.monthly_limit) * 100;
    const isNearLimit = percentage > 80;

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Utilisation mensuelle</span>
          <span className={`font-medium ${isNearLimit ? 'text-red-600' : 'text-gray-900'}`}>
            {status.monthly_used} / {status.monthly_limit} fiches
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              isNearLimit ? 'bg-red-500' : 'bg-purple-600'
            }`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8 shadow-sm">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Mon abonnement</h2>
          {getStatusBadge()}
        </div>
        
        {status.trial_end_date && status.trial_active && (
          <div className="text-right">
            <div className="text-sm text-gray-500">Essai expire le</div>
            <div className="text-lg font-semibold text-blue-600">
              {new Date(status.trial_end_date).toLocaleDateString('fr-FR')}
            </div>
          </div>
        )}
      </div>

      {/* Message de statut */}
      {status.message && (
        <div className={`p-4 rounded-lg mb-6 ${
          status.requires_action || status.requires_payment_action
            ? 'bg-red-50 border border-red-200 text-red-800'
            : 'bg-blue-50 border border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-center">
            <span className="text-lg mr-2">
              {status.requires_action || status.requires_payment_action ? '⚠️' : 'ℹ️'}
            </span>
            <span className="font-medium">{status.message}</span>
          </div>
        </div>
      )}

      {/* Barre d'utilisation */}
      <div className="mb-6">
        {getUsageBar()}
      </div>

      {/* Actions selon le statut */}
      <div className="flex flex-wrap gap-3">
        {status.plan_type !== 'gratuit' && (
          <>
            <button
              onClick={() => onCancel(true)}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 font-medium"
            >
              {loading ? '⏳' : '🚫'} Désabonner immédiatement
            </button>
            
            <button
              onClick={() => onCancel(false)}
              disabled={loading}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
            >
              {loading ? '⏳' : '🛑'} Annuler à la fin de période
            </button>
            
            <button
              onClick={() => onReactivate()}
              disabled={loading}
              className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
            >
              {loading ? '⏳' : '🔄'} Réactiver l'abonnement
            </button>
          </>
        )}

        {(status.payment_failed || status.requires_payment_action) && (
          <button
            onClick={() => window.open('https://billing.stripe.com/p/login/test_CUSTOMER_PORTAL', '_blank')}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
          >
            💳 Mettre à jour le paiement
          </button>
        )}
      </div>
    </div>
  );
};

// ================================================================================
// 📋 COMPOSANT PLANS DISPONIBLES - VERSION ROBUSTE
// ================================================================================

const AvailablePlans = ({ plans, currentStatus, onCreate, onCreateNewAfterFailure, loading }) => {
  const getPlanCard = (planKey, planConfig) => {
    const isCurrentPlan = currentStatus?.plan_type === planKey;
    const canUpgrade = currentStatus?.plan_type === 'gratuit' || 
                      (currentStatus?.plan_type === 'pro' && planKey === 'premium');
    
    // ✅ CORRECTION: Logique robuste pour essai et abonnement direct
    const canStartTrial = currentStatus?.can_start_trial && planKey !== 'gratuit';
    const canSubscribeDirectly = currentStatus?.can_subscribe_directly && planKey !== 'gratuit';
    const hasUsedTrial = currentStatus?.has_used_trial;
    const hasIncompleteSubscriptions = currentStatus?.has_incomplete_subscriptions;

    return (
      <div 
        key={planKey}
        className={`relative border-2 rounded-xl p-6 transition-all duration-300 ${
          planKey === 'pro' 
            ? 'border-purple-300 bg-purple-50' 
            : planKey === 'premium'
            ? 'border-yellow-300 bg-yellow-50'
            : 'border-gray-200 bg-white'
        }`}
      >
        {/* Badge recommandé */}
        {planConfig.recommended && (
          <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
            <span className="bg-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
              ⭐ Recommandé
            </span>
          </div>
        )}

        {/* Badge plan actuel */}
        {isCurrentPlan && (
          <div className="absolute -top-3 right-4">
            <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
              ✅ Plan actuel
            </span>
          </div>
        )}

        <div className="text-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{planConfig.name}</h3>
          <div className="mb-4">
            {planConfig.price === 0 ? (
              <span className="text-3xl font-bold text-gray-900">Gratuit</span>
            ) : (
              <div>
                <span className="text-3xl font-bold text-gray-900">{planConfig.price}€</span>
                <span className="text-gray-500">/mois</span>
              </div>
            )}
          </div>
        </div>

        {/* Fonctionnalités */}
        <ul className="space-y-3 mb-8">
          {planConfig.features.map((feature, index) => (
            <li key={index} className="flex items-center">
              <span className="text-green-500 mr-3">✅</span>
              <span className="text-gray-700">{feature}</span>
            </li>
          ))}
        </ul>

        {/* Boutons d'action */}
        <div className="space-y-3">
          {planKey === 'gratuit' ? (
            <div className="text-center text-gray-500">
              Plan actuel
            </div>
          ) : (
            <>
              {/* ✅ CORRECTION: Bouton essai gratuit seulement si éligible */}
              {canStartTrial && (
                <button
                  onClick={() => onCreate(planKey, true)}
                  disabled={loading || isCurrentPlan}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? '⏳ Traitement...' : `🎁 Essai gratuit 7 jours`}
                </button>
              )}

              {/* ✅ CORRECTION: Bouton abonnement direct TOUJOURS visible si possible */}
              {canSubscribeDirectly && !isCurrentPlan && (
                <button
                  onClick={() => hasIncompleteSubscriptions 
                    ? onCreateNewAfterFailure(planKey) 
                    : onCreate(planKey, false)
                  }
                  disabled={loading}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    planKey === 'premium'
                      ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                      : 'bg-purple-600 text-white hover:bg-purple-700'
                  }`}
                >
                  {loading ? '⏳ Traitement...' : 
                   hasUsedTrial && !canStartTrial ? '🔄 S\'abonner maintenant' : 
                   hasIncompleteSubscriptions ? '🆕 Nouvel abonnement' :
                   `🚀 S'abonner maintenant`}
                </button>
              )}

              {/* ✅ NOUVEAU: Message explicite pour recovery */}
              {!canStartTrial && hasUsedTrial && canSubscribeDirectly && planKey !== 'gratuit' && (
                <div className="text-center text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
                  💡 Essai gratuit déjà utilisé - Abonnez-vous directement
                </div>
              )}

              {/* Message si impossible de s'abonner */}
              {!canSubscribeDirectly && !canStartTrial && planKey !== 'gratuit' && (
                <div className="text-center text-sm text-gray-500">
                  Non disponible actuellement
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  if (!plans || Object.keys(plans).length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-500">Aucun plan disponible</div>
      </div>
    );
  }

  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Choisissez votre plan</h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Sélectionnez le plan qui correspond le mieux à vos besoins. 
          {currentStatus?.can_start_trial && ' Profitez de 7 jours d\'essai gratuit sur les plans payants !'}
          {currentStatus?.has_used_trial && !currentStatus?.can_start_trial && ' Vous pouvez vous abonner directement.'}
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {Object.entries(plans).map(([planKey, planConfig]) => 
          getPlanCard(planKey, planConfig)
        )}
      </div>

      {/* ✅ NOUVEAU: Informations recovery */}
      <div className="mt-12 bg-gray-50 rounded-xl p-6">
        <h3 className="font-bold text-gray-900 mb-4">💡 Informations importantes</h3>
        <ul className="space-y-2 text-gray-700">
          <li>• L'essai gratuit de 7 jours n'est disponible qu'une seule fois par compte</li>
          <li>• Même après un essai expiré ou échoué, vous pouvez toujours vous abonner</li>
          <li>• Aucun engagement - Annulez à tout moment</li>
          <li>• Paiement sécurisé avec Stripe</li>
          <li>• Accès immédiat à toutes les fonctionnalités du plan</li>
          <li>• Support client disponible pour tous les plans</li>
        </ul>
      </div>
    </div>
  );
};

export default SubscriptionManager;