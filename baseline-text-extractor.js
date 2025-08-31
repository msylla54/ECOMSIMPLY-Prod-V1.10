/**
 * Baseline Text Extractor - ECOMSIMPLY Refonte Awwwards
 * Extrait et sauvegarde les textes des pages pour éviter la régression
 */

// Fonction pour extraire les textes par sélecteurs principaux
function extractPageTexts() {
  const selectors = {
    // Navigation et header
    'nav-logo': '[data-testid="nav-logo"], .logo, nav img[alt]',
    'nav-links': 'nav a, [data-testid="nav-link"]',
    'nav-buttons': 'nav button, [data-testid="nav-button"]',
    
    // Hero section
    'hero-title': 'h1, [data-testid="hero-title"]',
    'hero-subtitle': '[data-testid="hero-subtitle"], .hero-subtitle, h1 + p',
    'hero-description': '[data-testid="hero-description"], .hero-description',
    'hero-cta': '[data-testid="hero-cta"], .hero-cta, .cta-button',
    
    // Pricing section
    'pricing-title': '[data-testid="pricing-title"], .pricing h2, .pricing-header h2',
    'pricing-plans': '[data-testid="pricing-plan"], .pricing-plan, .plan-card',
    'pricing-features': '[data-testid="pricing-features"], .plan-features li',
    'pricing-prices': '[data-testid="pricing-price"], .plan-price, .price',
    
    // Features section
    'features-title': '[data-testid="features-title"], .features h2',
    'features-items': '[data-testid="feature-item"], .feature-item, .feature-card',
    
    // Testimonials
    'testimonials-title': '[data-testid="testimonials-title"], .testimonials h2',
    'testimonial-items': '[data-testid="testimonial"], .testimonial, .testimonial-card',
    
    // Footer
    'footer-links': 'footer a, [data-testid="footer-link"]',
    'footer-text': 'footer p, footer span',
    
    // Dashboard specific
    'dashboard-title': '[data-testid="dashboard-title"], .dashboard h1, .dashboard-header h1',
    'dashboard-stats': '[data-testid="dashboard-stat"], .dashboard-stat, .stat-card',
    'dashboard-tabs': '[data-testid="dashboard-tab"], .dashboard-tab, .tab-button',
    'dashboard-content': '[data-testid="dashboard-content"], .dashboard-content',
    
    // Modals and overlays
    'modal-titles': '[data-testid="modal-title"], .modal h2, .modal-title',
    'modal-content': '[data-testid="modal-content"], .modal-content p, .modal-body',
    'modal-buttons': '[data-testid="modal-button"], .modal button',
    
    // Forms
    'form-labels': 'label, [data-testid="form-label"]',
    'form-placeholders': 'input[placeholder], textarea[placeholder]',
    'form-buttons': 'form button, [data-testid="form-button"]',
    
    // Notifications and alerts
    'notifications': '[data-testid="notification"], .notification, .alert, .banner',
    
    // General content
    'headings': 'h1, h2, h3, h4, h5, h6',
    'paragraphs': 'p',
    'buttons': 'button',
    'links': 'a[href]'
  };

  const extracted = {};
  
  Object.entries(selectors).forEach(([key, selector]) => {
    try {
      const elements = document.querySelectorAll(selector);
      extracted[key] = Array.from(elements).map((el, index) => ({
        index,
        text: el.innerText?.trim() || el.textContent?.trim() || '',
        tagName: el.tagName.toLowerCase(),
        className: el.className || '',
        id: el.id || '',
        placeholder: el.placeholder || '',
        alt: el.alt || '',
        title: el.title || ''
      })).filter(item => item.text.length > 0);
    } catch (error) {
      console.warn(`Error extracting ${key}:`, error);
      extracted[key] = [];
    }
  });
  
  return {
    timestamp: new Date().toISOString(),
    url: window.location.href,
    title: document.title,
    extracted,
    totalTexts: Object.values(extracted).reduce((sum, arr) => sum + arr.length, 0)
  };
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { extractPageTexts };
} else if (typeof window !== 'undefined') {
  window.extractPageTexts = extractPageTexts;
}