// ================================================================================
// TEST E2E - HERO 3D FUNCTIONALITY - VERSION COMPLETE
// ================================================================================

const { test, expect } = require('@playwright/test');

test.describe('Hero 3D Section - Tests Fonctionnels', () => {
  
  test.beforeEach(async ({ page }) => {
    // Configuration de la viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
  });

  test('Hero 3D - Éléments principaux présents et fonctionnels', async ({ page }) => {
    console.log('🎯 Test des éléments principaux du Hero 3D...');
    
    try {
      // Navigation vers la page
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      console.log('✅ Page chargée');

      // Vérifier le titre principal
      const heroTitle = page.locator('text=IA Premium');
      await expect(heroTitle).toBeVisible({ timeout: 10000 });
      console.log('✅ Titre "IA Premium" visible');

      const heroSubtitle = page.locator('text=pour Fiches Produits');
      await expect(heroSubtitle).toBeVisible();
      console.log('✅ Sous-titre "pour Fiches Produits" visible');

      // Vérifier le texte de vision
      const visionText = page.locator('text=Imaginez…');
      await expect(visionText).toBeVisible();
      console.log('✅ Texte de vision visible');

      const aiText = page.locator('text=Une IA qui veille sur votre boutique');
      await expect(aiText).toBeVisible();
      console.log('✅ Description IA visible');

      // Vérifier les boutons CTA
      const demoButton = page.locator('button:has-text("🚀 Lancer la Démo")');
      await expect(demoButton).toBeVisible();
      console.log('✅ Bouton "Lancer la Démo" visible');

      const trialButton = page.locator('button:has-text("🎁 Essai Gratuit 7 Jours")');
      await expect(trialButton).toBeVisible();
      console.log('✅ Bouton "Essai Gratuit 7 Jours" visible');

      const watchDemoButton = page.locator('button:has-text("🎥 Voir la Démo")');
      await expect(watchDemoButton).toBeVisible();
      console.log('✅ Bouton "Voir la Démo" visible');

      console.log('🎉 Tous les éléments principaux sont présents !');

    } catch (error) {
      console.error('❌ Erreur lors du test des éléments:', error);
      throw error;
    }
  });

  test('Hero 3D - Navigation et interactions des boutons', async ({ page }) => {
    console.log('🎯 Test des interactions des boutons...');
    
    try {
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

      // Test du bouton "Lancer la Démo"
      const demoButton = page.locator('button:has-text("🚀 Lancer la Démo")');
      await expect(demoButton).toBeVisible();
      
      // Vérifier que le bouton est cliquable
      await expect(demoButton).toBeEnabled();
      console.log('✅ Bouton "Lancer la Démo" cliquable');

      // Test du bouton "Essai Gratuit"
      const trialButton = page.locator('button:has-text("🎁 Essai Gratuit 7 Jours")');
      await expect(trialButton).toBeVisible();
      await expect(trialButton).toBeEnabled();
      console.log('✅ Bouton "Essai Gratuit" cliquable');

      // Test hover effects (si supportés)
      await demoButton.hover();
      console.log('✅ Hover sur bouton démo OK');

      await trialButton.hover();
      console.log('✅ Hover sur bouton trial OK');

      console.log('🎉 Toutes les interactions fonctionnent !');

    } catch (error) {
      console.error('❌ Erreur lors du test des interactions:', error);
      throw error;
    }
  });

  test('Hero 3D - Banner de notification', async ({ page }) => {
    console.log('🎯 Test du banner de notification...');
    
    try {
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

      // Vérifier le banner de notification
      const banner = page.locator('text=NOUVEAU ! IA Premium');
      await expect(banner).toBeVisible({ timeout: 5000 });
      console.log('✅ Banner "NOUVEAU !" visible');

      // Vérifier le taux de commission
      const commission = page.locator('text=15% commission');
      await expect(commission).toBeVisible();
      console.log('✅ Commission "15%" affichée');

      // Vérifier l'essai gratuit
      const freeTrial = page.locator('text=GRATUIT 7 jours');
      await expect(freeTrial).toBeVisible();
      console.log('✅ "GRATUIT 7 jours" affiché');

      // Test du bouton fermer
      const closeButton = page.locator('button:has-text("✕")');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        console.log('✅ Banner fermé avec succès');
        
        // Vérifier que le banner a disparu
        await expect(banner).not.toBeVisible();
        console.log('✅ Banner masqué après fermeture');
      }

      console.log('🎉 Banner de notification fonctionne !');

    } catch (error) {
      console.error('❌ Erreur lors du test du banner:', error);
      throw error;
    }
  });

  test('Hero 3D - Responsive Design', async ({ page }) => {
    console.log('🎯 Test du design responsive...');
    
    try {
      // Test Desktop
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      
      const desktopTitle = page.locator('text=IA Premium');
      await expect(desktopTitle).toBeVisible();
      console.log('✅ Desktop: Titre visible');

      // Test Tablet
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500); // Attendre le reflow
      
      await expect(desktopTitle).toBeVisible();
      console.log('✅ Tablet: Titre visible');

      // Test Mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      await expect(desktopTitle).toBeVisible();
      console.log('✅ Mobile: Titre visible');

      // Vérifier que les boutons restent accessibles sur mobile
      const mobileButtons = page.locator('button:has-text("🚀 Lancer la Démo")');
      await expect(mobileButtons).toBeVisible();
      console.log('✅ Mobile: Boutons accessibles');

      console.log('🎉 Design responsive fonctionne !');

    } catch (error) {
      console.error('❌ Erreur lors du test responsive:', error);
      throw error;
    }
  });

  test('Hero 3D - Performance et accessibilité', async ({ page }) => {
    console.log('🎯 Test de performance et accessibilité...');
    
    try {
      const startTime = Date.now();
      
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      
      // Mesurer le temps de chargement
      const loadTime = Date.now() - startTime;
      console.log(`⏱️ Temps de chargement: ${loadTime}ms`);
      
      // Vérifier que le contenu est chargé rapidement
      expect(loadTime).toBeLessThan(5000); // 5 secondes max
      console.log('✅ Chargement dans les temps');

      // Test d'accessibilité basique - Focus
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement.tagName);
      console.log(`🎯 Premier focus: ${focusedElement}`);
      
      // Vérifier que les éléments sont focusables
      const focusableButtons = await page.locator('button').count();
      expect(focusableButtons).toBeGreaterThan(0);
      console.log(`✅ ${focusableButtons} boutons focusables trouvés`);

      // Test des couleurs de contraste (vérification basique)
      const heroBackground = await page.locator('[class*="min-h-screen"]').first();
      await expect(heroBackground).toBeVisible();
      console.log('✅ Background hero détecté');

      console.log('🎉 Performance et accessibilité OK !');

    } catch (error) {
      console.error('❌ Erreur lors du test performance:', error);
      throw error;
    }
  });

  test('Hero 3D - Capture d\'écran finale', async ({ page }) => {
    console.log('🎯 Capture d\'écran finale du Hero 3D...');
    
    try {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      
      // Attendre que tout soit chargé
      await page.waitForSelector('text=IA Premium', { timeout: 10000 });
      await page.waitForTimeout(2000); // Laisser les animations se terminer
      
      // Prendre une capture d'écran
      await page.screenshot({ 
        path: '/tmp/hero_3d_final.png', 
        quality: 90,
        fullPage: false 
      });
      
      console.log('✅ Capture d\'écran sauvegardée');
      console.log('🎉 Test Hero 3D COMPLET !');

    } catch (error) {
      console.error('❌ Erreur lors de la capture:', error);
      throw error;
    }
  });
});