#!/bin/bash

# 🚀 QUICK COMPARE SCRIPT - ECOMSIMPLY UI/UX
# Relance build local, ouvre preview et prend screenshots comparatifs

set -e

echo "🔍 QUICK COMPARE ECOMSIMPLY - Démarrage..."

# Configuration
LOCAL_PORT=3001
PREVIEW_URL="https://ecomsimply-deploy.preview.emergentagent.com"
PROD_URL="https://www.ecomsimply.com"
SCREENSHOT_DIR="./reports/ui-sync/screenshots"

# Créer dossier screenshots
mkdir -p "$SCREENSHOT_DIR"

echo "📁 Screenshots seront sauvés dans: $SCREENSHOT_DIR"

# 1. Build frontend local
echo "🔨 Build frontend local..."
cd frontend
npm run build
echo "✅ Build terminé"

# 2. Démarrer serveur local
echo "🚀 Démarrage serveur local sur port $LOCAL_PORT..."
nohup serve -s build -p $LOCAL_PORT > ../serve.log 2>&1 &
SERVER_PID=$!
sleep 3

# Vérifier serveur démarré
if curl -s -f "http://localhost:$LOCAL_PORT" > /dev/null; then
    echo "✅ Serveur local démarré avec succès"
else
    echo "❌ Erreur: Serveur local n'a pas démarré"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

cd ..

# 3. Prendre screenshots avec Playwright
echo "📸 Prise de screenshots comparatifs..."

# Screenshot local
echo "  📱 Local build..."
python3 << EOF
import asyncio
from playwright.async_api import async_playwright

async def take_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        try:
            await page.goto("http://localhost:$LOCAL_PORT", wait_until="load")
            await page.screenshot(path="$SCREENSHOT_DIR/local_build.png", quality=80)
            print("✅ Screenshot local pris")
        except Exception as e:
            print(f"❌ Erreur screenshot local: {e}")
        finally:
            await browser.close()

asyncio.run(take_screenshot())
EOF

# Screenshot preview
echo "  🔍 Preview environment..."
python3 << EOF
import asyncio
from playwright.async_api import async_playwright

async def take_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        try:
            await page.goto("$PREVIEW_URL", wait_until="load")
            await page.screenshot(path="$SCREENSHOT_DIR/preview_env.png", quality=80)
            print("✅ Screenshot preview pris")
        except Exception as e:
            print(f"❌ Erreur screenshot preview: {e}")
        finally:
            await browser.close()

asyncio.run(take_screenshot())
EOF

# Screenshot production
echo "  🌐 Production..."
python3 << EOF
import asyncio
from playwright.async_api import async_playwright

async def take_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        try:
            await page.goto("$PROD_URL", wait_until="load")
            await page.screenshot(path="$SCREENSHOT_DIR/production.png", quality=80)
            print("✅ Screenshot production pris")
        except Exception as e:
            print(f"❌ Erreur screenshot production: {e}")
        finally:
            await browser.close()

asyncio.run(take_screenshot())
EOF

# 4. Arrêter serveur local
echo "🛑 Arrêt serveur local..."
kill $SERVER_PID 2>/dev/null || true

# 5. Résumé
echo ""
echo "🎯 COMPARAISON TERMINÉE"
echo "================================"
echo "📁 Screenshots disponibles dans: $SCREENSHOT_DIR"
echo "   - local_build.png"
echo "   - preview_env.png" 
echo "   - production.png"
echo ""
echo "👀 Ouvrir les images pour comparaison visuelle"
echo "💡 Utiliser un outil de diff d'images pour analyse précise"
echo ""
echo "✅ Quick compare terminé avec succès!"