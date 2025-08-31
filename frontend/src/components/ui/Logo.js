import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Logo Component ECOMSIMPLY XXL - Ultra Visible Headers
 * Selon spécifications: logo GRAND, sans opacité, responsive
 * 
 * @param {Object} props
 * @param {string} props.size - 'mobile', 'tablet', 'desktop' (defaults to 'tablet')
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onClick - Click handler (optional)
 * @param {boolean} props.linkToHome - Use Link component for routing (default: true)
 */
const Logo = ({ 
  size = 'tablet', 
  className = '', 
  onClick = null,
  linkToHome = true 
}) => {
  // Size mapping for XXL responsive design
  const sizeClasses = {
    mobile: 'h-10 w-auto max-h-full',      // Mobile: h-10 (40px)
    tablet: 'h-16 w-auto max-h-full',      // Tablet: h-16 (64px)  
    desktop: 'h-20 w-auto max-h-full'      // Desktop: h-20 (80px)
  };

  // Base classes for premium styling - NEVER opacity < 100%
  const baseClasses = `
    object-contain 
    drop-shadow-sm 
    transition-all 
    duration-300 
    ease-in-out
    hover:scale-105 
    cursor-pointer
    ${sizeClasses[size]}
    ${className}
  `.trim();

  // Priority: PNG in public root, fallback to logo.png
  const logoSrc = '/ecomsimply-logo.png';
  const logoFallback = '/logo.png';

  // Handle click events
  const handleClick = (e) => {
    if (onClick) {
      e.preventDefault();
      onClick(e);
    }
    // Default: navigate to home - handled by Link component
  };

  const logoElement = (
    <img
      src={logoSrc}
      onError={(e) => {
        e.target.src = logoFallback;
      }}
      alt="ECOMSIMPLY"
      title="ECOMSIMPLY"
      className={baseClasses}
      onClick={handleClick}
      loading="eager" // Load immediately for headers
      // Accessibility attributes
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick(e);
        }
      }}
    />
  );

  // Use Link component for navigation
  if (linkToHome) {
    return (
      <Link 
        to="/" 
        className="inline-block focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 rounded-md"
        onClick={handleClick}
        aria-label="Retour à l'accueil ECOMSIMPLY"
      >
        {logoElement}
      </Link>
    );
  }

  return logoElement;
};

// Header Logo XXL - Pour bandeaux principales (MEGA ULTRA VISIBLE) 
export const HeaderLogo = ({ className = '', onClick = null }) => {
  return (
    <Logo
      size="desktop"
      className={`
        h-16 md:h-36 lg:h-40 
        w-auto 
        max-h-[90%] 
        object-contain 
        drop-shadow-lg
        ${className}
      `}
      onClick={onClick}
      linkToHome={true}
    />
  );
};

// NavLogo XXL responsive - Spécifications MEGA ULTRA VISIBLE
export const NavLogo = ({ className = '', onClick = null }) => {
  return (
    <Logo
      size="tablet"
      className={`
        h-20 md:h-32 lg:h-40 
        w-auto 
        max-h-full 
        object-contain 
        drop-shadow-lg
        ${className}
      `}
      onClick={onClick}
      linkToHome={true}
    />
  );
};

// Dashboard Logo XXL (MEGA ULTRA VISIBLE)
export const DashboardLogo = ({ className = '', onClick = null }) => {
  return (
    <Logo
      size="desktop"
      className={`
        h-20 md:h-32 lg:h-40 
        w-auto 
        max-h-full 
        object-contain 
        drop-shadow-lg
        ${className}
      `}
      onClick={onClick}
      linkToHome={true}
    />
  );
};

export default Logo;