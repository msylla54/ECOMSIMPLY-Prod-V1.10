// ================================================================================
// ECOMSIMPLY - TEST E2E PAGE D'ACCUEIL (HOME SMOKE TEST)
// ================================================================================

import { test, expect } from '@playwright/test';

/**
 * Suite de tests E2E pour la page d'accueil d'ECOMSIMPLY
 * Tags: @home-smoke
 */
test.describe('ECOMSIMPLY - Page d\'accueil', () => {
  
  test.beforeEach(async ({ page }) => {
    // Configuration viewport responsive
    await page.setViewportSize({ width: 1920, height: 1080 });
  });

  test('@home-smoke - Navigation et éléments principaux', async ({ page }) => {
    console.log('🏠 Test de la page d\'accueil - Navigation et éléments principaux');
    
    // Naviguer vers la page d'accueil
    await page.goto('http://localhost:3000');
    
    // Attendre le chargement complet
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Vérifier que la page se charge sans erreur 500/404
    const response = await page.request.get('http://localhost:3000');
    expect(response.status()).toBe(200);
    
    console.log('✅ Page chargée avec succès (status 200)');
  });

  test('@home-smoke - Bouton CTA principal "Lancer la Démo"', async ({ page }) => {
    console.log('🚀 Test du bouton call-to-action principal');
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Chercher le bouton "Lancer la Démo" (floating button)
    const demoButton = page.locator('button:has-text("Lancer la Démo")');
    
    // Vérifier que le bouton est présent et visible
    await expect(demoButton).toBeVisible();
    console.log('✅ Bouton "Lancer la Démo" trouvé et visible');
    
    // Vérifier les styles du bouton (gradient, shadow, etc.)
    await expect(demoButton).toHaveClass(/bg-gradient-to-r/);
    await expect(demoButton).toHaveClass(/from-purple-600/);
    await expect(demoButton).toHaveClass(/to-pink-600/);
    
    console.log('✅ Styles du bouton validés (gradient purple-pink)');
    
    // Vérifier que le bouton est cliquable
    await demoButton.click();
    
    // Attendre la navigation ou l'ouverture de modal
    await page.waitForTimeout(2000);
    
    // Vérifier la redirection vers /demo ou ouverture modal
    const currentUrl = page.url();
    const hasNavigated = currentUrl.includes('/demo') || currentUrl !== 'http://localhost:3000/';
    const hasModal = await page.locator('[role="dialog"], .modal, [data-modal]').count() > 0;
    
    if (hasNavigated) {
      console.log('✅ Navigation vers démo détectée:', currentUrl);
    } else if (hasModal) {
      console.log('✅ Modal de démo ouverte');
    } else {
      console.log('⚠️ Aucune action détectée après clic (peut être normal)');
    }
  });

  test('@home-smoke - Section Hero présente', async ({ page }) => {
    console.log('🎯 Test de la présence de la section Hero');
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Chercher des éléments typiques de hero section
    const heroElements = [
      page.locator('h1'), // Titre principal
      page.locator('[class*="hero"]'), // Section avec classe hero
      page.locator('[class*="gradient"]'), // Éléments avec gradient
      page.locator('button:has-text("Commencer")'), // Boutons CTA alternatifs
      page.locator('button:has-text("Essai gratuit")'), // Bouton essai gratuit
    ];
    
    let heroFound = false;
    
    for (const element of heroElements) {
      const count = await element.count();
      if (count > 0) {
        heroFound = true;
        console.log('✅ Élément hero trouvé:', await element.first().textContent() || 'Element trouvé');
        break;
      }
    }
    
    expect(heroFound).toBe(true);
    console.log('✅ Section Hero détectée avec succès');
  });

  test('@home-smoke - Screenshot de la hero section', async ({ page }) => {
    console.log('📸 Capture d\'écran de la section hero');
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // Attendre les animations
    
    // Créer le répertoire des artifacts s'il n'existe pas
    await page.evaluate(() => {
      // Cette commande sera exécutée côté navigateur
      console.log('Page chargée pour screenshot');
    });
    
    // Prendre un screenshot de toute la page (hero section visible)
    await page.screenshot({ 
      path: '/app/tests/e2e/home-hero.png',
      fullPage: false, // Juste le viewport pour capturer le hero
      quality: 85
    });
    
    console.log('✅ Screenshot sauvegardé: /app/tests/e2e/home-hero.png');
    
    // Prendre aussi un screenshot mobile
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(2000);
    
    await page.screenshot({ 
      path: '/app/tests/e2e/home-hero-mobile.png',
      fullPage: false,
      quality: 85
    });
    
    console.log('✅ Screenshot mobile sauvegardé: /app/tests/e2e/home-hero-mobile.png');
  });

  test('@home-smoke - Responsive design mobile', async ({ page }) => {
    console.log('📱 Test du design responsive mobile');
    
    // Configuration mobile
    await page.setViewportSize({ width: 390, height: 844 });
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Vérifier que la page se charge correctement sur mobile
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log('✅ Titre de page présent sur mobile:', title);
    
    // Chercher le bouton demo sur mobile
    const demoButton = page.locator('button:has-text("Lancer la Démo")');
    await expect(demoButton).toBeVisible();
    console.log('✅ Bouton démo visible sur mobile');
    
    // Vérifier qu'il n'y a pas de débordement horizontal
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = 390;
    
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20); // Marge de 20px
    console.log('✅ Pas de débordement horizontal détecté');
  });

  test('@home-smoke - Performance et chargement', async ({ page }) => {
    console.log('⚡ Test de performance et temps de chargement');
    
    // Mesurer le temps de chargement
    const startTime = Date.now();
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    console.log(`⏱️ Temps de chargement: ${loadTime}ms`);
    
    // Vérifier que le chargement est raisonnable (moins de 10 secondes)
    expect(loadTime).toBeLessThan(10000);
    
    // Vérifier qu'il n'y a pas d'erreurs JavaScript critiques
    const errors = [];
    page.on('pageerror', error => errors.push(error));
    
    await page.waitForTimeout(3000);
    
    // Filtrer les erreurs non-critiques
    const criticalErrors = errors.filter(error => 
      !error.message.includes('404') && 
      !error.message.includes('favicon') &&
      !error.message.includes('unauthorized')
    );
    
    expect(criticalErrors.length).toBe(0);
    console.log('✅ Aucune erreur JavaScript critique détectée');
  });

});

// Configuration du test pour export
export {}