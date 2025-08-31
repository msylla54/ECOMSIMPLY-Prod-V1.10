/**
 * 🚀 ECOMSIMPLY - Composants d'État UI Cohérents
 * Gestion standardisée des états loading/success/error/disabled
 */

import React from 'react';
import { isFeatureEnabled } from '../../lib/apiClient';

// ✅ Composant Loading Spinner
export const LoadingSpinner = ({ size = 'medium', color = 'blue' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6', 
    large: 'w-8 h-8'
  };

  const colorClasses = {
    blue: 'border-blue-600 border-t-transparent',
    white: 'border-white border-t-transparent',
    gray: 'border-gray-600 border-t-transparent'
  };

  return (
    <div 
      className={`animate-spin rounded-full border-2 ${sizeClasses[size]} ${colorClasses[color]}`}
      role="status"
      aria-label="Chargement en cours"
    >
      <span className="sr-only">Chargement...</span>
    </div>
  );
};

// ✅ Composant Button avec États
export const StateButton = ({ 
  children, 
  loading = false, 
  disabled = false, 
  variant = 'primary',
  size = 'medium',
  featureRequired = null,
  onClick,
  className = '',
  ...props 
}) => {
  // Vérifier si la feature est disponible
  const featureAvailable = featureRequired ? isFeatureEnabled(featureRequired) : true;
  const isDisabled = disabled || loading || !featureAvailable;

  const baseClasses = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2";
  
  const variantClasses = {
    primary: isDisabled 
      ? "bg-gray-300 text-gray-500 cursor-not-allowed" 
      : "bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500",
    secondary: isDisabled
      ? "bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed"
      : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 focus:ring-gray-500",
    success: isDisabled
      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
      : "bg-green-600 hover:bg-green-700 text-white focus:ring-green-500",
    danger: isDisabled
      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
      : "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500",
    warning: isDisabled
      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
      : "bg-orange-500 hover:bg-orange-600 text-white focus:ring-orange-500"
  };

  const sizeClasses = {
    small: "px-3 py-1.5 text-sm",
    medium: "px-4 py-2 text-base",
    large: "px-6 py-3 text-lg"
  };

  const handleClick = (e) => {
    if (isDisabled || loading) return;
    onClick?.(e);
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={isDisabled}
      onClick={handleClick}
      {...props}
    >
      {loading && <LoadingSpinner size="small" color={variant === 'primary' ? 'white' : 'gray'} />}
      <span className={loading ? 'ml-2' : ''}>{children}</span>
      {!featureAvailable && (
        <span className="ml-2 text-xs opacity-75">ENV manquante</span>
      )}
    </button>
  );
};

// ✅ Composant Success Message
export const SuccessMessage = ({ message, onClose, autoHide = true, duration = 5000 }) => {
  React.useEffect(() => {
    if (autoHide && onClose) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [autoHide, duration, onClose]);

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-green-500 mr-2">✅</span>
            <span>{message}</span>
          </div>
          {onClose && (
            <button 
              onClick={onClose}
              className="text-green-500 hover:text-green-700 ml-4"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ✅ Composant Error Message
export const ErrorMessage = ({ message, onClose, onRetry }) => {
  return (
    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-red-500 mr-2">❌</span>
          <span>{message}</span>
        </div>
        <div className="flex items-center space-x-2">
          {onRetry && (
            <button 
              onClick={onRetry}
              className="text-red-600 hover:text-red-800 text-sm underline"
            >
              Réessayer
            </button>
          )}
          {onClose && (
            <button 
              onClick={onClose}
              className="text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ✅ Composant Loading State avec Skeleton
export const LoadingState = ({ lines = 3, height = 'h-4' }) => {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className={`bg-gray-200 rounded ${height} w-full`}></div>
      ))}
    </div>
  );
};

// ✅ Composant Empty State
export const EmptyState = ({ 
  icon = "📭", 
  title = "Aucune donnée", 
  description = "Il n'y a rien à afficher pour le moment.",
  action = null 
}) => {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      {action}
    </div>
  );
};

// ✅ Composant Feature Disabled Warning
export const FeatureDisabledWarning = ({ featureName, onClose }) => {
  return (
    <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-yellow-500 mr-2">⚠️</span>
          <span>
            La fonctionnalité "{featureName}" est désactivée. 
            Variable d'environnement REACT_APP_BACKEND_URL manquante.
          </span>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="text-yellow-500 hover:text-yellow-700"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

// ✅ Hook pour gérer l'état UI complet
export const useUIState = (initialState = {}) => {
  const [state, setState] = React.useState({
    loading: false,
    success: false,
    error: null,
    data: null,
    ...initialState
  });

  const setLoading = (loading) => setState(prev => ({ 
    ...prev, 
    loading, 
    success: false, 
    error: null 
  }));

  const setSuccess = (data = null, message = null) => setState(prev => ({ 
    ...prev, 
    loading: false, 
    success: true, 
    error: null, 
    data,
    successMessage: message
  }));

  const setError = (error) => setState(prev => ({ 
    ...prev, 
    loading: false, 
    success: false, 
    error 
  }));

  const reset = () => setState({
    loading: false,
    success: false,
    error: null,
    data: null,
    ...initialState
  });

  return {
    ...state,
    setLoading,
    setSuccess,
    setError,
    reset
  };
};

// ✅ Composant Modal avec État UI
export const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  loading = false,
  preventCloseOnBackdrop = false 
}) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !preventCloseOnBackdrop && !loading) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div 
        className="fixed inset-0" 
        onClick={handleBackdropClick}
      ></div>
      <div className="bg-white rounded-lg shadow-xl z-10 w-full max-w-md mx-4 max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
          {!loading && (
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="large" />
              <span className="ml-3">Traitement en cours...</span>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
};

export default {
  LoadingSpinner,
  StateButton,
  SuccessMessage,
  ErrorMessage,
  LoadingState,
  EmptyState,
  FeatureDisabledWarning,
  useUIState,
  Modal
};