/**
 * E2E test for Chapter 1 Demo Animation
 * Tests the modernized SEO workflow animation using Playwright
 */

const { test, expect } = require('@playwright/test');

test.describe('Chapter 1 Demo Animation', () => {
  
  test('demo_chapter1_animation - should display new SEO workflow animation', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Look for and click the demo button
    const demoButton = page.locator('text=Lancer la Démo');
    if (await demoButton.count() > 0) {
      await demoButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Test 1: Verify new Chapter 1 title with SEO mention
    await expect(page.locator('text=Chapitre 1 - Recherche et Publication automatique des SEO')).toBeVisible();
    
    // Test 2: Verify old terminal animation is completely removed
    await expect(page.locator('text=scraping-terminal.ai')).not.toBeVisible();
    await expect(page.locator('text=Scanning Amazon prices')).not.toBeVisible();
    await expect(page.locator('text=Analyzing competitor trends')).not.toBeVisible();
    
    // Test 3: Verify new AI workflow elements are present
    await expect(page.locator('text=Scan du Web')).toBeVisible();
    await expect(page.locator('text=Analyse SEO')).toBeVisible();
    await expect(page.locator('text=Optimisation')).toBeVisible();
    await expect(page.locator('text=Publication')).toBeVisible();
    
    // Test 4: Verify platform badges are displayed
    await expect(page.locator('text=Shopify')).toBeVisible();
    await expect(page.locator('text=WooCommerce')).toBeVisible();
    await expect(page.locator('text=Amazon')).toBeVisible();
    await expect(page.locator('text=eBay')).toBeVisible();
    
    // Test 5: Verify performance metrics are shown
    await expect(page.locator('text=98%')).toBeVisible();
    await expect(page.locator('text=Score SEO moyen')).toBeVisible();
    await expect(page.locator('text=2.4s')).toBeVisible();
    await expect(page.locator('text=Temps de traitement')).toBeVisible();
    await expect(page.locator('text=15+')).toBeVisible();
    await expect(page.locator('text=Plateformes supportées')).toBeVisible();
    
    // Test 6: Verify sub-process indicators
    await expect(page.locator('text=Analyse des tendances')).toBeVisible();
    await expect(page.locator('text=Collecte de données')).toBeVisible();
    await expect(page.locator('text=Mots-clés')).toBeVisible();
    await expect(page.locator('text=+Score SEO')).toBeVisible();
    await expect(page.locator('text=Performance')).toBeVisible();
    
    // Test 7: Verify animation elements are properly structured
    const animatedCircles = page.locator('.w-20.h-20.rounded-full');
    await expect(animatedCircles).toHaveCount(4); // Four main workflow steps
    
    // Test 8: Verify responsive grid structure
    const workflowGrid = page.locator('.grid.grid-cols-1.md\\:grid-cols-4');
    await expect(workflowGrid).toBeVisible();
    
    // Test 9: Verify connecting lines between steps
    const connectingLines = page.locator('.absolute.top-10.left-full');
    await expect(connectingLines.first()).toBeVisible();
    
    // Test 10: Take a screenshot for visual comparison
    await page.screenshot({ 
      path: 'tests/screenshots/chapter1-animation.png',
      fullPage: false,
      quality: 80
    });
  });
  
  test('demo_chapter1_animation - should have proper animation timing', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    const demoButton = page.locator('text=Lancer la Démo');
    if (await demoButton.count() > 0) {
      await demoButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Test animation delays and timing
    const delayedElements = page.locator('[class*="delay-"]');
    await expect(delayedElements.first()).toBeVisible();
    
    // Verify pulse animations
    const pulseElements = page.locator('.animate-pulse');
    await expect(pulseElements.first()).toBeVisible();
    
    // Verify fadeInUp animations  
    const fadeElements = page.locator('.animate-fadeInUp');
    await expect(fadeElements.first()).toBeVisible();
  });
  
  test('demo_chapter1_animation - should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    const demoButton = page.locator('text=Lancer la Démo');
    if (await demoButton.count() > 0) {
      await demoButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Verify mobile responsive layout
    await expect(page.locator('text=Chapitre 1 - Recherche et Publication automatique des SEO')).toBeVisible();
    await expect(page.locator('text=Scan du Web')).toBeVisible();
    
    // Take mobile screenshot
    await page.screenshot({ 
      path: 'tests/screenshots/chapter1-animation-mobile.png',
      fullPage: false,
      quality: 80
    });
  });
  
  test('demo_chapter1_animation - should handle chapter navigation', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    const demoButton = page.locator('text=Lancer la Démo');
    if (await demoButton.count() > 0) {
      await demoButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Verify Chapter 1 is active by default or can be selected
    await expect(page.locator('text=Chapitre 1 - Recherche et Publication automatique des SEO')).toBeVisible();
    
    // Check if there are navigation controls for chapters
    const chapterButtons = page.locator('[class*="chapter"], button:has-text("Chapitre")');
    if (await chapterButtons.count() > 0) {
      // Test chapter switching if available
      const firstChapter = chapterButtons.first();
      await firstChapter.click();
      await page.waitForTimeout(1000);
      
      // Verify the animation is still working after navigation
      await expect(page.locator('text=Scan du Web')).toBeVisible();
    }
  });
});

module.exports = {};