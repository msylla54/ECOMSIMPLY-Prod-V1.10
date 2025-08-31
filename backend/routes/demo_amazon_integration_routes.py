# Demo Amazon Integration Routes - Pour tests frontend sans authentification
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)

# Router pour démo Amazon Integration
demo_amazon_integration_router = APIRouter(prefix="/api/demo/amazon", tags=["Demo Amazon Integration"])

@demo_amazon_integration_router.get("/status")
async def demo_amazon_status():
    """
    Endpoint démo pour status Amazon sans authentification
    Simule différents états de connexion pour tests frontend
    """
    return {
        "status": "none",
        "message": "Aucune connexion Amazon (DEMO)",
        "connections_count": 0,
        "active_marketplaces": [],
        "demo_mode": True
    }

@demo_amazon_integration_router.get("/marketplaces")
async def demo_amazon_marketplaces():
    """
    Endpoint démo pour marketplaces Amazon supportés
    """
    return {
        "marketplaces": [
            {
                "marketplace_id": "A13V1IB3VIYZZH",
                "country_code": "FR",
                "currency": "EUR",
                "name": "Amazon.fr",
                "region": "eu"
            },
            {
                "marketplace_id": "A1PA6795UKMFR9",
                "country_code": "DE", 
                "currency": "EUR",
                "name": "Amazon.de",
                "region": "eu"
            },
            {
                "marketplace_id": "ATVPDKIKX0DER",
                "country_code": "US",
                "currency": "USD",
                "name": "Amazon.com",
                "region": "na"
            },
            {
                "marketplace_id": "A1F83G8C2ARO7P",
                "country_code": "UK",
                "currency": "GBP",
                "name": "Amazon.co.uk",
                "region": "eu"
            },
            {
                "marketplace_id": "APJ6JRA9NG5V4",
                "country_code": "IT",
                "currency": "EUR",
                "name": "Amazon.it",
                "region": "eu"
            },
            {
                "marketplace_id": "A1RKKUPIHCS9HS",
                "country_code": "ES",
                "currency": "EUR",
                "name": "Amazon.es",
                "region": "eu"
            }
        ],
        "total_count": 6,
        "demo_mode": True
    }

@demo_amazon_integration_router.post("/connect")
async def demo_amazon_connect():
    """
    Endpoint démo pour simulation connexion Amazon
    """
    return {
        "connection_id": "demo_connection_123",
        "authorization_url": "https://sellercentral-europe.amazon.com/apps/authorize/consent?demo=true",
        "state": "demo_state_12345",
        "expires_at": "2025-01-12T18:00:00Z",
        "marketplace_id": "A13V1IB3VIYZZH",
        "region": "eu",
        "demo_mode": True
    }

@demo_amazon_integration_router.post("/disconnect")
async def demo_amazon_disconnect():
    """
    Endpoint démo pour simulation déconnexion Amazon
    """
    return {
        "status": "revoked",
        "message": "Déconnexion simulée (DEMO)",
        "disconnected_count": 1,
        "demo_mode": True
    }

# PHASE 2 DEMO ENDPOINTS - Générateur de fiches produits
@demo_amazon_integration_router.post("/listings/generate")
async def demo_amazon_listings_generate(product_data: Dict[str, Any]):
    """
    Endpoint démo pour génération de listing Amazon
    Simule la génération IA d'une fiche produit
    """
    import time
    
    # Simulation de temps de génération
    await asyncio.sleep(2)
    
    product_name = product_data.get("product_name", "Produit de test")
    brand = product_data.get("brand", "Marque")
    
    return {
        "listing_id": str(uuid.uuid4()),
        "generated_at": "2025-01-20T15:30:00Z",
        "seo_content": {
            "title": f"{brand} {product_name} - Édition 2025 Premium avec Garantie",
            "bullet_points": [
                f"✅ QUALITÉ PREMIUM - {product_name} avec matériaux haute qualité et finition exceptionnelle",
                f"✅ TECHNOLOGIE AVANCÉE - Dernières innovations intégrées pour performances optimales",
                f"✅ DESIGN ÉLÉGANT - Style moderne et ergonomique adapté à tous les usages",
                f"✅ GARANTIE ÉTENDUE - Service client dédié et garantie constructeur incluse",
                f"✅ LIVRAISON RAPIDE - Expédition immédiate depuis nos entrepôts européens"
            ],
            "description": f"Découvrez le {product_name} de {brand}, un produit d'exception qui allie performance, qualité et design. Conçu avec les dernières technologies, ce produit offre une expérience utilisateur incomparable.\n\nCARACTÉRISTIQUES PRINCIPALES:\n- Matériaux premium sélectionnés\n- Technologie de pointe intégrée\n- Design ergonomique et moderne\n- Compatibilité universelle\n\nBÉNÉFICES:\n- Performance exceptionnelle au quotidien\n- Durabilité et fiabilité garanties\n- Facilité d'utilisation pour tous\n- Service après-vente premium\n\nUTILISATION:\nIdéal pour un usage quotidien, ce produit s'adapte parfaitement à vos besoins. Installation simple et prise en main immédiate.",
            "backend_keywords": f"{product_name.lower()} {brand.lower()} premium qualité technologie design moderne garantie livraison rapide",
            "image_requirements": {
                "main_image": "Image principale haute résolution sur fond blanc",
                "lifestyle_images": "Images d'utilisation en contexte réel",
                "detail_images": "Photos détaillées des caractéristiques",
                "format": "WEBP",
                "quality": 85
            }
        },
        "generation_metadata": {
            "optimization_score": 95,
            "a9_a10_compliant": True,
            "generation_time": 2.1,
            "ai_model": "ECOMSIMPLY-PRO-v2.5",
            "language": "fr"
        },
        "demo_mode": True
    }

@demo_amazon_integration_router.post("/listings/validate")
async def demo_amazon_listings_validate(listing_data: Dict[str, Any]):
    """
    Endpoint démo pour validation de listing Amazon
    Simule la validation selon les règles A9/A10
    """
    import time
    await asyncio.sleep(1)
    
    return {
        "validation_id": str(uuid.uuid4()),
        "validated_at": "2025-01-20T15:32:00Z",
        "overall_status": "APPROVED",
        "validation_score": 100,
        "errors": [],
        "warnings": [],
        "details": {
            "title": {
                "score": 100,
                "status": "APPROVED",
                "length": 65,
                "max_length": 200,
                "issues": []
            },
            "bullets": {
                "score": 100,
                "status": "APPROVED", 
                "count": 5,
                "max_count": 5,
                "avg_length": 98,
                "max_length": 255,
                "issues": []
            },
            "description": {
                "score": 100,
                "status": "APPROVED",
                "length": 892,
                "min_length": 100,
                "max_length": 2000,
                "issues": []
            },
            "keywords": {
                "score": 100,
                "status": "APPROVED",
                "bytes": 127,
                "max_bytes": 250,
                "issues": []
            },
            "images": {
                "score": 100,
                "status": "APPROVED",
                "requirements_met": True,
                "issues": []
            },
            "brand": {
                "score": 100,
                "status": "APPROVED",
                "recognized": True,
                "issues": []
            }
        },
        "summary": "Excellent listing prêt pour publication Amazon",
        "demo_mode": True
    }

@demo_amazon_integration_router.post("/listings/publish")
async def demo_amazon_listings_publish(publish_data: Dict[str, Any]):
    """
    Endpoint démo pour publication listing Amazon
    Simule la publication via SP-API
    """
    import time
    await asyncio.sleep(3)
    
    return {
        "publication_id": str(uuid.uuid4()),
        "published_at": "2025-01-20T15:35:00Z",
        "status": "SUCCESS",
        "sku": f"DEMO-{uuid.uuid4().hex[:8].upper()}",
        "asin": f"B{uuid.uuid4().hex[:9].upper()}",
        "marketplace": "Amazon.fr",
        "feed_id": f"feed_{uuid.uuid4().hex[:12]}",
        "processing_status": "COMPLETED",
        "sp_api_response": {
            "result": "SUCCESS",
            "processing_time": 2.8,
            "feed_submission_id": f"sub_{uuid.uuid4().hex[:16]}"
        },
        "demo_mode": True
    }

@demo_amazon_integration_router.get("/demo-page", response_class=HTMLResponse)
async def demo_amazon_integration_page():
    """Page de démonstration complète Amazon Integration"""
    
    html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECOMSIMPLY - Démo Amazon SP-API Phase 1</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" href="/favicon.png" type="image/png">
    <style>
        .connection-status-none { @apply bg-gray-50 text-gray-600 border-gray-200; }
        .connection-status-connected { @apply bg-green-50 text-green-600 border-green-200; }
        .connection-status-pending { @apply bg-yellow-50 text-yellow-600 border-yellow-200; }
        .connection-status-error { @apply bg-red-50 text-red-600 border-red-200; }
        .connection-status-revoked { @apply bg-gray-50 text-gray-600 border-gray-200; }
    </style>
</head>
<body class="bg-gray-50">
    <div id="demo-amazon-root"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;

        // Composant Générateur de fiche Phase 2
        const DemoAmazonListingGenerator = () => {
            const [step, setStep] = useState('input'); // input, generating, preview, validating, validated, publishing, published
            const [formData, setFormData] = useState({
                product_name: '',
                brand: '',
                category: 'électronique',
                features: '',
                target_keywords: '',
                size: '',
                color: '',
                price: '',
                description: ''
            });
            const [generatedListing, setGeneratedListing] = useState(null);
            const [validationResult, setValidationResult] = useState(null);
            const [publicationResult, setPublicationResult] = useState(null);
            const [loading, setLoading] = useState(false);

            const handleInputChange = (field, value) => {
                setFormData(prev => ({ ...prev, [field]: value }));
            };

            const handleGenerate = async () => {
                if (!formData.product_name || !formData.brand) {
                    alert('Veuillez remplir au moins le nom du produit et la marque');
                    return;
                }

                setLoading(true);
                setStep('generating');

                try {
                    const response = await fetch('/api/demo/amazon/listings/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    setGeneratedListing(result);
                    setStep('preview');
                } catch (error) {
                    alert('Erreur lors de la génération: ' + error.message);
                    setStep('input');
                } finally {
                    setLoading(false);
                }
            };

            const handleValidate = async () => {
                setLoading(true);
                setStep('validating');

                try {
                    const response = await fetch('/api/demo/amazon/listings/validate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(generatedListing)
                    });
                    
                    const result = await response.json();
                    setValidationResult(result);
                    setStep('validated');
                } catch (error) {
                    alert('Erreur lors de la validation: ' + error.message);
                    setStep('preview');
                } finally {
                    setLoading(false);
                }
            };

            const handlePublish = async () => {
                setLoading(true);
                setStep('publishing');

                try {
                    const response = await fetch('/api/demo/amazon/listings/publish', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ listing: generatedListing, validation: validationResult })
                    });
                    
                    const result = await response.json();
                    setPublicationResult(result);
                    setStep('published');
                } catch (error) {
                    alert('Erreur lors de la publication: ' + error.message);
                    setStep('validated');
                } finally {
                    setLoading(false);
                }
            };

            const resetGenerator = () => {
                setStep('input');
                setFormData({
                    product_name: '',
                    brand: '',
                    category: 'électronique',
                    features: '',
                    target_keywords: '',
                    size: '',
                    color: '',
                    price: '',
                    description: ''
                });
                setGeneratedListing(null);
                setValidationResult(null);
                setPublicationResult(null);
            };

            const fillSampleData = () => {
                setFormData({
                    product_name: 'iPhone 15 Pro Max 256GB',
                    brand: 'Apple',
                    category: 'électronique',
                    features: 'Puce A17 Pro, Écran Super Retina XDR 6,7", Système caméra Pro triple 48 Mpx, Châssis titane',
                    target_keywords: 'smartphone, iphone, premium, apple, pro, titanium',
                    size: '6,7 pouces',
                    color: 'Titane Naturel',
                    price: '1479',
                    description: 'Le smartphone le plus avancé d\'Apple avec puce A17 Pro et design titane premium'
                });
            };

            // Étapes du workflow
            const steps = [
                { id: 'input', name: 'Saisie', icon: '📝', active: step === 'input' },
                { id: 'generating', name: 'Génération', icon: '🤖', active: step === 'generating' || step === 'preview' },
                { id: 'validating', name: 'Validation', icon: '🔍', active: step === 'validating' || step === 'validated' },
                { id: 'publishing', name: 'Publication', icon: '🚀', active: step === 'publishing' || step === 'published' }
            ];

            return (
                <div className="space-y-6">
                    {/* Progress bar */}
                    <div className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center justify-between">
                            {steps.map((stepItem, index) => (
                                <div key={stepItem.id} className="flex items-center">
                                    <div className={`
                                        flex items-center justify-center w-10 h-10 rounded-full border-2 
                                        ${stepItem.active 
                                            ? 'bg-blue-500 border-blue-500 text-white' 
                                            : 'bg-gray-100 border-gray-300 text-gray-500'
                                        }
                                    `}>
                                        <span className="text-sm">{stepItem.icon}</span>
                                    </div>
                                    <span className={`ml-2 text-sm font-medium ${stepItem.active ? 'text-blue-600' : 'text-gray-500'}`}>
                                        {stepItem.name}
                                    </span>
                                    {index < steps.length - 1 && (
                                        <div className="ml-4 w-8 h-0.5 bg-gray-300"></div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Étape 1: Formulaire de saisie */}
                    {step === 'input' && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    📝 Informations du produit
                                </h3>
                                <button
                                    onClick={fillSampleData}
                                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                >
                                    Remplir avec des données d'exemple
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nom du produit *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.product_name}
                                        onChange={(e) => handleInputChange('product_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ex: iPhone 15 Pro Max 256GB"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Marque *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.brand}
                                        onChange={(e) => handleInputChange('brand', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ex: Apple"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Catégorie
                                    </label>
                                    <select
                                        value={formData.category}
                                        onChange={(e) => handleInputChange('category', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="électronique">Électronique</option>
                                        <option value="mode">Mode</option>
                                        <option value="maison">Maison</option>
                                        <option value="sport">Sport</option>
                                        <option value="beauté">Beauté</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Prix (€)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.price}
                                        onChange={(e) => handleInputChange('price', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ex: 1479"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Caractéristiques principales
                                    </label>
                                    <textarea
                                        value={formData.features}
                                        onChange={(e) => handleInputChange('features', e.target.value)}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ex: Puce A17 Pro, Écran Super Retina XDR 6,7 pouces, Système caméra Pro triple..."
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Mots-clés cibles
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.target_keywords}
                                        onChange={(e) => handleInputChange('target_keywords', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ex: smartphone, premium, apple, iphone, pro"
                                    />
                                </div>
                            </div>

                            <div className="mt-6">
                                <button
                                    onClick={handleGenerate}
                                    disabled={!formData.product_name || !formData.brand}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                                >
                                    <span>🤖</span>
                                    Générer la fiche produit IA
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Étape 2: Génération en cours */}
                    {step === 'generating' && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                            <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                🤖 Génération en cours...
                            </h3>
                            <p className="text-gray-600">
                                L'IA génère votre fiche produit optimisée Amazon A9/A10
                            </p>
                        </div>
                    )}

                    {/* Étape 3: Prévisualisation */}
                    {step === 'preview' && generatedListing && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    📄 Fiche produit générée
                                </h3>
                                <div className="flex items-center gap-2">
                                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                                        Score: {generatedListing.generation_metadata.optimization_score}%
                                    </span>
                                    {generatedListing.generation_metadata.a9_a10_compliant && (
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                            ✅ A9/A10 Conforme
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Titre Amazon</h4>
                                    <div className="p-3 bg-gray-50 rounded-md">
                                        <p className="text-sm text-gray-900">{generatedListing.seo_content.title}</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {generatedListing.seo_content.title.length}/200 caractères
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Points clés (Bullets)</h4>
                                    <div className="space-y-2">
                                        {generatedListing.seo_content.bullet_points.map((bullet, index) => (
                                            <div key={index} className="p-3 bg-gray-50 rounded-md">
                                                <p className="text-sm text-gray-900">{bullet}</p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {bullet.length}/255 caractères
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                                    <div className="p-3 bg-gray-50 rounded-md">
                                        <p className="text-sm text-gray-900 whitespace-pre-line">{generatedListing.seo_content.description}</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {generatedListing.seo_content.description.length}/2000 caractères
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Mots-clés backend</h4>
                                    <div className="p-3 bg-gray-50 rounded-md">
                                        <p className="text-sm text-gray-900">{generatedListing.seo_content.backend_keywords}</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {new Blob([generatedListing.seo_content.backend_keywords]).size}/250 bytes
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 flex gap-4">
                                <button
                                    onClick={resetGenerator}
                                    className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                >
                                    Recommencer
                                </button>
                                <button
                                    onClick={handleValidate}
                                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                                >
                                    <span>🔍</span>
                                    Valider le listing
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Étape 4: Validation en cours */}
                    {step === 'validating' && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                            <div className="animate-spin h-12 w-12 border-4 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                🔍 Validation en cours...
                            </h3>
                            <p className="text-gray-600">
                                Validation selon les règles Amazon A9/A10
                            </p>
                        </div>
                    )}

                    {/* Étape 5: Résultats de validation */}
                    {step === 'validated' && validationResult && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    🔍 Validation Amazon A9/A10
                                </h3>
                                <div className="flex items-center gap-2">
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                        validationResult.overall_status === 'APPROVED' 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {validationResult.overall_status === 'APPROVED' ? '✅ APPROUVÉ' : '⚠️ ATTENTION'}
                                    </span>
                                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                        Score: {validationResult.validation_score}%
                                    </span>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                                {Object.entries(validationResult.details).map(([component, details]) => (
                                    <div key={component} className="p-3 bg-gray-50 rounded-md">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm font-medium text-gray-900 capitalize">{component}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded ${
                                                details.status === 'APPROVED' 
                                                    ? 'bg-green-100 text-green-800' 
                                                    : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {details.score}%
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-600">
                                            {details.status === 'APPROVED' ? '✅ Conforme' : '⚠️ À améliorer'}
                                        </p>
                                    </div>
                                ))}
                            </div>

                            <div className="p-4 bg-green-50 rounded-lg border border-green-200 mb-6">
                                <p className="text-sm text-green-800 font-medium">
                                    📋 {validationResult.summary}
                                </p>
                            </div>

                            <div className="flex gap-4">
                                <button
                                    onClick={() => setStep('preview')}
                                    className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                >
                                    Retour à la prévisualisation
                                </button>
                                <button
                                    onClick={handlePublish}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                                >
                                    <span>🚀</span>
                                    Publier sur Amazon
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Étape 6: Publication en cours */}
                    {step === 'publishing' && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                            <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                🚀 Publication en cours...
                            </h3>
                            <p className="text-gray-600">
                                Envoi vers Amazon via SP-API
                            </p>
                        </div>
                    )}

                    {/* Étape 7: Publication réussie */}
                    {step === 'published' && publicationResult && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <span className="text-2xl">✅</span>
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                    Publication réussie !
                                </h3>
                                <p className="text-gray-600">
                                    Votre produit a été publié sur Amazon avec succès
                                </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                <div className="p-4 bg-blue-50 rounded-lg">
                                    <h4 className="font-medium text-blue-900 mb-2">Informations de publication</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-blue-700">SKU:</span>
                                            <span className="font-mono text-blue-900">{publicationResult.sku}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-blue-700">ASIN:</span>
                                            <span className="font-mono text-blue-900">{publicationResult.asin}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-blue-700">Marketplace:</span>
                                            <span className="text-blue-900">{publicationResult.marketplace}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-blue-700">Status:</span>
                                            <span className="text-green-600 font-medium">{publicationResult.status}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <h4 className="font-medium text-gray-900 mb-2">Traitement SP-API</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-700">Feed ID:</span>
                                            <span className="font-mono text-gray-900">{publicationResult.feed_id}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-700">Temps:</span>
                                            <span className="text-gray-900">{publicationResult.sp_api_response.processing_time}s</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-700">Résultat:</span>
                                            <span className="text-green-600 font-medium">{publicationResult.sp_api_response.result}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-green-50 rounded-lg border border-green-200 mb-6">
                                <p className="text-sm text-green-800">
                                    🎉 <strong>Félicitations !</strong> Votre produit est maintenant disponible sur Amazon. 
                                    Il peut prendre quelques minutes à apparaître dans les résultats de recherche.
                                </p>
                            </div>

                            <button
                                onClick={resetGenerator}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                            >
                                Créer une nouvelle fiche produit
                            </button>
                        </div>
                    )}
                </div>
            );
        };

        // Composant de démonstration AmazonConnectionManager
        const DemoAmazonConnectionManager = () => {
            const [connectionStatus, setConnectionStatus] = useState('none');
            const [loading, setLoading] = useState(false);
            const [error, setError] = useState('');
            const [connections, setConnections] = useState([]);
            const [selectedMarketplace, setSelectedMarketplace] = useState('A13V1IB3VIYZZH');

            // Marketplaces supportés
            const marketplaces = [
                { id: 'A13V1IB3VIYZZH', name: 'France (Amazon.fr)', flag: '🇫🇷', region: 'eu' },
                { id: 'A1PA6795UKMFR9', name: 'Allemagne (Amazon.de)', flag: '🇩🇪', region: 'eu' },
                { id: 'ATVPDKIKX0DER', name: 'États-Unis (Amazon.com)', flag: '🇺🇸', region: 'na' },
                { id: 'A1F83G8C2ARO7P', name: 'Royaume-Uni (Amazon.co.uk)', flag: '🇬🇧', region: 'eu' },
                { id: 'APJ6JRA9NG5V4', name: 'Italie (Amazon.it)', flag: '🇮🇹', region: 'eu' },
                { id: 'A1RKKUPIHCS9HS', name: 'Espagne (Amazon.es)', flag: '🇪🇸', region: 'eu' }
            ];

            const handleConnect = async () => {
                setLoading(true);
                setError('');
                
                setTimeout(() => {
                    setConnectionStatus('connected');
                    setConnections([{
                        connection_id: 'demo_123',
                        marketplace_id: selectedMarketplace,
                        seller_id: 'DEMO_SELLER_123'
                    }]);
                    setLoading(false);
                }, 2000);
            };

            const handleDisconnect = async () => {
                if (!window.confirm('Êtes-vous sûr de vouloir déconnecter votre compte Amazon ? (DEMO)')) {
                    return;
                }
                
                setLoading(true);
                setTimeout(() => {
                    setConnectionStatus('revoked');
                    setConnections([]);
                    setLoading(false);
                }, 1000);
            };

            const getStatusDisplay = () => {
                switch (connectionStatus) {
                    case 'connected':
                        return {
                            color: 'text-green-600',
                            bgColor: 'bg-green-50',
                            icon: '✅',
                            text: 'Connecté',
                            description: `${connections.length} marketplace(s) connecté(s)`
                        };
                    case 'pending':
                        return {
                            color: 'text-yellow-600',
                            bgColor: 'bg-yellow-50',
                            icon: '⏳',
                            text: 'En cours',
                            description: 'Connexion en cours de traitement'
                        };
                    case 'error':
                        return {
                            color: 'text-red-600',
                            bgColor: 'bg-red-50',
                            icon: '❌',
                            text: 'Erreur',
                            description: 'Problème de connexion détecté'
                        };
                    case 'revoked':
                        return {
                            color: 'text-gray-600',
                            bgColor: 'bg-gray-50',
                            icon: '🔌',
                            text: 'Déconnecté',
                            description: 'Compte déconnecté'
                        };
                    default:
                        return {
                            color: 'text-gray-600',
                            bgColor: 'bg-gray-50',
                            icon: '➖',
                            text: 'Non connecté',
                            description: 'Aucune connexion Amazon'
                        };
                }
            };

            const statusDisplay = getStatusDisplay();

            return (
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <span className="text-2xl">🛒</span>
                                Connexion Amazon (DÉMO)
                            </h3>
                            <p className="text-sm text-gray-600 mt-1">
                                Connectez votre compte Amazon Seller Central
                            </p>
                        </div>
                        
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${statusDisplay.bgColor} ${statusDisplay.color} flex items-center gap-2`}>
                            <span>{statusDisplay.icon}</span>
                            {statusDisplay.text}
                        </div>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                            <p className="text-sm text-red-600">{error}</p>
                        </div>
                    )}

                    <div className="mb-6">
                        <div className={`p-4 rounded-lg ${statusDisplay.bgColor} border border-gray-200`}>
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{statusDisplay.icon}</span>
                                <div>
                                    <p className={`font-medium ${statusDisplay.color}`}>
                                        {statusDisplay.text}
                                    </p>
                                    <p className="text-sm text-gray-600">
                                        {statusDisplay.description}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {connections.length > 0 && (
                        <div className="mb-6">
                            <h4 className="font-medium text-gray-900 mb-3">Marketplaces connectés</h4>
                            <div className="space-y-2">
                                {connections.map((connection, index) => {
                                    const marketplace = marketplaces.find(m => m.id === connection.marketplace_id);
                                    return (
                                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                                            <div className="flex items-center gap-3">
                                                <span className="text-xl">{marketplace?.flag || '🌍'}</span>
                                                <div>
                                                    <p className="font-medium text-gray-900">
                                                        {marketplace?.name || connection.marketplace_id}
                                                    </p>
                                                    <p className="text-sm text-gray-600">
                                                        Vendeur: {connection.seller_id}
                                                    </p>
                                                </div>
                                            </div>
                                            <span className="text-green-600 text-sm">✅ Actif</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {connectionStatus !== 'connected' && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Marketplace à connecter
                                </label>
                                <select
                                    value={selectedMarketplace}
                                    onChange={(e) => setSelectedMarketplace(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={loading}
                                >
                                    {marketplaces.map((marketplace) => (
                                        <option key={marketplace.id} value={marketplace.id}>
                                            {marketplace.flag} {marketplace.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                onClick={handleConnect}
                                disabled={loading}
                                className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                        Connexion en cours...
                                    </>
                                ) : (
                                    <>
                                        <span>🔗</span>
                                        Connecter mon compte Amazon
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {connectionStatus === 'connected' && (
                        <button
                            onClick={handleDisconnect}
                            disabled={loading}
                            className="w-full bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                    Déconnexion...
                                </>
                            ) : (
                                <>
                                    <span>🔌</span>
                                    Déconnecter Amazon
                                </>
                            )}
                        </button>
                    )}

                    <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <h4 className="font-medium text-blue-900 mb-2">🔐 Sécurité & Permissions</h4>
                        <ul className="text-sm text-blue-800 space-y-1">
                            <li>• Connexion sécurisée via OAuth 2.0</li>
                            <li>• Tokens chiffrés et stockés de manière sécurisée</li>
                            <li>• Accès en lecture seule à vos listings</li>
                            <li>• Aucune modification sans votre autorisation</li>
                        </ul>
                    </div>
                </div>
            );
        };

        // Page de démonstration complète
        const DemoAmazonIntegrationPage = () => {
            const [activeTab, setActiveTab] = useState('connexions');

            const tabs = [
                {
                    id: 'connexions',
                    name: 'Connexions',
                    icon: '🔗',
                    description: 'Gérer vos connexions Amazon',
                    active: true
                },
                {
                    id: 'seo',
                    name: 'SEO',
                    icon: '📈',
                    description: 'Optimisation SEO Amazon A9/A10',
                    active: false,
                    comingSoon: true
                },
                {
                    id: 'prix',
                    name: 'Prix',
                    icon: '💰',
                    description: 'Gestion des prix et surveillance',
                    active: false,
                    comingSoon: true
                },
                {
                    id: 'generateur',
                    name: 'Générateur de fiche',
                    icon: '📝',
                    description: 'Génération automatique de fiches produits',
                    active: false,
                    comingSoon: false
                },
                {
                    id: 'monitoring',
                    name: 'Monitoring',
                    icon: '📊',
                    description: 'Surveillance des performances',
                    active: false,
                    comingSoon: true
                },
                {
                    id: 'optimisations',
                    name: 'Optimisations',
                    icon: '⚡',
                    description: 'Améliorations automatiques',
                    active: false,
                    comingSoon: true
                }
            ];

            return (
                <div className="min-h-screen bg-gray-50">
                    <div className="bg-white border-b border-gray-200">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div className="flex items-center justify-between h-16">
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => alert('DÉMO: Navigation vers dashboard simulée')}
                                        className="text-gray-500 hover:text-gray-700 transition-colors"
                                    >
                                        ← Retour au dashboard
                                    </button>
                                    <div className="h-6 w-px bg-gray-300"></div>
                                    <div>
                                        <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                                            <span className="text-2xl">🛒</span>
                                            Amazon SP-API (DÉMO Phase 1)
                                        </h1>
                                        <p className="text-sm text-gray-600">
                                            Intégration complète avec Amazon Seller Central
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                            <div className="lg:col-span-1">
                                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                                    <div className="p-4 border-b border-gray-200">
                                        <h2 className="font-semibold text-gray-900">Fonctionnalités</h2>
                                        <p className="text-sm text-gray-600 mt-1">
                                            Phase 1 - Fondations
                                        </p>
                                    </div>
                                    
                                    <nav className="space-y-1 p-2">
                                        {tabs.map((tab) => (
                                            <button
                                                key={tab.id}
                                                onClick={() => !tab.comingSoon && setActiveTab(tab.id)}
                                                disabled={tab.comingSoon}
                                                className={`
                                                    w-full text-left px-3 py-3 rounded-md transition-colors relative
                                                    ${activeTab === tab.id 
                                                        ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                                                        : tab.comingSoon
                                                        ? 'text-gray-400 cursor-not-allowed'
                                                        : 'text-gray-700 hover:bg-gray-50'
                                                    }
                                                `}
                                            >
                                                <div className="flex items-center gap-3">
                                                    <span className="text-lg">{tab.icon}</span>
                                                    <div className="flex-1">
                                                        <div className="font-medium">{tab.name}</div>
                                                        <div className="text-xs text-gray-500 mt-0.5">
                                                            {tab.description}
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                {tab.comingSoon && (
                                                    <div className="absolute top-2 right-2">
                                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                                            Bientôt
                                                        </span>
                                                    </div>
                                                )}
                                            </button>
                                        ))}
                                    </nav>

                                    <div className="p-4 border-t border-gray-200 bg-gray-50">
                                        <div className="text-xs text-gray-600">
                                            <div className="font-medium mb-2">🚀 Phase 1 - Fondations</div>
                                            <ul className="space-y-1">
                                                <li>✅ Connexion SP-API OAuth 2.0</li>
                                                <li>✅ Multi-tenant sécurisé</li>
                                                <li>✅ Chiffrement des tokens</li>
                                                <li>🔄 UI dédiée Amazon</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>

                                {activeTab === 'generateur' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                                Générateur de fiche produit Amazon IA
                                            </h2>
                                            <p className="text-gray-600">
                                                Créez des fiches produits optimisées Amazon avec l'intelligence artificielle. 
                                                Génération automatique conforme aux règles A9/A10.
                                            </p>
                                        </div>

                                        <DemoAmazonListingGenerator />

                                        <div className="bg-purple-50 rounded-lg border border-purple-200 p-6">
                                            <h3 className="font-semibold text-purple-900 mb-4 flex items-center gap-2">
                                                <span>🤖</span>
                                                Fonctionnalités IA Phase 2
                                            </h3>
                                            
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-purple-800">
                                                <div>
                                                    <h4 className="font-medium mb-2">✨ Génération automatique</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Titre optimisé Amazon (max 200 chars)</li>
                                                        <li>• 5 bullet points SEO (max 255 chars)</li>
                                                        <li>• Description structurée (100-2000 chars)</li>
                                                        <li>• Mots-clés backend (max 250 bytes)</li>
                                                    </ul>
                                                </div>
                                                
                                                <div>
                                                    <h4 className="font-medium mb-2">🔍 Validation A9/A10</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Conformité règles Amazon</li>
                                                        <li>• Score de qualité détaillé</li>
                                                        <li>• Validation par composant</li>
                                                        <li>• Suggestions d'amélioration</li>
                                                    </ul>
                                                </div>

                                                <div>
                                                    <h4 className="font-medium mb-2">🚀 Publication SP-API</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Publication directe Amazon</li>
                                                        <li>• Génération SKU automatique</li>
                                                        <li>• Suivi Feed Amazon</li>
                                                        <li>• Gestion des erreurs</li>
                                                    </ul>
                                                </div>

                                                <div>
                                                    <h4 className="font-medium mb-2">⚡ Workflow optimisé</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Interface intuitive 4 étapes</li>
                                                        <li>• Prévisualisation en temps réel</li>
                                                        <li>• Validation avant publication</li>
                                                        <li>• Intégration Phase 1 (OAuth)</li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-green-50 rounded-lg border border-green-200 p-6">
                                            <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                                                <span>🎉</span>
                                                Démo Phase 2 Amazon SP-API
                                            </h3>
                                            <p className="text-green-800 text-sm">
                                                Cette interface de démonstration simule le comportement complet du générateur IA Phase 2. 
                                                Workflow: saisie produit → génération IA → prévisualisation → validation A9/A10 → publication SP-API.
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {activeTab === 'connexions' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                                Connexions Amazon
                                            </h2>
                                            <p className="text-gray-600">
                                                Configurez vos connexions Amazon Seller Central pour accéder à vos données de vente et gérer vos listings.
                                            </p>
                                        </div>

                                        <DemoAmazonConnectionManager />

                                        <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
                                            <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
                                                <span>📚</span>
                                                Guide de configuration
                                            </h3>
                                            
                                            <div className="space-y-4 text-blue-800">
                                                <div>
                                                    <h4 className="font-medium mb-2">1. Prérequis</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Compte Amazon Seller Central actif</li>
                                                        <li>• Statut de vendeur professionnel</li>
                                                        <li>• Autorisations SP-API activées</li>
                                                    </ul>
                                                </div>
                                                
                                                <div>
                                                    <h4 className="font-medium mb-2">2. Processus de connexion</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Sélectionnez votre marketplace principal</li>
                                                        <li>• Cliquez sur "Connecter mon compte Amazon"</li>
                                                        <li>• Autorisez l'accès dans Amazon Seller Central</li>
                                                        <li>• Retour automatique avec confirmation</li>
                                                    </ul>
                                                </div>

                                                <div>
                                                    <h4 className="font-medium mb-2">3. Sécurité</h4>
                                                    <ul className="text-sm space-y-1 ml-4">
                                                        <li>• Tokens chiffrés avec AES-GCM</li>
                                                        <li>• Protection CSRF avec state OAuth</li>
                                                        <li>• Isolation multi-tenant</li>
                                                        <li>• Révocation possible à tout moment</li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-green-50 rounded-lg border border-green-200 p-6">
                                            <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                                                <span>🎉</span>
                                                Démo Phase 1 Amazon SP-API
                                            </h3>
                                            <p className="text-green-800 text-sm">
                                                Cette interface de démonstration simule le comportement de l'intégration Amazon SP-API Phase 1. 
                                                Tous les éléments sont fonctionnels et respectent les spécifications de la Phase 1.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            );
        };

        // Rendu de l'application
        ReactDOM.render(<DemoAmazonIntegrationPage />, document.getElementById('demo-amazon-root'));
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)