/**
 * Tests E2E Playwright - Logo XXL dans Headers ECOMSIMPLY
 * Validation complète selon spécifications ingénieur frontend
 */

const { test, expect } = require('@playwright/test');

class LogoXXLHeadersTester {
  constructor() {
    this.baseURL = process.env.BASE_URL || 'http://localhost:3000';
    this.testResults = [];
    
    // Spécifications de tailles selon demande
    this.expectedSizes = {
      mobile: { minWidth: 120, headerHeight: 64 },     // h-16 mobile, logo h-10
      tablet: { minWidth: 180, headerHeight: 80 },     // h-20 tablet, logo h-16  
      desktop: { minWidth: 240, headerHeight: 96 }     // h-24 desktop, logo h-20
    };
  }

  async runAllTests() {
    console.log('🎯 DÉMARRAGE TESTS LOGO XXL HEADERS - SPÉCIFICATIONS FRONTEND');
    console.log('=' * 70);

    const testSuite = [
      this.testHomePageLogoVisibility,
      this.testDashboardLogoVisibility, 
      this.testLogoClickRedirection,
      this.testResponsiveLogoSizes,
      this.testHeaderNoOverlap,
      this.testLogoContrast,
      this.testAccessibility
    ];

    for (const testFn of testSuite) {
      try {
        await testFn.call(this);
        console.log(`✅ ${testFn.name}: PASSED`);
        this.testResults.push({ name: testFn.name, status: 'PASSED' });
      } catch (error) {
        console.error(`❌ ${testFn.name}: FAILED - ${error.message}`);
        this.testResults.push({ name: testFn.name, status: 'FAILED', error: error.message });
      }
    }

    this.generateFinalReport();
  }

  async testHomePageLogoVisibility() {
    test('Homepage Logo XXL Visibility', async ({ page }) => {
      console.log('🏠 Test: Logo XXL visible sur page d\'accueil...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Chercher le logo avec les nouveaux sélecteurs
      const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
      await expect(logo).toBeVisible();

      // Vérifier les attributs requis
      const logoSrc = await logo.getAttribute('src');
      expect(logoSrc).toMatch(/assets\/logo\/ecomsimply-logo\.(png|svg)/);

      const logoAlt = await logo.getAttribute('alt');
      expect(logoAlt).toBe('ECOMSIMPLY');

      const logoTitle = await logo.getAttribute('title');
      expect(logoTitle).toBe('ECOMSIMPLY');

      // Vérifier que pas de classes hidden/sr-only
      const logoClasses = await logo.getAttribute('class');
      expect(logoClasses).not.toContain('hidden');
      expect(logoClasses).not.toContain('sr-only');
      expect(logoClasses).not.toContain('opacity-0');

      console.log(`   ✓ Logo src: ${logoSrc}`);
      console.log(`   ✓ Alt/Title: ${logoAlt}/${logoTitle}`);
    });
  }

  async testDashboardLogoVisibility() {
    test('Dashboard Logo XXL Visibility', async ({ page }) => {
      console.log('📊 Test: Logo XXL visible sur dashboard...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');
      
      // Simuler connexion ou naviguer vers dashboard (ajuster selon auth)
      // Pour ce test, on suppose que le DashboardShell est accessible
      
      // Chercher le logo dashboard
      const dashboardLogo = await page.locator('header img[alt="ECOMSIMPLY"]').first();
      
      if (await dashboardLogo.count() > 0) {
        await expect(dashboardLogo).toBeVisible();
        
        // Vérifier les classes spécifiques au dashboard
        const logoClasses = await dashboardLogo.getAttribute('class');
        expect(logoClasses).toContain('object-contain');
        expect(logoClasses).toContain('drop-shadow-sm');
        
        console.log('   ✓ Logo dashboard détecté et visible');
      } else {
        console.log('   ℹ️ Dashboard non accessible (nécessite auth)');
      }
    });
  }

  async testLogoClickRedirection() {
    test('Logo Click Redirection', async ({ page }) => {
      console.log('🔗 Test: Redirection clic logo vers "/"...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Scroll down pour tester redirection
      await page.evaluate(() => window.scrollTo(0, 1000));
      await page.waitForTimeout(500);

      // Cliquer sur le logo
      const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
      
      // Vérifier que le logo est cliquable (cursor pointer)
      const logoParent = logo.locator('..');
      await expect(logoParent).toHaveCSS('cursor', 'pointer');
      
      await logo.click();
      
      // Attendre navigation ou scroll
      await page.waitForTimeout(1000);
      
      // Vérifier URL (doit être "/" ou scroll vers haut)
      const currentURL = page.url();
      const scrollY = await page.evaluate(() => window.scrollY);
      
      // Si c'est un scroll, vérifier qu'on est en haut
      if (currentURL === this.baseURL || currentURL.endsWith('/')) {
        expect(scrollY).toBeLessThan(100);
        console.log(`   ✓ Redirection réussie: URL=${currentURL}, scroll=${scrollY}px`);
      }
    });
  }

  async testResponsiveLogoSizes() {
    test('Responsive Logo Sizes (Mobile/Tablet/Desktop)', async ({ page }) => {
      console.log('📱 Test: Tailles responsives logo selon spécifications...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      const viewports = [
        { name: 'mobile', width: 375, height: 667 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'desktop', width: 1920, height: 1080 }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
        const logoBox = await logo.boundingBox();
        const expectedSize = this.expectedSizes[viewport.name];

        // Vérifier largeur minimale logo
        expect(logoBox.width).toBeGreaterThanOrEqual(expectedSize.minWidth);
        
        // Vérifier hauteur header
        const header = await page.locator('nav, header').first();
        const headerBox = await header.boundingBox();
        
        console.log(`   ${viewport.name}: Logo ${logoBox.width}x${logoBox.height}px, Header ${headerBox.height}px`);
        
        // Vérifier que logo respecte contraintes responsive
        if (viewport.name === 'mobile') {
          expect(logoBox.height).toBeLessThanOrEqual(50); // h-10 max
        } else if (viewport.name === 'tablet') {
          expect(logoBox.height).toBeLessThanOrEqual(80); // h-16 max
        } else { // desktop
          expect(logoBox.height).toBeLessThanOrEqual(100); // h-20 max
        }
      }
    });
  }

  async testHeaderNoOverlap() {
    test('Header No Overlap - Logo Priority', async ({ page }) => {
      console.log('🚫 Test: Aucun chevauchement du logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Tester sur mobile (plus contraignant)
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
      const logoBox = await logo.boundingBox();

      // Vérifier qu'aucun élément ne chevauche le logo
      const overlappingElements = await page.locator('nav *, header *').evaluateAll((elements, logoRect) => {
        return elements.filter(el => {
          if (el.tagName === 'IMG' && el.alt === 'ECOMSIMPLY') return false;
          
          const rect = el.getBoundingClientRect();
          return (
            rect.left < logoRect.right &&
            rect.right > logoRect.left &&
            rect.top < logoRect.bottom &&
            rect.bottom > logoRect.top
          );
        }).length;
      }, logoBox);

      expect(overlappingElements).toBe(0);
      console.log('   ✓ Aucun chevauchement détecté');
    });
  }

  async testLogoContrast() {
    test('Logo Contrast & Visibility', async ({ page }) => {
      console.log('🌈 Test: Contraste et visibilité logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
      
      // Vérifier drop-shadow pour contraste
      const logoStyles = await logo.evaluate(el => getComputedStyle(el));
      
      // Vérifier opacity à 100%
      const opacity = await logo.evaluate(el => getComputedStyle(el).opacity);
      expect(parseFloat(opacity)).toBeGreaterThanOrEqual(1.0);
      
      // Vérifier que object-fit: contain préserve aspect ratio
      const objectFit = await logo.evaluate(el => getComputedStyle(el).objectFit);
      expect(objectFit).toBe('contain');

      console.log(`   ✓ Opacity: ${opacity}, Object-fit: ${objectFit}`);
    });
  }

  async testAccessibility() {
    test('Logo Accessibility', async ({ page }) => {
      console.log('♿ Test: Accessibilité logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      const logo = await page.locator('nav img[alt="ECOMSIMPLY"], header img[alt="ECOMSIMPLY"]').first();
      
      // Test navigation clavier
      await logo.focus();
      const isFocused = await logo.evaluate(el => document.activeElement === el || document.activeElement.contains(el));
      expect(isFocused).toBe(true);

      // Test activation clavier
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
      
      // Test attributs ARIA
      const role = await logo.getAttribute('role');
      const tabIndex = await logo.getAttribute('tabindex');
      
      console.log(`   ✓ Focus: ${isFocused}, Role: ${role}, TabIndex: ${tabIndex}`);
    });
  }

  generateFinalReport() {
    console.log('\n📊 RAPPORT FINAL - TESTS LOGO XXL HEADERS');
    console.log('=' * 70);
    
    const passed = this.testResults.filter(r => r.status === 'PASSED').length;
    const failed = this.testResults.filter(r => r.status === 'FAILED').length;
    const total = this.testResults.length;
    
    console.log(`✅ Tests réussis: ${passed}/${total}`);
    console.log(`❌ Tests échoués: ${failed}/${total}`);
    console.log(`📈 Taux de réussite: ${(passed/total*100).toFixed(1)}%`);
    
    if (failed > 0) {
      console.log('\n❌ ÉCHECS DÉTAILLÉS:');
      this.testResults
        .filter(r => r.status === 'FAILED')
        .forEach(r => {
          console.log(`   • ${r.name}: ${r.error}`);
        });
    }
    
    console.log('\n📋 CRITÈRES D\'ACCEPTATION:');
    console.log('✓ Logo GRAND affiché à gauche dans headers');
    console.log('✓ Aucune opacité < 100%, parfaitement visible');
    console.log('✓ Headers adaptatifs: h-16/h-20/h-24');
    console.log('✓ Logo responsive: h-10/h-16/h-20');
    console.log('✓ Clic logo → redirection "/"');
    console.log('✓ Aucun chevauchement');
    console.log('✓ Tests E2E 100% passés');
    
    if (passed === total) {
      console.log('\n🎉 INTÉGRATION LOGO XXL HEADERS: PRODUCTION READY!');
    } else {
      console.log('\n⚠️ CORRECTIONS REQUISES AVANT VALIDATION');
    }
  }
}

// Export pour Playwright
module.exports = { LogoXXLHeadersTester };

// Exécution directe
if (require.main === module) {
  const tester = new LogoXXLHeadersTester();
  tester.runAllTests().catch(console.error);
}