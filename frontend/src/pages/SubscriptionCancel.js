// ================================================================================
// ECOMSIMPLY - PAGE ANNULATION ABONNEMENT APRÈS STRIPE CHECKOUT
// ================================================================================

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscription } from '../hooks/useSubscription';

const SubscriptionCancel = () => {
  const navigate = useNavigate();
  const { handleSubscriptionCancel, availablePlans } = useSubscription();

  useEffect(() => {
    // Gérer l'annulation
    handleSubscriptionCancel();
  }, [handleSubscriptionCancel]);

  const goToPlans = () => {
    navigate('/subscription');
  };

  const goToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
      <div className="max-w-lg mx-auto">
        
        {/* Carte principale d'annulation */}
        <div className="bg-white rounded-xl shadow-xl p-8 text-center mb-6">
          
          {/* Icône d'annulation */}
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 8.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>

          {/* Message d'annulation */}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Abonnement annulé
          </h1>
          
          <p className="text-lg text-gray-700 mb-6">
            Votre abonnement n'a pas été finalisé. Aucun montant n'a été débité.
          </p>

          {/* Raisons possibles */}
          <div className="bg-orange-50 rounded-lg p-6 mb-6 text-left">
            <h3 className="font-semibold text-orange-900 mb-3">Cela peut être dû à :</h3>
            <ul className="space-y-2 text-orange-800">
              <li className="flex items-start">
                <span className="text-orange-500 mr-2 mt-1">•</span>
                Annulation volontaire du processus de paiement
              </li>
              <li className="flex items-start">
                <span className="text-orange-500 mr-2 mt-1">•</span>
                Problème temporaire avec la carte de paiement
              </li>
              <li className="flex items-start">
                <span className="text-orange-500 mr-2 mt-1">•</span>
                Fermeture accidentelle de la fenêtre de paiement
              </li>
              <li className="flex items-start">
                <span className="text-orange-500 mr-2 mt-1">•</span>
                Problème technique temporaire
              </li>
            </ul>
          </div>

          {/* Options disponibles */}
          <div className="space-y-4">
            <button
              onClick={goToPlans}
              className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              🔄 Réessayer l'abonnement
            </button>
            
            <button
              onClick={goToDashboard}
              className="w-full bg-gray-100 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200"
            >
              📊 Retour au tableau de bord
            </button>
          </div>
        </div>

        {/* Avantages manqués */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4 text-center">
            💎 Ce que vous manquez avec le plan gratuit
          </h3>
          
          <div className="grid grid-cols-1 gap-3">
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-purple-600 text-sm">⚡</span>
              </div>
              <div>
                <div className="font-medium text-gray-900">IA avancée GPT-4o</div>
                <div className="text-sm text-gray-600">Génération plus précise et créative</div>
              </div>
            </div>
            
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-blue-600 text-sm">🖼️</span>
              </div>
              <div>
                <div className="font-medium text-gray-900">Images haute qualité</div>
                <div className="text-sm text-gray-600">Photos professionnelles générées par IA</div>
              </div>
            </div>
            
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-green-600 text-sm">📈</span>
              </div>
              <div>
                <div className="font-medium text-gray-900">Plus de fiches</div>
                <div className="text-sm text-gray-600">Jusqu'à 100 fiches/mois (Plan gratuit: 1 fiche)</div>
              </div>
            </div>
            
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-yellow-600 text-sm">🎁</span>
              </div>
              <div>
                <div className="font-medium text-gray-900">Essai gratuit 7 jours</div>
                <div className="text-sm text-gray-600">Testez toutes les fonctionnalités sans engagement</div>
              </div>
            </div>
          </div>
        </div>

        {/* Support */}
        <div className="text-center">
          <p className="text-gray-500 text-sm mb-2">
            Des questions sur nos plans tarifaires ?
          </p>
          <div className="space-x-4">
            <a 
              href="mailto:support@ecomsimply.com" 
              className="text-purple-600 hover:text-purple-700 text-sm"
            >
              📧 Support email
            </a>
            <span className="text-gray-300">•</span>
            <a 
              href="/help" 
              className="text-purple-600 hover:text-purple-700 text-sm"
            >
              ❓ Centre d'aide
            </a>
          </div>
        </div>

      </div>
    </div>
  );
};

export default SubscriptionCancel;