// ================================================================================
// ECOMSIMPLY - ACCESSIBILITY UTILITIES AWWWARDS
// Utilitaires pour l'accessibilité et focus management
// ================================================================================

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

// Focus Ring utility
export const FocusRing = ({ children, className = "" }) => {
  return (
    <div className={cn(
      "focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 focus-within:ring-offset-background rounded-lg transition-all duration-2",
      className
    )}>
      {children}
    </div>
  );
};

// Skip to content link
export const SkipToContent = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 transition-all duration-2"
    >
      Aller au contenu principal
    </a>
  );
};

// Accessible button avec states
export const AccessibleButton = ({ 
  children, 
  onClick, 
  disabled = false, 
  ariaLabel,
  className = "",
  loading = false,
  ...props 
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-disabled={disabled || loading}
      className={cn(
        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "transition-all duration-2 ease-premium",
        className
      )}
      {...props}
    >
      {loading && (
        <span className="sr-only">Chargement en cours...</span>
      )}
      {children}
    </button>
  );
};

// Live region pour les annonces
export const LiveRegion = ({ message, level = "polite", className = "" }) => {
  const regionRef = useRef(null);

  useEffect(() => {
    if (message && regionRef.current) {
      // Clear and set message to ensure screen reader announces it
      regionRef.current.textContent = '';
      setTimeout(() => {
        regionRef.current.textContent = message;
      }, 100);
    }
  }, [message]);

  return (
    <div
      ref={regionRef}
      aria-live={level}
      aria-atomic="true"
      className={cn("sr-only", className)}
    />
  );
};

// Modal avec gestion focus
export const AccessibleModal = ({ 
  isOpen, 
  onClose, 
  title, 
  children,
  className = "" 
}) => {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Store currently focused element
      previousFocusRef.current = document.activeElement;
      
      // Focus modal
      setTimeout(() => {
        if (modalRef.current) {
          modalRef.current.focus();
        }
      }, 100);

      // Trap focus in modal
      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          onClose();
        }
        
        if (e.key === 'Tab') {
          const focusableElements = modalRef.current?.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          
          if (focusableElements && focusableElements.length > 0) {
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (e.shiftKey && document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        
        // Restore focus
        if (previousFocusRef.current) {
          previousFocusRef.current.focus();
        }
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        className={cn(
          "bg-card rounded-xl border border-border shadow-soft-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
          className
        )}
        tabIndex={-1}
      >
        <div className="p-6">
          <h2 id="modal-title" className="text-xl font-bold text-foreground mb-4">
            {title}
          </h2>
          {children}
        </div>
      </div>
    </div>
  );
};

// Hook pour détecter prefers-reduced-motion
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};