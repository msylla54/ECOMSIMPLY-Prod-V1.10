// ================================================================================
// ECOMSIMPLY - PREMIUM PAGE TRANSITIONS AWWWARDS
// Transitions de page avec layoutId et animations orchestrées
// ================================================================================

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const PageTransition = ({ children, pageKey }) => {
  const pageVariants = {
    initial: {
      opacity: 0,
      y: 20,
      scale: 0.98
    },
    in: {
      opacity: 1,
      y: 0,
      scale: 1
    },
    out: {
      opacity: 0,
      y: -20,
      scale: 1.02
    }
  };

  const pageTransition = {
    type: "tween",
    ease: [0.22, 0.61, 0.36, 1],
    duration: 0.4
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pageKey}
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

// Container pour stagger animations
export const StaggerContainer = ({ children, className = "", delay = 0 }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: delay,
      },
    },
  };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {children}
    </motion.div>
  );
};

// Item pour stagger animations
export const StaggerItem = ({ children, className = "" }) => {
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.22, 0.61, 0.36, 1],
      },
    },
  };

  return (
    <motion.div
      className={className}
      variants={itemVariants}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;