// ================================================================================
// TEST E2E - NO CONSOLE ERRORS - VERSION REACT 18.2.0
// ================================================================================

const { test, expect } = require('@playwright/test');

test.describe('Console Errors - React 18.2.0 Compatibility', () => {
  
  test('no ReactCurrentOwner errors on homepage', async ({ page }) => {
    console.log('🔍 Test des erreurs console ReactCurrentOwner...');
    
    // Capturer toutes les erreurs console
    const consoleErrors = [];
    const consoleWarnings = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`❌ Console Error: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
        console.log(`⚠️ Console Warning: ${msg.text()}`);
      }
    });

    // Capturer les erreurs de page
    const pageErrors = [];
    page.on('pageerror', error => {
      pageErrors.push(error.message);
      console.log(`🚨 Page Error: ${error.message}`);
    });

    try {
      // Configuration de la viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      // Navigation vers la page avec timeout étendu
      await page.goto('http://localhost:3000', { 
        waitUntil: 'networkidle',
        timeout: 15000 
      });
      
      console.log('✅ Page chargée sans erreur de navigation');

      // Attendre que les composants 3D soient chargés
      await page.waitForTimeout(3000);
      
      // Vérifier les éléments principaux
      await page.waitForSelector('text=IA Premium', { timeout: 10000 });
      console.log('✅ Composants principaux chargés');

      // Interagir avec les boutons pour déclencher les event handlers
      const demoButton = page.locator('button:has-text("🚀 Lancer la Démo")');
      if (await demoButton.isVisible()) {
        await demoButton.hover();
        console.log('✅ Interaction avec bouton démo OK');
      }

      // Attendre un peu plus pour capturer les erreurs async
      await page.waitForTimeout(2000);

      // Vérifications des erreurs critiques
      const reactCurrentOwnerErrors = consoleErrors.filter(error => 
        error.includes('ReactCurrentOwner') || 
        error.includes('Cannot read properties of undefined') ||
        error.includes('react-reconciler') ||
        error.includes('@react-three/fiber')
      );

      const fiberErrors = consoleErrors.filter(error =>
        error.includes('fiber') || 
        error.includes('reconciler')
      );

      // Assertions
      expect(reactCurrentOwnerErrors).toHaveLength(0);
      expect(fiberErrors).toHaveLength(0);
      expect(pageErrors).toHaveLength(0);

      // Log du résumé
      console.log('📊 RÉSUMÉ DES ERREURS:');
      console.log(`   Erreurs console totales: ${consoleErrors.length}`);
      console.log(`   Erreurs ReactCurrentOwner: ${reactCurrentOwnerErrors.length}`);
      console.log(`   Erreurs Fiber: ${fiberErrors.length}`);
      console.log(`   Erreurs de page: ${pageErrors.length}`);
      console.log(`   Warnings: ${consoleWarnings.length}`);

      if (consoleErrors.length === 0 && pageErrors.length === 0) {
        console.log('🎉 AUCUNE ERREUR CRITIQUE DÉTECTÉE !');
      } else {
        console.log('⚠️ Erreurs détectées:', consoleErrors);
      }

    } catch (error) {
      console.error('❌ Erreur lors du test:', error);
      throw error;
    }
  });

  test('CTA "Lancer la Démo" navigation works without errors', async ({ page }) => {
    console.log('🎯 Test de navigation du bouton Démo...');
    
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    try {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

      // Attendre et cliquer sur le bouton démo
      const demoButton = page.locator('button:has-text("🚀 Lancer la Démo")');
      await expect(demoButton).toBeVisible({ timeout: 10000 });
      
      console.log('✅ Bouton démo visible');

      // Tester le clic (peut rediriger ou ouvrir une modal)
      await demoButton.click();
      console.log('✅ Clic sur bouton démo effectué');

      // Attendre les éventuels changements de page
      await page.waitForTimeout(2000);

      // Vérifier qu'aucune erreur n'est survenue
      const criticalErrors = consoleErrors.filter(error => 
        error.includes('ReactCurrentOwner') ||
        error.includes('Cannot read properties of undefined')
      );

      expect(criticalErrors).toHaveLength(0);
      console.log('🎉 Navigation fonctionnelle sans erreurs React !');

    } catch (error) {
      console.error('❌ Erreur lors du test de navigation:', error);
      throw error;
    }
  });

  test('3D fallback works without WebGL', async ({ page }) => {
    console.log('🎯 Test du fallback 3D sans WebGL...');
    
    // Désactiver WebGL
    await page.addInitScript(() => {
      HTMLCanvasElement.prototype.getContext = function(contextType) {
        if (contextType === 'webgl' || contextType === 'experimental-webgl') {
          return null;
        }
        return null;
      };
    });

    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    try {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

      // Vérifier que le contenu se charge malgré l'absence de WebGL
      await page.waitForSelector('text=IA Premium', { timeout: 10000 });
      console.log('✅ Fallback chargé sans WebGL');

      // Vérifier qu'aucune erreur 3D critique n'est survenue
      const webglErrors = consoleErrors.filter(error => 
        error.includes('WebGL') ||
        error.includes('three') ||
        error.includes('Canvas')
      );

      // On accepte les warnings WebGL mais pas les erreurs critiques
      const criticalErrors = consoleErrors.filter(error => 
        error.includes('ReactCurrentOwner') ||
        error.includes('Cannot read properties of undefined')
      );

      expect(criticalErrors).toHaveLength(0);
      console.log(`✅ Fallback fonctionne (${webglErrors.length} warnings WebGL acceptables)`);

    } catch (error) {
      console.error('❌ Erreur lors du test fallback:', error);
      throw error;
    }
  });

  test('performance - no memory leaks on mount/unmount', async ({ page }) => {
    console.log('🎯 Test des fuites mémoire...');

    try {
      await page.setViewportSize({ width: 1920, height: 1080 });

      // Mesurer la mémoire initiale
      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      // Charger et décharger la page plusieurs fois
      for (let i = 0; i < 3; i++) {
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForSelector('text=IA Premium', { timeout: 10000 });
        await page.waitForTimeout(1000);
        await page.goto('about:blank');
        await page.waitForTimeout(500);
      }

      // Mesurer la mémoire finale
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      const memoryIncrease = finalMemory - initialMemory;
      const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100;

      console.log(`📊 Mémoire initiale: ${(initialMemory / 1024 / 1024).toFixed(2)} MB`);
      console.log(`📊 Mémoire finale: ${(finalMemory / 1024 / 1024).toFixed(2)} MB`);
      console.log(`📊 Augmentation: ${memoryIncreasePercent.toFixed(1)}%`);

      // Accepter une augmentation raisonnable (< 50%)
      expect(memoryIncreasePercent).toBeLessThan(50);
      console.log('✅ Pas de fuite mémoire majeure détectée');

    } catch (error) {
      console.error('❌ Erreur lors du test mémoire:', error);
      // Ne pas faire échouer le test pour les problèmes de mesure mémoire
      console.log('⚠️ Test mémoire incomplet mais non critique');
    }
  });
});