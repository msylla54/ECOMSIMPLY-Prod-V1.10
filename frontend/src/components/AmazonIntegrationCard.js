import React from 'react';

/**
 * Composant réutilisable pour la gestion Amazon SP-API
 * Affiche l'état de connexion et gère les actions de connexion/déconnexion
 */
const AmazonIntegrationCard = ({
  amazonConnectionStatus,
  selectedPlatform,
  onConnect,
  onDisconnect,
  showConfirmDialog = true,
  size = 'normal' // 'small', 'normal', 'large'
}) => {
  
  const handleClick = async () => {
    if (amazonConnectionStatus === 'connected') {
      // Si connecté, proposer la déconnexion
      if (showConfirmDialog) {
        if (confirm('Voulez-vous vraiment déconnecter votre compte Amazon ?')) {
          await onDisconnect();
        }
      } else {
        await onDisconnect();
      }
    } else {
      // Si pas connecté (none, revoked, error), lancer la connexion
      await onConnect();
    }
  };

  const getStatusDisplay = () => {
    switch (amazonConnectionStatus) {
      case 'connected':
        return {
          text: 'Connecté',
          icon: '✅',
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200'
        };
      case 'revoked':
        return {
          text: 'Déconnecté',
          icon: '❌',
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200'
        };
      case 'error':
        return {
          text: 'Erreur',
          icon: '⚠️',
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200'
        };
      case 'pending':
        return {
          text: 'En attente',
          icon: '⏳',
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200'
        };
      default: // 'none'
        return {
          text: 'Non connecté',
          icon: '🔌',
          color: 'text-gray-500',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200'
        };
    }
  };

  const getButtonText = () => {
    if (selectedPlatform === 'amazon') {
      return amazonConnectionStatus === 'connected' ? 'Déconnexion...' : 'Connexion...';
    }
    
    if (amazonConnectionStatus === 'connected') {
      return 'Déconnecter';
    } else if (amazonConnectionStatus === 'revoked') {
      return 'Reconnecter';
    } else {
      return 'Connecter';
    }
  };

  const getButtonStyle = () => {
    if (amazonConnectionStatus === 'connected') {
      return 'bg-red-600 hover:bg-red-700 text-white';
    } else {
      return 'bg-green-600 hover:bg-green-700 text-white';
    }
  };

  const status = getStatusDisplay();
  
  // Styles adaptatifs selon la taille
  const sizeClasses = {
    small: {
      container: 'p-3',
      icon: 'text-lg',
      title: 'text-sm font-medium',
      description: 'text-xs',
      button: 'px-3 py-1 text-xs',
      statusText: 'text-xs'
    },
    normal: {
      container: 'p-4',
      icon: 'text-2xl',
      title: 'text-base font-medium',
      description: 'text-sm',
      button: 'px-4 py-2 text-sm',
      statusText: 'text-sm'
    },
    large: {
      container: 'p-6',
      icon: 'text-3xl',
      title: 'text-lg font-medium',
      description: 'text-base',
      button: 'px-6 py-3 text-base',
      statusText: 'text-base'
    }
  };

  const currentSize = sizeClasses[size];

  return (
    <div className={`bg-white border ${status.borderColor} rounded-lg ${currentSize.container} transition-all duration-200 hover:shadow-md`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={currentSize.icon}>📦</div>
          <div>
            <h4 className={`text-gray-900 ${currentSize.title}`}>Amazon</h4>
            <p className={`text-gray-600 ${currentSize.description}`}>
              SP-API Marketplace
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Status Badge */}
          <div className={`${status.bgColor} ${status.borderColor} border rounded-full px-3 py-1 flex items-center space-x-1`}>
            <span className="text-sm">{status.icon}</span>
            <span className={`${status.color} font-medium ${currentSize.statusText}`}>
              {status.text}
            </span>
          </div>
          
          {/* Action Button */}
          <button
            onClick={handleClick}
            disabled={selectedPlatform === 'amazon'}
            className={`${getButtonStyle()} rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${currentSize.button}`}
          >
            {getButtonText()}
          </button>
        </div>
      </div>
      
      {/* Status Description */}
      {amazonConnectionStatus === 'revoked' && (
        <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start">
            <div className="text-lg mr-2">⚠️</div>
            <div>
              <p className="text-sm text-yellow-700">
                Connexion révoquée. Pour republier sur Amazon, reconnectez-vous.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {amazonConnectionStatus === 'error' && (
        <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-start">
            <div className="text-lg mr-2">❌</div>
            <div>
              <p className="text-sm text-red-700">
                Erreur de connexion. Essayez de vous reconnecter.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {amazonConnectionStatus === 'connected' && (
        <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-start">
            <div className="text-lg mr-2">✅</div>
            <div>
              <p className="text-sm text-green-700">
                Connexion active. Prêt pour la publication automatique.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AmazonIntegrationCard;