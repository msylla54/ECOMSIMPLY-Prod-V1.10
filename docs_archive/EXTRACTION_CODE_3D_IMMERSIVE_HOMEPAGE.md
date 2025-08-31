# 🎯 EXTRACTION CODE 3D IMMERSIVE HOMEPAGE - ECOMSIMPLY

## 📋 RÉSUMÉ DE L'IMPLÉMENTATION

Cette extraction contient tous les composants, hooks et configurations nécessaires pour créer une homepage 3D immersive avec React, Three.js, et Framer Motion. L'implémentation est entièrement sécurisée avec des fallbacks gracieux et une détection automatique des capacités device.

## 🏗️ ARCHITECTURE DES COMPOSANTS

### 1. COMPOSANT PRINCIPAL HERO 3D - `HeroScene3D.js`
```javascript
// ================================================================================
// ECOMSIMPLY - COMPOSANT 3D HERO SCENE - VERSION WORKFLOW IMMERSIVE
// ================================================================================

import * as React from 'react';
import { Suspense, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import WorkflowAnimation3D from './WorkflowAnimation3D';

// ================================================================================
// 🔒 GUARDS CLIENT-SIDE ET DÉTECTION WEBGL SÉCURISÉE
// ================================================================================

const isClient = typeof window !== 'undefined';

const detectWebGLSupport = () => {
  if (!isClient) return false;
  
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return false;
    
    // Test basique des capacités WebGL
    const renderer = gl.getParameter(gl.RENDERER);
    const vendor = gl.getParameter(gl.VENDOR);
    
    // Rejeter les implémentations software-only connues
    if (renderer && (
      renderer.toLowerCase().includes('software') ||
      renderer.toLowerCase().includes('mesa') ||
      vendor.toLowerCase().includes('microsoft')
    )) {
      return false;
    }
    
    return true;
  } catch (e) {
    console.warn('WebGL detection failed:', e);
    return false;
  }
};

const hasWebGL = () => {
  if (!isClient) return false;
  return detectWebGLSupport();
};

const isLowEndDevice = () => {
  if (!isClient) return true; // Safe default pour SSR
  
  // Détection basique de device low-end
  const isSlowDevice = navigator.hardwareConcurrency <= 2;
  const isSlowConnection = navigator.connection && navigator.connection.effectiveType === 'slow-2g';
  const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  return isSlowDevice || isSlowConnection || isReducedMotion;
};

// ================================================================================
// 🎭 FALLBACK GRACIEUX WORKFLOW
// ================================================================================

const HeroFallback = ({ className }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
      className={`${className} bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden`}
    >
      {/* Animation CSS du workflow */}
      <div className="absolute inset-0">
        {/* Étape 1: Scraping */}
        <motion.div
          className="absolute top-1/2 left-1/4 transform -translate-x-1/2 -translate-y-1/2"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            repeatType: "reverse",
          }}
        >
          <div className="w-20 h-20 bg-cyan-500 rounded-full opacity-70 flex items-center justify-center">
            <div className="text-white font-bold text-xs">WEB</div>
          </div>
        </motion.div>

        {/* Étape 2: IA Optimization */}
        <motion.div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            repeatType: "reverse",
            delay: 1,
          }}
        >
          <div className="w-24 h-24 bg-purple-500 rounded-full opacity-70 flex items-center justify-center">
            <div className="text-white font-bold text-xs">IA</div>
          </div>
        </motion.div>

        {/* Étape 3: Publication */}
        <motion.div
          className="absolute top-1/2 right-1/4 transform translate-x-1/2 -translate-y-1/2"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            repeatType: "reverse",
            delay: 2,
          }}
        >
          <div className="w-20 h-20 bg-pink-500 rounded-full opacity-70 flex items-center justify-center">
            <div className="text-white font-bold text-xs">SHOP</div>
          </div>
        </motion.div>

        {/* Flux de connexion */}
        <motion.div
          className="absolute top-1/2 left-1/4 right-1/4 h-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 opacity-50"
          animate={{
            opacity: [0.2, 0.8, 0.2],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            repeatType: "reverse",
          }}
        />

        {/* Particules flottantes */}
        {[...Array(15)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-white rounded-full opacity-30"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            animate={{
              x: Math.random() * (window.innerWidth || 1920),
              y: Math.random() * (window.innerHeight || 1080),
            }}
            transition={{
              duration: 8 + Math.random() * 4,
              repeat: Infinity,
              repeatType: "reverse",
            }}
          />
        ))}
      </div>

      {/* Overlay gradient animé */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-pink-600/20"
        animate={{
          background: [
            'linear-gradient(45deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))',
            'linear-gradient(225deg, rgba(139, 92, 246, 0.2), rgba(6, 182, 212, 0.2))',
            'linear-gradient(45deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))',
          ],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          repeatType: "reverse",
        }}
      />
    </motion.div>
  );
};

// ================================================================================
// 🎯 COMPOSANT PRINCIPAL HERO SCENE 3D - VERSION DURCIE
// ================================================================================

const HeroScene3D = ({ className, children, fallback = false }) => {
  const [webGLSupported, setWebGLSupported] = useState(null);
  const [shouldUse3D, setShouldUse3D] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Guard client-side seulement
    if (!isClient) {
      setShouldUse3D(false);
      return;
    }

    try {
      // Détection progressive avec error handling
      const hasWebGLSupport = hasWebGL();
      const isLowEnd = isLowEndDevice();
      
      setWebGLSupported(hasWebGLSupport);
      setShouldUse3D(hasWebGLSupport && !isLowEnd && !fallback);
    } catch (err) {
      console.warn('Error during 3D capability detection:', err);
      setError(err.message);
      setWebGLSupported(false);
      setShouldUse3D(false);
    }
  }, [fallback]);

  // Error boundary pour les erreurs 3D
  const handleCanvasError = (error) => {
    console.error('Canvas error detected:', error);
    setError(error.message || 'Canvas rendering error');
    setShouldUse3D(false);
  };

  // Loading state
  if (shouldUse3D === null) {
    return (
      <div className={`${className} bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="w-8 h-8 border-2 border-white border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
        {children}
      </div>
    );
  }

  // Utiliser 3D seulement si supporté et aucune erreur
  if (shouldUse3D && !error && isClient) {
    return (
      <div className={`${className} relative`}>
        <Suspense fallback={<HeroFallback className="absolute inset-0" />}>
          <WorkflowAnimation3D
            className="absolute inset-0"
            fallback={false}
          />
        </Suspense>
        <div className="relative z-10">
          {children}
        </div>
      </div>
    );
  }

  // Fallback gracieux pour tous les autres cas
  return (
    <div className={`${className} relative`}>
      <HeroFallback className="absolute inset-0" />
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default HeroScene3D;
```

### 2. COMPOSANT SECTION HERO 3D - `Hero3DSection.js`
```javascript
// ================================================================================
// ECOMSIMPLY - HERO 3D SECTION IMMERSIVE - VERSION COMPLETE SÉCURISÉE
// ================================================================================

import * as React from 'react';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import HeroScene3D from './HeroScene3D';
import { AnimatedButton, FadeInWhenVisible, StaggerContainer, StaggerItem } from './MotionComponents';
import { use3DCapabilities, useAnimationLevel } from '../hooks/useDeviceCapabilities';

// ================================================================================
// 🌟 COMPOSANT HERO 3D IMMERSIF
// ================================================================================

const Hero3DSection = ({ 
  onShowTrialPlanSelection, 
  currentLanguage = 'fr',
  PLATFORM_CONFIG = {},
  className = '' 
}) => {
  const navigate = useNavigate();
  const { canUse3D, shouldUse3D, loading } = use3DCapabilities();
  const animationLevel = useAnimationLevel();
  
  // États locaux
  const [showBanner, setShowBanner] = useState(true);
  const [heroLoaded, setHeroLoaded] = useState(false);

  // Configuration des traductions locales (simplifiées pour la section hero)
  const heroTranslations = {
    fr: {
      newFeature: "🎉 NOUVEAU ! IA Premium + Analyse SEO + Affiliation",
      commissionRate: "commission",
      freeTrialBanner: `GRATUIT ${PLATFORM_CONFIG.FREE_TRIAL_DAYS || 7} jours`,
      heroMainTitle: "IA Premium",
      heroSubTitle: "pour Fiches Produits",
      visionIntro: "Imaginez…",
      visionText: "Une IA qui veille sur votre boutique",
      vision24h: "24h/24",
      demoButtonText: "🚀 Lancer la Démo",
      trialButtonText: "🎁 Essai Gratuit 7 Jours",
      watchDemoText: "🎥 Voir la Démo"
    },
    en: {
      newFeature: "🎉 NEW! Premium AI + SEO Analysis + Affiliate",
      commissionRate: "commission per sale",
      freeTrialBanner: `FREE ${PLATFORM_CONFIG.FREE_TRIAL_DAYS || 7} days`,
      heroMainTitle: "Premium AI",
      heroSubTitle: "for Product Sheets",
      visionIntro: "Imagine…",
      visionText: "An AI watching over your store",
      vision24h: "24/7",
      demoButtonText: "🚀 Launch Demo",
      trialButtonText: "🎁 Free 7-Day Trial",
      watchDemoText: "🎥 Watch Demo"
    }
  };

  const t = (key) => heroTranslations[currentLanguage]?.[key] || heroTranslations.fr[key] || key;

  // Gestion du chargement
  useEffect(() => {
    const timer = setTimeout(() => setHeroLoaded(true), 500);
    return () => clearTimeout(timer);
  }, []);

  // Handler pour le bouton démo principal
  const handleDemoClick = () => {
    console.log('🎯 Hero Demo button clicked');
    navigate('/demo');
  };

  // Handler pour l'essai gratuit
  const handleTrialClick = () => {
    console.log('🎯 Hero Trial button clicked');
    if (onShowTrialPlanSelection) {
      onShowTrialPlanSelection();
    } else {
      // Fallback
      navigate('/demo');
    }
  };

  // Configuration des animations selon les capacités
  const getAnimationConfig = () => {
    switch (animationLevel) {
      case 'full':
        return {
          initial: { opacity: 0, y: 50 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }
        };
      case 'reduced':
        return {
          initial: { opacity: 0 },
          animate: { opacity: 1 },
          transition: { duration: 0.4 }
        };
      default:
        return {}; // Pas d'animation
    }
  };

  // Rendu du banner de notification
  const NotificationBanner = () => (
    <FadeInWhenVisible>
      <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white py-3 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-green-600/50 to-emerald-600/50"></div>
        <div className="relative z-10 flex items-center justify-center space-x-2 text-sm md:text-base font-medium">
          <motion.span 
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            🎉
          </motion.span>
          
          {/* Mobile version */}
          <span className="block md:hidden text-center">
            {t('newFeature')}: {PLATFORM_CONFIG.PREMIUM_COMMISSION_RATE || 15}% {t('commissionRate')}
          </span>
          
          {/* Desktop version */}
          <span className="hidden md:block text-center">
            {t('newFeature')}: {PLATFORM_CONFIG.PREMIUM_COMMISSION_RATE || 15}% {t('commissionRate')}
          </span>
          
          <div className="hidden md:flex items-center space-x-1 ml-4">
            <span className="text-yellow-200 text-xs bg-yellow-500/20 px-2 py-1 rounded-full animate-pulse">
              {t('freeTrialBanner')}
            </span>
          </div>
          
          {/* Close button */}
          <button
            onClick={() => setShowBanner(false)}
            className="ml-4 text-white/80 hover:text-white transition-colors"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>
      </div>
    </FadeInWhenVisible>
  );

  // Rendu du contenu Hero 3D
  const HeroContent = () => (
    <div className="relative z-10 flex items-center justify-center min-h-screen px-4 py-20">
      <div className="text-center max-w-6xl mx-auto">
        
        {/* Titre principal avec animation staggerée */}
        <StaggerContainer className="mb-8">
          <StaggerItem>
            <motion.h1 
              className="text-4xl sm:text-5xl lg:text-7xl tracking-tight font-extrabold text-white mb-6"
              {...getAnimationConfig()}
            >
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400">
                {t('heroMainTitle')}
              </span>
              <br />
              <span className="text-white">{t('heroSubTitle')}</span>
            </motion.h1>
          </StaggerItem>

          <StaggerItem>
            <div className="mt-6 max-w-4xl mx-auto mb-10">
              <motion.p 
                className="text-xl sm:text-2xl text-gray-200 leading-relaxed mb-6"
                {...getAnimationConfig()}
              >
                <span className="inline-block text-3xl font-bold text-cyan-400 animate-pulse">
                  {t('visionIntro')}
                </span>
                <br/>
                <span className="text-lg">{t('visionText')}</span>
                <span className="inline-block bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-bold text-2xl ml-2">
                  {t('vision24h')}
                </span>.
              </motion.p>
            </div>
          </StaggerItem>
        </StaggerContainer>

        {/* Boutons CTA avec animations */}
        <StaggerContainer delayChildren={0.6}>
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            
            {/* Bouton principal Démo */}
            <StaggerItem>
              <AnimatedButton
                onClick={handleDemoClick}
                variant="primary"
                className="px-8 py-4 text-lg font-semibold rounded-full shadow-2xl transform hover:scale-105 transition-all duration-300"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 20px 40px rgba(102, 126, 234, 0.4)'
                }}
              >
                {t('demoButtonText')}
              </AnimatedButton>
            </StaggerItem>

            {/* Bouton essai gratuit */}
            <StaggerItem>
              <AnimatedButton
                onClick={handleTrialClick}
                variant="outline"
                className="px-8 py-4 text-lg font-semibold rounded-full border-2 border-white/30 text-white backdrop-blur-sm bg-white/10 hover:bg-white/20 transition-all duration-300"
              >
                {t('trialButtonText')}
              </AnimatedButton>
            </StaggerItem>

            {/* Bouton watch demo */}
            <StaggerItem>
              <motion.button
                onClick={() => {
                  // Scroll vers la section démo
                  document.getElementById('demo-section')?.scrollIntoView({ 
                    behavior: 'smooth' 
                  });
                }}
                className="px-6 py-3 text-white/80 hover:text-white font-medium transition-colors duration-300 flex items-center space-x-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span>{t('watchDemoText')}</span>
                <motion.div
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  →
                </motion.div>
              </motion.button>
            </StaggerItem>
          </div>
        </StaggerContainer>

        {/* Indicateur de scroll (optionnel) */}
        {animationLevel === 'full' && (
          <motion.div
            className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5, duration: 0.8 }}
          >
            <motion.div
              className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <motion.div
                className="w-1 h-3 bg-white/60 rounded-full mt-2"
                animate={{ y: [0, 12, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );

  // Rendu conditionnel selon les capacités
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="w-12 h-12 border-4 border-white border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Banner de notification */}
      {showBanner && <NotificationBanner />}

      {/* Section Hero avec 3D ou Fallback */}
      <HeroScene3D
        className="min-h-screen relative"
        fallback={!canUse3D || animationLevel === 'minimal'}
      >
        <HeroContent />
      </HeroScene3D>
    </div>
  );
};

export default Hero3DSection;
```

### 3. COMPOSANTS MOTION RÉUTILISABLES - `MotionComponents.js`
```javascript
// ================================================================================
// ECOMSIMPLY - COMPOSANTS MOTION RÉUTILISABLES - VERSION ACCESSIBLE SÉCURISÉE
// ================================================================================

import * as React from 'react';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';

// ================================================================================
// 🎯 UTILITAIRES MOTION
// ================================================================================

// Respecte les préférences utilisateur pour reduced-motion
const getAnimationProps = (animationProps, fallbackProps = {}) => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (prefersReducedMotion) {
    return {
      initial: false,
      animate: false,
      transition: { duration: 0 },
      ...fallbackProps
    };
  }
  
  return animationProps;
};

// ================================================================================
// 🌟 ANIMATIONS FADE IN
// ================================================================================

export const FadeInWhenVisible = ({ children, delay = 0, direction = 'up', className = '' }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const directions = {
    up: { y: 50, x: 0 },
    down: { y: -50, x: 0 },
    left: { y: 0, x: 50 },
    right: { y: 0, x: -50 }
  };

  const animationProps = getAnimationProps({
    initial: { 
      opacity: 0, 
      ...directions[direction],
      scale: 0.95
    },
    animate: isInView ? { 
      opacity: 1, 
      y: 0, 
      x: 0,
      scale: 1
    } : {},
    transition: { 
      duration: 0.6, 
      delay: delay,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  });

  return (
    <motion.div ref={ref} className={className} {...animationProps}>
      {children}
    </motion.div>
  );
};

// ================================================================================
// 🎨 ANIMATIONS PARALLAX
// ================================================================================

export const ParallaxContainer = ({ children, speed = 0.5, className = '' }) => {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start']
  });

  const y = useTransform(scrollYProgress, [0, 1], ['0%', `${speed * 100}%`]);

  const animationProps = getAnimationProps({
    style: { y }
  });

  return (
    <motion.div ref={ref} className={className} {...animationProps}>
      {children}
    </motion.div>
  );
};

// ================================================================================
// 🎯 ANIMATION STAGGER
// ================================================================================

export const StaggerContainer = ({ children, delayChildren = 0.1, staggerChildren = 0.1, className = '' }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  const animationProps = getAnimationProps({
    initial: 'hidden',
    animate: isInView ? 'visible' : 'hidden',
    variants: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          delayChildren,
          staggerChildren
        }
      }
    }
  });

  return (
    <motion.div ref={ref} className={className} {...animationProps}>
      {children}
    </motion.div>
  );
};

export const StaggerItem = ({ children, className = '' }) => {
  const animationProps = getAnimationProps({
    variants: {
      hidden: { 
        opacity: 0, 
        y: 30,
        scale: 0.95
      },
      visible: { 
        opacity: 1, 
        y: 0,
        scale: 1,
        transition: {
          duration: 0.5,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    }
  });

  return (
    <motion.div className={className} {...animationProps}>
      {children}
    </motion.div>
  );
};

// ================================================================================
// 🎭 ANIMATIONS HOVER
// ================================================================================

export const HoverCard = ({ children, className = '', scale = 1.02, rotateX = 5, rotateY = 5 }) => {
  const animationProps = getAnimationProps({
    whileHover: { 
      scale,
      rotateX,
      rotateY,
      transition: { duration: 0.2 }
    },
    whileTap: { 
      scale: 0.98,
      transition: { duration: 0.1 }
    }
  }, {
    // Fallback pour reduced-motion : simple focus/hover via CSS
    className: `${className} hover:shadow-lg focus:shadow-lg transition-shadow duration-200`
  });

  return (
    <motion.div 
      className={className} 
      style={{ transformStyle: 'preserve-3d' }}
      {...animationProps}
    >
      {children}
    </motion.div>
  );
};

// ================================================================================
// 🌊 ANIMATIONS PRICING CARDS
// ================================================================================

export const PricingCard = ({ children, className = '', isPopular = false }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const animationProps = getAnimationProps({
    initial: { 
      opacity: 0, 
      y: 50,
      scale: 0.9
    },
    animate: isInView ? { 
      opacity: 1, 
      y: 0,
      scale: 1
    } : {},
    whileHover: { 
      y: -8,
      scale: 1.02,
      transition: { duration: 0.3 }
    },
    transition: { 
      duration: 0.6,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  });

  const glowProps = isPopular ? getAnimationProps({
    animate: {
      boxShadow: [
        '0 0 20px rgba(139, 92, 246, 0.3)',
        '0 0 40px rgba(139, 92, 246, 0.6)',
        '0 0 20px rgba(139, 92, 246, 0.3)'
      ]
    },
    transition: {
      duration: 2,
      repeat: Infinity,
      repeatType: 'reverse'
    }
  }) : {};

  return (
    <motion.div 
      ref={ref}
      className={className}
      {...animationProps}
      {...glowProps}
    >
      {children}
    </motion.div>
  );
};

// ================================================================================
// 🎪 ANIMATIONS BOUTONS
// ================================================================================

export const AnimatedButton = ({ children, className = '', variant = 'primary', onClick, disabled = false, ...props }) => {
  const baseClasses = 'relative overflow-hidden';
  
  const variants = {
    primary: 'bg-gradient-to-r from-purple-600 to-pink-600 text-white',
    secondary: 'bg-white text-gray-900 border border-gray-300',
    outline: 'border-2 border-purple-600 text-purple-600 bg-transparent hover:bg-purple-600 hover:text-white'
  };

  const animationProps = getAnimationProps({
    whileHover: disabled ? {} : { 
      scale: 1.02,
      transition: { duration: 0.2 }
    },
    whileTap: disabled ? {} : { 
      scale: 0.98,
      transition: { duration: 0.1 }
    },
    animate: {
      boxShadow: variant === 'primary' ? [
        '0 4px 15px rgba(139, 92, 246, 0.2)',
        '0 6px 20px rgba(139, 92, 246, 0.4)',
        '0 4px 15px rgba(139, 92, 246, 0.2)'
      ] : 'none'
    },
    transition: {
      boxShadow: {
        duration: 2,
        repeat: Infinity,
        repeatType: 'reverse'
      }
    }
  });

  return (
    <motion.button
      className={`${baseClasses} ${variants[variant]} ${className} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      {...animationProps}
      {...props}
    >
      {/* Effet de vague au clic */}
      <motion.div
        className="absolute inset-0 bg-white opacity-0"
        whileTap={disabled ? {} : {
          scale: [0, 1],
          opacity: [0.3, 0],
          transition: { duration: 0.4 }
        }}
        style={{ borderRadius: '50%' }}
      />
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};

// ================================================================================
// 📊 ANIMATION COMPTEURS
// ================================================================================

export const CounterAnimation = ({ from = 0, to, duration = 2, prefix = '', suffix = '', className = '' }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  
  const animationProps = getAnimationProps({
    initial: { opacity: 0 },
    animate: isInView ? { opacity: 1 } : {},
    transition: { duration: 0.5 }
  });

  return (
    <motion.div ref={ref} className={className} {...animationProps}>
      {isInView && (
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration }}
        >
          {prefix}
          <motion.span
            initial={from}
            animate={to}
            transition={{ duration, ease: 'easeOut' }}
          >
            {({ value }) => Math.round(value).toLocaleString()}
          </motion.span>
          {suffix}
        </motion.span>
      )}
    </motion.div>
  );
};

export default {
  FadeInWhenVisible,
  ParallaxContainer,
  StaggerContainer,
  StaggerItem,
  HoverCard,
  PricingCard,
  AnimatedButton,
  CounterAnimation
};
```

### 4. HOOK DÉTECTION CAPACITÉS DEVICE - `useDeviceCapabilities.js`
```javascript
// ================================================================================
// ECOMSIMPLY - HOOK DÉTECTION CAPACITÉS DEVICE - VERSION PERFORMANCE SÉCURISÉE
// ================================================================================

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';

// ================================================================================
// 🔍 HOOK PRINCIPAL DEVICE CAPABILITIES
// ================================================================================

export const useDeviceCapabilities = () => {
  const [capabilities, setCapabilities] = useState({
    webGL: null,
    webGL2: null,
    hardware: null,
    network: null,
    memory: null,
    reducedMotion: null,
    touch: null,
    gpu: null,
    loading: true
  });

  // Test WebGL support
  const testWebGL = useCallback(() => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      const gl2 = canvas.getContext('webgl2');
      
      return {
        webGL: !!gl,
        webGL2: !!gl2,
        gpu: gl ? gl.getParameter(gl.RENDERER) : null
      };
    } catch (e) {
      return { webGL: false, webGL2: false, gpu: null };
    }
  }, []);

  // Test hardware capabilities
  const testHardware = useCallback(() => {
    const nav = navigator;
    
    return {
      cores: nav.hardwareConcurrency || 1,
      memory: nav.deviceMemory || null,
      platform: nav.platform || 'unknown',
      userAgent: nav.userAgent || '',
      touch: 'ontouchstart' in window || navigator.maxTouchPoints > 0
    };
  }, []);

  // Test network capabilities
  const testNetwork = useCallback(() => {
    if ('connection' in navigator) {
      const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      
      return {
        effectiveType: conn?.effectiveType || 'unknown',
        downlink: conn?.downlink || null,
        rtt: conn?.rtt || null,
        saveData: conn?.saveData || false
      };
    }
    
    return {
      effectiveType: 'unknown',
      downlink: null,
      rtt: null,
      saveData: false
    };
  }, []);

  // Test reduced motion preference
  const testReducedMotion = useCallback(() => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }, []);

  // Performance tier calculation
  const calculatePerformanceTier = useCallback((caps) => {
    let score = 0;

    // WebGL support
    if (caps.webGL2) score += 30;
    else if (caps.webGL) score += 20;

    // Hardware score
    if (caps.hardware.cores >= 8) score += 25;
    else if (caps.hardware.cores >= 4) score += 15;
    else if (caps.hardware.cores >= 2) score += 10;

    // Memory score
    if (caps.hardware.memory >= 8) score += 20;
    else if (caps.hardware.memory >= 4) score += 15;
    else if (caps.hardware.memory >= 2) score += 10;

    // Network score
    if (caps.network.effectiveType === '4g') score += 15;
    else if (caps.network.effectiveType === '3g') score += 10;
    else if (caps.network.effectiveType === 'slow-2g') score -= 10;

    // Save data preference
    if (caps.network.saveData) score -= 15;

    // GPU quality (basic heuristic)
    if (caps.gpu && caps.gpu.toLowerCase().includes('nvidia')) score += 10;
    else if (caps.gpu && caps.gpu.toLowerCase().includes('radeon')) score += 8;

    // Determine tier
    if (score >= 80) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  }, []);

  // Initialize capabilities detection
  useEffect(() => {
    const detectCapabilities = async () => {
      try {
        const webglResults = testWebGL();
        const hardware = testHardware();
        const network = testNetwork();
        const reducedMotion = testReducedMotion();

        const newCapabilities = {
          webGL: webglResults.webGL,
          webGL2: webglResults.webGL2,
          gpu: webglResults.gpu,
          hardware,
          network,
          reducedMotion,
          touch: hardware.touch,
          loading: false
        };

        // Calculate performance tier
        const performanceTier = calculatePerformanceTier(newCapabilities);
        newCapabilities.performanceTier = performanceTier;

        setCapabilities(newCapabilities);
      } catch (error) {
        console.warn('Error detecting device capabilities:', error);
        
        // Fallback safe values
        setCapabilities({
          webGL: false,
          webGL2: false,
          gpu: null,
          hardware: { cores: 1, memory: null, platform: 'unknown', userAgent: '', touch: false },
          network: { effectiveType: 'unknown', downlink: null, rtt: null, saveData: false },
          reducedMotion: true, // Safe default
          touch: false,
          performanceTier: 'low',
          loading: false
        });
      }
    };

    detectCapabilities();
  }, [testWebGL, testHardware, testNetwork, testReducedMotion, calculatePerformanceTier]);

  // Listen for changes in reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleChange = (e) => {
      setCapabilities(prev => ({
        ...prev,
        reducedMotion: e.matches
      }));
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return capabilities;
};

// ================================================================================
// 🎯 HOOK SPÉCIALISÉS
// ================================================================================

// Hook pour déterminer si on peut utiliser les animations 3D
export const use3DCapabilities = () => {
  const capabilities = useDeviceCapabilities();
  
  const canUse3D = capabilities.webGL && 
                   capabilities.performanceTier !== 'low' && 
                   !capabilities.reducedMotion &&
                   !capabilities.network.saveData;

  const shouldUse3D = canUse3D && 
                      capabilities.hardware.cores >= 2 && 
                      capabilities.performanceTier === 'high';

  return {
    canUse3D,
    shouldUse3D,
    webGLSupport: capabilities.webGL,
    webGL2Support: capabilities.webGL2,
    performanceTier: capabilities.performanceTier,
    loading: capabilities.loading
  };
};

// Hook pour déterminer le niveau d'animation approprié
export const useAnimationLevel = () => {
  const capabilities = useDeviceCapabilities();
  
  if (capabilities.loading) return 'loading';
  
  if (capabilities.reducedMotion) return 'minimal';
  
  if (capabilities.performanceTier === 'high' && !capabilities.network.saveData) {
    return 'full';
  }
  
  if (capabilities.performanceTier === 'medium') {
    return 'reduced';
  }
  
  return 'minimal';
};

export default {
  useDeviceCapabilities,
  use3DCapabilities,
  useAnimationLevel
};
```

### 5. ANIMATION 3D WORKFLOW - `WorkflowAnimation3D.js`
```javascript
// ================================================================================
// ECOMSIMPLY - ANIMATION 3D WORKFLOW DYNAMIQUE - VERSION COMPLETE
// ================================================================================

import * as React from 'react';
import { Suspense, useRef, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  Text3D, 
  Float, 
  Trail, 
  Environment, 
  OrbitControls,
  Sphere,
  Box,
  Cylinder
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// ================================================================================
// 🌐 COMPOSANT SCRAPING WEB (ÉTAPE 1)
// ================================================================================

const ScrapingNode = ({ position, active, scale = 1, isMobile = false }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  // Tailles adaptatives selon device
  const sphereSize = isMobile ? 1.2 : 1.8;
  const labelSize = isMobile ? 0.25 : 0.4;
  const effectScale = scale * (isMobile ? 1.5 : 2.2);

  useFrame((state) => {
    if (meshRef.current && active) {
      meshRef.current.rotation.y += 0.02;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.15;
    }
  });

  return (
    <group position={position} scale={effectScale}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.8}>
        {/* Icône Web/Globe agrandie */}
        <mesh
          ref={meshRef}
          scale={1}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
        >
          <sphereGeometry args={[sphereSize, 20, 20]} />
          <meshStandardMaterial 
            color={active ? "#00f5ff" : "#6b7280"} 
            emissive={active ? "#003d4d" : "#000000"}
            wireframe={true}
            transparent
            opacity={active ? 0.95 : 0.6}
            emissiveIntensity={active ? 0.3 : 0}
          />
        </mesh>

        {/* Particules de données améliorées */}
        {active && (
          <>
            <Trail width={0.2} length={12} color="#00f5ff" attenuation={(t) => t * t}>
              <mesh position={[1.5, 0, 0]}>
                <boxGeometry args={[0.2, 0.2, 0.2]} />
                <meshBasicMaterial color="#00f5ff" />
              </mesh>
            </Trail>
            <Trail width={0.2} length={12} color="#00f5ff" attenuation={(t) => t * t}>
              <mesh position={[-1.5, 0, 0]}>
                <boxGeometry args={[0.2, 0.2, 0.2]} />
                <meshBasicMaterial color="#00f5ff" />
              </mesh>
            </Trail>
            <Trail width={0.15} length={10} color="#7dd3fc" attenuation={(t) => t * t}>
              <mesh position={[0, 1.2, 0]}>
                <boxGeometry args={[0.15, 0.15, 0.15]} />
                <meshBasicMaterial color="#7dd3fc" />
              </mesh>
            </Trail>
          </>
        )}

        {/* Label avec contraste élevé */}
        <Text3D
          font="/fonts/helvetiker_regular.typeface.json"
          size={labelSize}
          height={0.08}
          position={[0, -2.5, 0]}
          castShadow
        >
          SCRAPING WEB
          <meshStandardMaterial 
            color={active ? "#ffffff" : "#9ca3af"} 
            emissive={active ? "#00f5ff" : "#000000"}
            emissiveIntensity={active ? 0.2 : 0}
          />
        </Text3D>

        {/* Halo lumineux pour contraste */}
        {active && (
          <mesh position={[0, 0, -0.5]} scale={effectScale * 1.5}>
            <circleGeometry args={[2, 32]} />
            <meshBasicMaterial 
              color="#00f5ff" 
              transparent 
              opacity={0.1}
            />
          </mesh>
        )}
      </Float>
    </group>
  );
};

// ================================================================================
// 🧠 COMPOSANT IA SEO/PRIX (ÉTAPE 2)
// ================================================================================

const AIOptimizationNode = ({ position, active, scale = 1, isMobile = false }) => {
  const meshRef = useRef();
  const brainRef = useRef();
  
  // Tailles adaptatives
  const brainSize = isMobile ? 0.8 : 1.4;
  const labelSize = isMobile ? 0.25 : 0.4;
  const effectScale = scale * (isMobile ? 1.5 : 2.5);
  const indicatorSize = isMobile ? 0.5 : 0.8;
  
  useFrame((state) => {
    if (meshRef.current && active) {
      meshRef.current.rotation.x += 0.01;
      meshRef.current.rotation.z += 0.005;
    }
    if (brainRef.current) {
      brainRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 3) * 0.08;
    }
  });

  return (
    <group position={position} scale={effectScale}>
      <Float speed={1.8} rotationIntensity={0.3} floatIntensity={0.6}>
        {/* Cerveau IA central agrandi */}
        <mesh ref={brainRef} scale={1}>
          <sphereGeometry args={[brainSize, 16, 12]} />
          <meshStandardMaterial 
            color={active ? "#a855f7" : "#6b7280"}
            emissive={active ? "#581c87" : "#000000"}
            roughness={0.2}
            metalness={0.8}
            emissiveIntensity={active ? 0.4 : 0}
          />
        </mesh>

        {/* Particules de traitement améliorées */}
        {active && Array.from({ length: 12 }).map((_, i) => (
          <Trail key={i} width={0.12} length={8} color="#a855f7" attenuation={(t) => t * t}>
            <mesh
              position={[
                Math.cos((i / 12) * Math.PI * 2) * 2.2,
                Math.sin(Date.now() * 0.001 + i) * 0.5,
                Math.sin((i / 12) * Math.PI * 2) * 2.2
              ]}
            >
              <boxGeometry args={[0.08, 0.08, 0.08]} />
              <meshBasicMaterial color="#a855f7" />
            </mesh>
          </Trail>
        ))}

        {/* Indicateurs SEO améliorés */}
        {active && (
          <>
            <mesh position={[1.8, 0.5, 0]} scale={indicatorSize}>
              <cylinderGeometry args={[0.5, 0.5, 0.2, 8]} />
              <meshStandardMaterial 
                color="#22c55e" 
                emissive="#15803d" 
                emissiveIntensity={0.3}
              />
            </mesh>
            <Text3D
              font="/fonts/helvetiker_regular.typeface.json"
              size={labelSize * 0.6}
              height={0.04}
              position={[1.2, 0.8, 0.1]}
            >
              SEO
              <meshStandardMaterial 
                color="#ffffff" 
                emissive="#22c55e"
                emissiveIntensity={0.2}
              />
            </Text3D>

            {/* Indicateur Prix amélioré */}
            <mesh position={[-1.8, 0.5, 0]} scale={indicatorSize}>
              <cylinderGeometry args={[0.5, 0.5, 0.2, 8]} />
              <meshStandardMaterial 
                color="#f59e0b" 
                emissive="#d97706" 
                emissiveIntensity={0.3}
              />
            </mesh>
            <Text3D
              font="/fonts/helvetiker_regular.typeface.json"
              size={labelSize * 0.6}
              height={0.04}
              position={[-2.2, 0.8, 0.1]}
            >
              PRIX
              <meshStandardMaterial 
                color="#ffffff" 
                emissive="#f59e0b"
                emissiveIntensity={0.2}
              />
            </Text3D>
          </>
        )}

        {/* Label principal avec contraste élevé */}
        <Text3D
          font="/fonts/helvetiker_regular.typeface.json"
          size={labelSize}
          height={0.08}
          position={[0, -2.5, 0]}
          castShadow
        >
          IA OPTIMIZATION
          <meshStandardMaterial 
            color={active ? "#ffffff" : "#9ca3af"} 
            emissive={active ? "#a855f7" : "#000000"}
            emissiveIntensity={active ? 0.2 : 0}
          />
        </Text3D>

        {/* Halo lumineux pour contraste */}
        {active && (
          <mesh position={[0, 0, -0.5]} scale={effectScale * 1.3}>
            <circleGeometry args={[2.5, 32]} />
            <meshBasicMaterial 
              color="#a855f7" 
              transparent 
              opacity={0.1}
            />
          </mesh>
        )}
      </Float>
    </group>
  );
};

// ================================================================================
// 🏪 COMPOSANT PUBLICATION E-COMMERCE (ÉTAPE 3)
// ================================================================================

const EcommercePublishNode = ({ position, active, scale = 1, isMobile = false }) => {
  const groupRef = useRef();
  const platformRefs = useRef([]);

  // Tailles adaptatives
  const hubSize = isMobile ? [1.2, 1.2, 0.6] : [1.8, 1.8, 0.8];
  const labelSize = isMobile ? 0.25 : 0.4;
  const effectScale = scale * (isMobile ? 1.5 : 2.2);
  const platformDistance = isMobile ? 2.5 : 3.5;

  useFrame((state) => {
    if (groupRef.current && active) {
      groupRef.current.rotation.y += 0.008;
    }
    
    // Animation des plateformes
    platformRefs.current.forEach((ref, i) => {
      if (ref && active) {
        ref.position.y = Math.sin(state.clock.elapsedTime * 2 + i * 0.5) * 0.15;
        ref.rotation.z += 0.005;
      }
    });
  });

  const platforms = [
    { name: 'SHOPIFY', color: '#96bf48', position: [platformDistance, 0.8, 0] },
    { name: 'WOOCOM', color: '#96588a', position: [-platformDistance, 0.8, 0] },
    { name: 'MAGENTO', color: '#ee672f', position: [0, 0.8, platformDistance] },
    { name: 'PRESTASHOP', color: '#df0067', position: [0, 0.8, -platformDistance] }
  ];

  return (
    <group position={position} ref={groupRef} scale={effectScale}>
      <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.4}>
        
        {/* Hub central agrandi */}
        <mesh scale={1}>
          <cylinderGeometry args={hubSize.concat([12])} />
          <meshStandardMaterial 
            color={active ? "#ec4899" : "#6b7280"}
            emissive={active ? "#be185d" : "#000000"}
            roughness={0.1}
            metalness={0.9}
            emissiveIntensity={active ? 0.4 : 0}
          />
        </mesh>

        {/* Plateformes e-commerce agrandies */}
        {platforms.map((platform, i) => (
          <group key={platform.name}>
            <mesh
              ref={(el) => (platformRefs.current[i] = el)}
              position={platform.position}
              scale={active ? 0.8 : 0.4}
            >
              <boxGeometry args={[1.5, 1.2, 0.4]} />
              <meshStandardMaterial 
                color={active ? platform.color : "#6b7280"}
                emissive={active ? new THREE.Color(platform.color).multiplyScalar(0.2) : "#000000"}
                emissiveIntensity={active ? 0.3 : 0}
              />
            </mesh>

            {/* Labels des plateformes */}
            <Text3D
              font="/fonts/helvetiker_regular.typeface.json"
              size={labelSize * 0.5}
              height={0.04}
              position={[
                platform.position[0] - 0.8,
                platform.position[1] + 0.8,
                platform.position[2]
              ]}
            >
              {platform.name}
              <meshStandardMaterial 
                color="#ffffff" 
                emissive={active ? platform.color : "#000000"}
                emissiveIntensity={active ? 0.2 : 0}
              />
            </Text3D>
            
            {/* Connexions vers le hub améliorées */}
            {active && (
              <Trail width={0.15} length={15} color={platform.color} attenuation={(t) => t * t}>
                <mesh position={[-platform.position[0] * 0.3, -platform.position[1] * 0.3, -platform.position[2] * 0.3]}>
                  <sphereGeometry args={[0.08]} />
                  <meshBasicMaterial color={platform.color} />
                </mesh>
              </Trail>
            )}
          </group>
        ))}

        {/* Label principal avec contraste élevé */}
        <Text3D
          font="/fonts/helvetiker_regular.typeface.json"
          size={labelSize}
          height={0.08}
          position={[0, -2.8, 0]}
          castShadow
        >
          PUBLICATION AUTO
          <meshStandardMaterial 
            color={active ? "#ffffff" : "#9ca3af"} 
            emissive={active ? "#ec4899" : "#000000"}
            emissiveIntensity={active ? 0.2 : 0}
          />
        </Text3D>

        {/* Halo lumineux pour contraste */}
        {active && (
          <mesh position={[0, 0, -0.5]} scale={effectScale * 1.4}>
            <circleGeometry args={[3, 32]} />
            <meshBasicMaterial 
              color="#ec4899" 
              transparent 
              opacity={0.1}
            />
          </mesh>
        )}
      </Float>
    </group>
  );
};

// ================================================================================
// 🔗 FLUX DE DONNÉES ANIMÉ AMÉLIORÉ
// ================================================================================

const DataFlow = ({ from, to, active, color = "#00f5ff", isMobile = false }) => {
  const lineRef = useRef();
  const flowWidth = isMobile ? 0.05 : 0.08;
  
  useFrame((state) => {
    if (lineRef.current && active) {
      const opacity = (Math.sin(state.clock.elapsedTime * 3) + 1) / 2;
      lineRef.current.material.opacity = opacity * 0.9;
    }
  });

  if (!active) return null;

  const points = [];
  const steps = 25;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = THREE.MathUtils.lerp(from[0], to[0], t);
    const y = THREE.MathUtils.lerp(from[1], to[1], t) + Math.sin(t * Math.PI) * (isMobile ? 0.8 : 1.2);
    const z = THREE.MathUtils.lerp(from[2], to[2], t);
    points.push(new THREE.Vector3(x, y, z));
  }

  const curve = new THREE.CatmullRomCurve3(points);
  const geometry = new THREE.TubeGeometry(curve, 80, flowWidth, 12, false);

  return (
    <mesh ref={lineRef} geometry={geometry}>
      <meshBasicMaterial color={color} transparent opacity={0.8} />
    </mesh>
  );
};

// ================================================================================
// 🎬 SCÈNE PRINCIPALE WORKFLOW RESPONSIVE
// ================================================================================

const WorkflowScene = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const { camera, viewport } = useThree();
  
  // Détection responsive
  useEffect(() => {
    const checkMobile = () => {
      const mobile = viewport.width < 8 || window.innerWidth < 768;
      setIsMobile(mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [viewport.width]);

  // Animation séquentielle des étapes
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % 4); // 0: all off, 1: scraping, 2: AI, 3: publish
    }, 4000); // Changement toutes les 4 secondes pour plus de visibilité

    return () => clearInterval(interval);
  }, []);

  // Positions adaptatives selon la taille d'écran
  const getPositions = () => {
    if (isMobile) {
      return {
        scraping: [-3, 1, 0],
        ai: [0, 0, 0], 
        publish: [3, -1, 0],
        cameraPos: [0, 3, 12]
      };
    } else {
      return {
        scraping: [-6, 0, 0],
        ai: [0, 0, 0],
        publish: [6, 0, 0],
        cameraPos: [0, 4, 16]
      };
    }
  };

  const positions = getPositions();

  // Position de la caméra adaptative
  useFrame(() => {
    camera.position.lerp(
      { x: positions.cameraPos[0], y: positions.cameraPos[1], z: positions.cameraPos[2] },
      0.02
    );
    camera.lookAt(0, 0, 0);
  });

  return (
    <>
      {/* Éclairage renforcé pour meilleur contraste */}
      <ambientLight intensity={0.4} />
      <directionalLight 
        position={[15, 15, 8]} 
        intensity={1.5} 
        castShadow 
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <pointLight position={[-12, -8, -8]} intensity={0.6} color="#00f5ff" />
      <pointLight position={[12, -5, 8]} intensity={0.6} color="#a855f7" />
      <pointLight position={[0, 10, 0]} intensity={0.4} color="#ec4899" />

      {/* Environnement */}
      <Environment preset="city" />

      {/* Nodes du workflow avec détection responsive */}
      <ScrapingNode 
        position={positions.scraping}
        active={currentStep >= 1} 
        scale={currentStep === 1 ? 1.3 : 1}
        isMobile={isMobile}
      />
      
      <AIOptimizationNode 
        position={positions.ai}
        active={currentStep >= 2} 
        scale={currentStep === 2 ? 1.3 : 1}
        isMobile={isMobile}
      />
      
      <EcommercePublishNode 
        position={positions.publish}
        active={currentStep >= 3} 
        scale={currentStep === 3 ? 1.3 : 1}
        isMobile={isMobile}
      />

      {/* Flux de données adaptatifs */}
      <DataFlow 
        from={positions.scraping}
        to={positions.ai}
        active={currentStep >= 2} 
        color="#00f5ff" 
        isMobile={isMobile}
      />
      
      <DataFlow 
        from={positions.ai}
        to={positions.publish}
        active={currentStep >= 3} 
        color="#a855f7" 
        isMobile={isMobile}
      />

      {/* Particules d'ambiance adaptées */}
      <ParticleField count={isMobile ? 30 : 80} />

      {/* Contrôles adaptatifs */}
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        maxPolarAngle={Math.PI / 2}
        minPolarAngle={Math.PI / 4}
        autoRotate
        autoRotateSpeed={isMobile ? 0.1 : 0.3}
        maxAzimuthAngle={Math.PI / 6}
        minAzimuthAngle={-Math.PI / 6}
      />
    </>
  );
};

// ================================================================================
// ✨ CHAMP DE PARTICULES
// ================================================================================

const ParticleField = ({ count = 50 }) => {
  const pointsRef = useRef();
  const [positions] = useState(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 15;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 15;
    }
    return pos;
  });

  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.02;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.03} color="#4a5568" transparent opacity={0.4} />
    </points>
  );
};

// ================================================================================
// 🎯 COMPOSANT PRINCIPAL WORKFLOW ANIMATION 3D
// ================================================================================

const WorkflowAnimation3D = ({ className, children, fallback = false }) => {
  const [webGLSupported, setWebGLSupported] = useState(null);
  const [shouldUse3D, setShouldUse3D] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (typeof window === 'undefined') {
      setShouldUse3D(false);
      return;
    }

    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      const hasWebGL = !!gl;
      const isLowEnd = navigator.hardwareConcurrency <= 2;
      const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      
      setWebGLSupported(hasWebGL);
      setShouldUse3D(hasWebGL && !isLowEnd && !isReducedMotion && !fallback);
    } catch (err) {
      console.warn('Error during 3D capability detection:', err);
      setError(err.message);
      setWebGLSupported(false);
      setShouldUse3D(false);
    }
  }, [fallback]);

  const handleCanvasError = (error) => {
    console.error('Canvas error in workflow animation:', error);
    setError(error.message || 'Canvas rendering error');
    setShouldUse3D(false);
  };

  // Loading state
  if (shouldUse3D === null) {
    return (
      <div className={`${className} bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="w-8 h-8 border-2 border-white border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
        {children}
      </div>
    );
  }

  // Utiliser 3D
  if (shouldUse3D && !error) {
    return (
      <div className={`${className} relative`}>
        <Suspense fallback={
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
            <div className="text-white text-center">
              <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p>Chargement de l'animation workflow...</p>
            </div>
          </div>
        }>
          <Canvas
            className="absolute inset-0"
            camera={{ position: [0, 2, 8], fov: 60 }}
            dpr={[1, 2]}
            performance={{ min: 0.5 }}
            style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 30%, #4338ca 70%, #6366f1 100%)' }}
            onError={handleCanvasError}
            gl={{ 
              antialias: false,
              alpha: false,
              preserveDrawingBuffer: false
            }}
          >
            <WorkflowScene />
          </Canvas>
        </Suspense>
        <div className="relative z-10">
          {children}
        </div>
      </div>
    );
  }

  // Fallback gracieux
  return (
    <div className={`${className} relative`}>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        {/* Animation CSS fallback */}
        <div className="absolute inset-0 overflow-hidden">
          {/* Simulation du workflow en CSS */}
          <motion.div
            className="absolute top-1/2 left-1/4 w-16 h-16 bg-blue-500 rounded-full opacity-60"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatType: "reverse",
            }}
          />
          <motion.div
            className="absolute top-1/2 left-1/2 w-16 h-16 bg-purple-500 rounded-full opacity-60"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatType: "reverse",
              delay: 0.7,
            }}
          />
          <motion.div
            className="absolute top-1/2 right-1/4 w-16 h-16 bg-pink-500 rounded-full opacity-60"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatType: "reverse",
              delay: 1.4,
            }}
          />
        </div>
      </div>
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default WorkflowAnimation3D;
```

## 📦 CONFIGURATION PACKAGE.JSON

### Dependencies Nécessaires
```json
{
  "dependencies": {
    "@react-three/drei": "^9.108.4",
    "@react-three/fiber": "^8.15.15",
    "framer-motion": "^11.3.19",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "three": "^0.160.0"
  },
  "overrides": {
    "react": "18.2.0",
    "react-dom": "18.2.0"
  }
}
```

## 🔧 CONFIGURATION TAILWIND CSS

### Extensions de Theme - `tailwind.config.js`
```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      animationDelay: {
        '100': '100ms',
        '200': '200ms',
        '300': '300ms',
        '400': '400ms',
        '500': '500ms',
        '600': '600ms',
        '700': '700ms',
        '800': '800ms',
        '900': '900ms',
        '1000': '1000ms',
        '1100': '1100ms',
        '1200': '1200ms',
        '1300': '1300ms',
        '1400': '1400ms',
        '1500': '1500ms',
      }
    },
  },
  plugins: [],
};
```

## 🚀 INTÉGRATION DANS APP.JS

### Imports et Lazy Loading
```javascript
import { Suspense, lazy } from 'react';

// Lazy loading sécurisé des composants 3D
const HeroScene3D = lazy(() => import('./components/HeroScene3D'));
const Hero3DSection = lazy(() => import('./components/Hero3DSection'));

import { 
  FadeInWhenVisible, 
  ParallaxContainer, 
  StaggerContainer, 
  StaggerItem, 
  HoverCard, 
  PricingCard, 
  AnimatedButton, 
  CounterAnimation,
  StickyHeader
} from './components/MotionComponents';
import { use3DCapabilities, useAnimationLevel } from './hooks/useDeviceCapabilities';
```

### Remplacement de la Section Hero
```javascript
// Remplacer l'ancienne section hero par :
<Suspense fallback={
  <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
    <div className="text-white text-center">
      <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p>Chargement de l'expérience 3D...</p>
    </div>
  </div>
}>
  <Hero3DSection
    onShowTrialPlanSelection={() => setShowTrialPlanSelection(true)}
    currentLanguage={language}
    PLATFORM_CONFIG={PLATFORM_CONFIG}
  />
</Suspense>
```

## 🔒 SÉCURITÉ ET FALLBACKS

### Détection Automatique des Capacités
- ✅ **WebGL Support**: Détection automatique avec fallback CSS
- ✅ **Performance Tiers**: Classification automatic des devices (low/medium/high)
- ✅ **Reduced Motion**: Respect des préférences accessibilité
- ✅ **Mobile Responsive**: Adaptations automatiques pour mobile
- ✅ **Error Boundaries**: Gestion d'erreurs avec retour gracieux

### Compatibilité
- ✅ **React 18.2.0**: Version forcée pour éviter les conflits
- ✅ **Three.js r160**: Version stable et performante
- ✅ **Framer Motion 11**: Animations modernes et performantes
- ✅ **SSR Safe**: Server-side rendering compatible

## 🎨 CUSTOMISATION

### Variables de Configuration
```javascript
const PLATFORM_CONFIG = {
  FREE_TRIAL_DAYS: 7,
  PREMIUM_COMMISSION_RATE: 15,
  // ... autres configurations
};
```

### Styles Personnalisables
- Couleurs: Gradients purple/blue/pink configurables
- Animations: Niveaux d'animation adaptatifs (full/reduced/minimal)
- Tailles: Responsive avec breakpoints Tailwind

## 📱 RESPONSIVE DESIGN

### Breakpoints
- **Mobile**: < 768px - Animations simplifiées, tailles réduites
- **Tablet**: 768px - 1024px - Animations moyennes
- **Desktop**: > 1024px - Animations complètes, effets 3D

### Optimisations Mobile
- Détection automatique des capacités
- Réduction du nombre de particules
- Simplification des animations 3D
- Fallback CSS pour devices low-end

## 🎯 POINTS CLÉS D'IMPLÉMENTATION

1. **Lazy Loading**: Tous les composants 3D sont chargés de manière différée
2. **Fallback Gracieux**: Animation CSS si 3D non supporté
3. **Performance Adaptative**: Ajustement automatique selon les capacités
4. **Accessibilité**: Respect des préférences reduced-motion
5. **Error Handling**: Gestion robuste des erreurs 3D
6. **SEO Friendly**: Contenu accessible sans JavaScript

Cette extraction contient tout le code nécessaire pour implémenter une homepage 3D immersive complète et sécurisée pour ECOMSIMPLY.