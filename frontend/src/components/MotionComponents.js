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

// ================================================================================
// 🎨 PROGRESS BAR ANIMÉE
// ================================================================================

export const AnimatedProgressBar = ({ progress = 0, className = '', height = 'h-2' }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  const animationProps = getAnimationProps({
    initial: { scaleX: 0 },
    animate: isInView ? { scaleX: progress / 100 } : { scaleX: 0 },
    transition: { duration: 1.5, ease: 'easeOut' }
  });

  return (
    <div ref={ref} className={`bg-gray-200 rounded-full overflow-hidden ${height} ${className}`}>
      <motion.div
        className="h-full bg-gradient-to-r from-purple-600 to-pink-600 origin-left"
        {...animationProps}
      />
    </div>
  );
};

// ================================================================================
// 🎭 HEADER STICKY ANIMATION
// ================================================================================

export const StickyHeader = ({ children, className = '' }) => {
  const { scrollY } = useScroll();
  const backgroundColor = useTransform(
    scrollY,
    [0, 100],
    ['rgba(255, 255, 255, 0)', 'rgba(255, 255, 255, 0.95)']
  );
  const backdropBlur = useTransform(scrollY, [0, 100], ['blur(0px)', 'blur(10px)']);
  const boxShadow = useTransform(
    scrollY,
    [0, 100],
    ['0 0 0 rgba(0, 0, 0, 0)', '0 4px 20px rgba(0, 0, 0, 0.1)']
  );

  const animationProps = getAnimationProps({
    style: {
      backgroundColor,
      backdropFilter: backdropBlur,
      boxShadow
    }
  });

  return (
    <motion.header className={`sticky top-0 z-50 transition-all duration-300 ${className}`} {...animationProps}>
      {children}
    </motion.header>
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
  CounterAnimation,
  AnimatedProgressBar,
  StickyHeader
};