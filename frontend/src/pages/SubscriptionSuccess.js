// ================================================================================
// ECOMSIMPLY - PAGE SUCCÈS ABONNEMENT APRÈS STRIPE CHECKOUT
// ================================================================================

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscription } from '../hooks/useSubscription';

const SubscriptionSuccess = () => {
  const navigate = useNavigate();
  const { handleSubscriptionSuccess, subscriptionStatus, loading } = useSubscription();
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const processSuccess = async () => {
      try {
        setProcessing(true);
        
        // Gérer le succès de l'abonnement
        await handleSubscriptionSuccess();
        
        // Attendre un peu pour que les données se synchronisent
        setTimeout(() => {
          setProcessing(false);
        }, 2000);
        
      } catch (error) {
        console.error('❌ Erreur traitement succès:', error);
        setProcessing(false);
      }
    };

    processSuccess();
  }, [handleSubscriptionSuccess]);

  const goToDashboard = () => {
    navigate('/dashboard');
  };

  if (processing || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Finalisation de votre abonnement...
          </h2>
          <p className="text-gray-600">
            Nous configurons votre compte premium. Cela ne prendra qu'un instant.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-lg mx-auto">
        
        {/* Carte principale de succès */}
        <div className="bg-white rounded-xl shadow-xl p-8 text-center mb-6">
          
          {/* Icône de succès */}
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          {/* Message de succès */}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🎉 Félicitations !
          </h1>
          
          <p className="text-xl text-gray-700 mb-6">
            Votre abonnement a été activé avec succès
          </p>

          {/* Détails de l'abonnement */}
          {subscriptionStatus && (
            <div className="bg-purple-50 rounded-lg p-6 mb-6">
              <h3 className="font-semibold text-purple-900 mb-3">Détails de votre abonnement</h3>
              
              <div className="space-y-2 text-left">
                <div className="flex justify-between">
                  <span className="text-gray-600">Plan :</span>
                  <span className="font-semibold text-purple-700 capitalize">
                    {subscriptionStatus.plan_type}
                  </span>
                </div>
                
                {subscriptionStatus.trial_active && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Essai gratuit :</span>
                    <span className="font-semibold text-blue-700">
                      Jusqu'au {new Date(subscriptionStatus.trial_end_date).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Fiches mensuelles :</span>
                  <span className="font-semibold text-gray-900">
                    {subscriptionStatus.monthly_limit === Infinity ? 'Illimitées' : subscriptionStatus.monthly_limit}
                  </span>
                </div>
                
                {subscriptionStatus.next_billing_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Prochaine facture :</span>
                    <span className="font-semibold text-gray-900">
                      {new Date(subscriptionStatus.next_billing_date).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Fonctionnalités débloquées */}
          <div className="bg-green-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-green-900 mb-3">🔓 Fonctionnalités débloquées</h3>
            
            <ul className="space-y-2 text-left text-green-800">
              {subscriptionStatus?.plan_type === 'pro' && (
                <>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Génération de 100 fiches par mois
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    IA avancée avec GPT-4o
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Images haute qualité
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Export multi-format
                  </li>
                </>
              )}
              
              {subscriptionStatus?.plan_type === 'premium' && (
                <>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Fiches illimitées
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Toutes les fonctionnalités Pro
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Analytics avancés
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Support dédié
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    Intégrations e-commerce
                  </li>
                </>
              )}
            </ul>
          </div>

          {/* Bouton d'action */}
          <button
            onClick={goToDashboard}
            className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            🚀 Commencer à utiliser ECOMSIMPLY
          </button>
        </div>

        {/* Carte informations supplémentaires */}
        <div className="bg-white rounded-lg shadow-lg p-6 text-center">
          <h3 className="font-semibold text-gray-900 mb-3">📧 Prochaines étapes</h3>
          <ul className="text-left text-gray-600 space-y-2">
            <li className="flex items-start">
              <span className="text-purple-500 mr-2 mt-1">•</span>
              Vous recevrez un email de confirmation dans quelques minutes
            </li>
            <li className="flex items-start">
              <span className="text-purple-500 mr-2 mt-1">•</span>
              Accédez à votre tableau de bord pour commencer
            </li>
            <li className="flex items-start">
              <span className="text-purple-500 mr-2 mt-1">•</span>
              Consultez nos guides d'utilisation
            </li>
            {subscriptionStatus?.trial_active && (
              <li className="flex items-start">
                <span className="text-blue-500 mr-2 mt-1">•</span>
                <span className="text-blue-700">
                  Profitez de votre essai gratuit de 3 jours
                </span>
              </li>
            )}
          </ul>
        </div>

        {/* Support */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            Une question ? Contactez notre support à{' '}
            <a href="mailto:support@ecomsimply.com" className="text-purple-600 hover:text-purple-700">
              support@ecomsimply.com
            </a>
          </p>
        </div>

      </div>
    </div>
  );
};

export default SubscriptionSuccess;