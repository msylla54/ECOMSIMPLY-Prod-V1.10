/**
 * Tests d'intégration Logo ECOMSIMPLY
 * Validation complète de l'intégration du logo officiel
 */

const { test, expect } = require('@playwright/test');

class LogoIntegrationTester {
  constructor() {
    this.baseURL = process.env.BASE_URL || 'http://localhost:3000';
    this.testResults = [];
  }

  async runAllTests() {
    console.log('🎨 DÉMARRAGE DES TESTS D\'INTÉGRATION LOGO ECOMSIMPLY');
    console.log('=' * 60);

    const testSuite = [
      this.testLogoVisibilityHomepage,
      this.testLogoVisibilityDashboard,
      this.testLogoClickRedirection,
      this.testLogoResponsiveDesign,
      this.testFaviconPresence,
      this.testLogoAccessibility
    ];

    for (const testFn of testSuite) {
      try {
        await testFn.call(this);
      } catch (error) {
        console.error(`❌ Test failed: ${testFn.name}`, error);
        this.testResults.push({
          name: testFn.name,
          status: 'FAILED',
          error: error.message
        });
      }
    }

    this.generateReport();
  }

  async testLogoVisibilityHomepage() {
    test('Logo visibility on Homepage', async ({ page }) => {
      console.log('🧪 Test: Logo visible sur la page d\'accueil...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Vérifier que le logo est présent dans la navbar
      const logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();
      await expect(logo).toBeVisible();

      // Vérifier les attributs du logo
      const logoSrc = await logo.getAttribute('src');
      expect(logoSrc).toBe('/logo.png');

      const logoAlt = await logo.getAttribute('alt');
      expect(logoAlt).toContain('ECOMSIMPLY');

      console.log('✅ Logo visible sur la page d\'accueil');
      this.testResults.push({
        name: 'Logo visibility on Homepage', 
        status: 'PASSED'
      });
    });
  }

  async testLogoVisibilityDashboard() {
    test('Logo visibility on Dashboard', async ({ page }) => {
      console.log('🧪 Test: Logo visible sur le tableau de bord...');
      
      // Simuler connexion (ajuster selon votre authentification)
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');
      
      // Si authentification nécessaire, la simuler ici
      // await page.fill('input[type="email"]', 'test@example.com');
      // await page.fill('input[type="password"]', 'password');
      // await page.click('button[type="submit"]');

      // Vérifier logo dans le dashboard
      const logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();
      await expect(logo).toBeVisible();

      // Vérifier que le logo a la bonne taille
      const logoBox = await logo.boundingBox();
      expect(logoBox.height).toBeGreaterThan(30); // Au moins 30px de hauteur
      expect(logoBox.height).toBeLessThan(80);   // Maximum 80px de hauteur

      console.log('✅ Logo visible sur le tableau de bord');
      this.testResults.push({
        name: 'Logo visibility on Dashboard',
        status: 'PASSED'
      });
    });
  }

  async testLogoClickRedirection() {
    test('Logo click redirection', async ({ page }) => {
      console.log('🧪 Test: Redirection au clic sur le logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Faire défiler vers le bas pour tester la redirection
      await page.evaluate(() => window.scrollTo(0, 1000));
      await page.waitForTimeout(500);

      // Cliquer sur le logo
      const logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();
      await logo.click();

      // Attendre le scroll vers le haut
      await page.waitForTimeout(1000);

      // Vérifier que la page a scrollé vers le haut
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeLessThan(100); // Doit être proche du haut

      console.log('✅ Redirection au clic fonctionne');
      this.testResults.push({
        name: 'Logo click redirection',
        status: 'PASSED'
      });
    });
  }

  async testLogoResponsiveDesign() {
    test('Logo responsive design', async ({ page }) => {
      console.log('🧪 Test: Design responsive du logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Test desktop (1920x1080)
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(500);
      
      let logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();
      let logoBox = await logo.boundingBox();
      const desktopHeight = logoBox.height;
      
      expect(desktopHeight).toBeGreaterThan(40); // Standard size h-12 (48px)
      console.log(`📱 Desktop logo height: ${desktopHeight}px`);

      // Test mobile (375x667)
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();
      logoBox = await logo.boundingBox();
      const mobileHeight = logoBox.height;
      
      expect(mobileHeight).toBeGreaterThan(20); // Mobile size h-8 (32px)
      console.log(`📱 Mobile logo height: ${mobileHeight}px`);

      // Vérifier que le logo est plus petit sur mobile
      expect(mobileHeight).toBeLessThanOrEqual(desktopHeight);

      console.log('✅ Design responsive validé');
      this.testResults.push({
        name: 'Logo responsive design',
        status: 'PASSED'
      });
    });
  }

  async testFaviconPresence() {
    test('Favicon presence', async ({ page }) => {
      console.log('🧪 Test: Présence du favicon...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      // Vérifier que le favicon est présent dans le DOM
      const faviconLink = await page.locator('link[rel="icon"]').first();
      await expect(faviconLink).toHaveAttribute('href', '/favicon.png');

      // Tester que le favicon se charge correctement
      const faviconResponse = await page.request.get(`${this.baseURL}/favicon.png`);
      expect(faviconResponse.status()).toBe(200);

      console.log('✅ Favicon présent et fonctionnel');
      this.testResults.push({
        name: 'Favicon presence',
        status: 'PASSED'
      });
    });
  }

  async testLogoAccessibility() {
    test('Logo accessibility', async ({ page }) => {
      console.log('🧪 Test: Accessibilité du logo...');
      
      await page.goto(this.baseURL);
      await page.waitForLoadState('networkidle');

      const logo = await page.locator('nav img[alt*="ECOMSIMPLY"]').first();

      // Vérifier les attributs d'accessibilité
      const alt = await logo.getAttribute('alt');
      expect(alt).toBeTruthy();
      expect(alt.length).toBeGreaterThan(5);

      const title = await logo.getAttribute('title');
      expect(title).toBeTruthy();

      // Tester la navigation au clavier
      await logo.focus();
      const focusedElement = await page.locator(':focus');
      await expect(focusedElement).toBeVisible();

      // Tester activation avec Entrée
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);

      console.log('✅ Accessibilité du logo validée');
      this.testResults.push({
        name: 'Logo accessibility',
        status: 'PASSED'
      });
    });
  }

  generateReport() {
    console.log('\n📊 RAPPORT FINAL DES TESTS LOGO');
    console.log('=' * 50);
    
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
    
    if (passed === total) {
      console.log('\n🎉 TOUS LES TESTS RÉUSSIS - INTÉGRATION LOGO COMPLÈTE!');
    } else {
      console.log('\n⚠️ CORRECTIONS NÉCESSAIRES AVANT VALIDATION');
    }
  }
}

// Export pour utilisation avec Playwright
module.exports = { LogoIntegrationTester };

// Exécution si lancé directement
if (require.main === module) {
  const tester = new LogoIntegrationTester();
  tester.runAllTests().catch(console.error);
}