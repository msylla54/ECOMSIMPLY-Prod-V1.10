import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { createPortal } from 'react-dom';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import './App.css';
import { NavLogo, HeaderLogo, DashboardLogo } from './components/ui/Logo';
import axios from 'axios';

// ✅ Import du client API centralisé
import apiClient from './lib/apiClient';

// ✅ NOUVEAU: Import des composants Stripe
import SubscriptionManager from './components/SubscriptionManager';
import SubscriptionGuard from './components/SubscriptionGuard';

// ✅ NOUVEAU: Import du composant Amazon SP-API
import AmazonIntegration from './components/AmazonIntegration';
import AmazonIntegrationCard from './components/AmazonIntegrationCard';

// ✅ PHASE 1: Import de la nouvelle page Amazon
import AmazonIntegrationPage from './pages/AmazonIntegrationPage';

// ✅ SHOPIFY PHASE 1: Import de la nouvelle page Shopify
import ShopifyIntegrationPage from './pages/ShopifyIntegrationPage';

// ✅ NOUVEAU: Import du composant de gestion des images
import ImageManagementSettings from './components/ImageManagementSettings';

// ✅ NOUVEAU: Import du composant de gestion des marchés multi-pays
import MarketSettingsManager from './components/MarketSettingsManager';

// ✅ NOUVEAU: Import du composant SEO Amazon A9/A10
import AmazonSEOOptimizer from './components/AmazonSEOOptimizer';

// ✅ Import des composants premium
import HeroSection from './components/HeroSection';
import BentoFeatures from './components/BentoFeatures';
import PremiumPricing from './components/PremiumPricing';
import DashboardShell from './components/DashboardShell';
import KPIGrid from './components/KPIGrid';
import PremiumTable, { TableActions } from './components/PremiumTable';

// ✅ NOUVEAU: Import du système PriceTruth
import { PriceTruthDisplay, PriceTruthBadge } from './components/PriceTruth';

import { 
  FadeInWhenVisible, 
  ParallaxContainer, 
  StaggerContainer, 
  StaggerItem, 
  HoverCard, 
  PricingCard, 
  AnimatedButton, 
  CounterAnimation,
  StickyHeader
} from './components/MotionComponents';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8001');
// ✅ CORRECTION AUTH: Éviter la duplication /api - BACKEND_URL doit pointer vers la racine du backend
const API = BACKEND_URL.endsWith('/api') ? BACKEND_URL : `${BACKEND_URL}/api`;

// Configuration des catégories de produits pour améliorer le ciblage SEO
const PRODUCT_CATEGORIES = {
  fr: [
    { value: 'electronique', label: '📱 Électronique' },
    { value: 'mode', label: '👕 Mode & Vêtements' },
    { value: 'maison', label: '🏠 Maison & Jardin' },
    { value: 'beaute', label: '💄 Beauté & Cosmétiques' },
    { value: 'sport', label: '⚽ Sport & Fitness' },
    { value: 'auto', label: '🚗 Automobile' },
    { value: 'bebe', label: '👶 Bébé & Enfants' },
    { value: 'alimentation', label: '🍎 Alimentation & Boissons' },
    { value: 'livre', label: '📚 Livres & Médias' },
    { value: 'jouet', label: '🧸 Jouets & Jeux' },
    { value: 'bricolage', label: '🔨 Bricolage & Outils' },
    { value: 'animalerie', label: '🐕 Animalerie' },
    { value: 'sante', label: '💊 Santé & Bien-être' },
    { value: 'bureau', label: '🖥️ Bureau & Informatique' },
    { value: 'musique', label: '🎵 Musique & Instruments' },
    { value: 'custom', label: '✏️ Catégorie personnalisée' }
  ],
  en: [
    { value: 'electronics', label: '📱 Electronics' },
    { value: 'fashion', label: '👕 Fashion & Clothing' },
    { value: 'home', label: '🏠 Home & Garden' },
    { value: 'beauty', label: '💄 Beauty & Cosmetics' },
    { value: 'sports', label: '⚽ Sports & Fitness' },
    { value: 'automotive', label: '🚗 Automotive' },
    { value: 'baby', label: '👶 Baby & Kids' },
    { value: 'food', label: '🍎 Food & Beverages' },
    { value: 'books', label: '📚 Books & Media' },
    { value: 'toys', label: '🧸 Toys & Games' },
    { value: 'tools', label: '🔨 Tools & Hardware' },
    { value: 'pets', label: '🐕 Pet Supplies' },
    { value: 'health', label: '💊 Health & Wellness' },
    { value: 'office', label: '🖥️ Office & Computing' },
    { value: 'music', label: '🎵 Music & Instruments' },
    { value: 'custom', label: '✏️ Custom Category' }
  ]
};

// Configuration centrale pour tous les chiffres dynamiques
const PLATFORM_CONFIG = {
  // Plans et limites
  FREE_SHEETS_LIMIT: 1,
  PRO_SHEETS_LIMIT: 100,
  PREMIUM_SHEETS_UNLIMITED: "illimitées",
  
  // Prix des plans (en euros)
  PRO_PRICE: 29,
  PREMIUM_PRICE: 99,
  
  // Commissions d'affiliation
  PRO_COMMISSION_RATE: 10,
  PREMIUM_COMMISSION_RATE: 15,
  
  // Plateformes e-commerce
  ECOMMERCE_PLATFORMS_COUNT: 7,
  
  // Analytics et délais
  ANALYTICS_DAYS: 30,
  TRENDS_DAYS: 7,
  GUARANTEE_DAYS: 15,
  FREE_TRIAL_DAYS: 7,
  
  // Performance et stats  
  CUSTOMER_SATISFACTION_RATE: 98,
  TOTAL_SHEETS_GENERATED: 10000,
  TRUSTED_CUSTOMERS: 1000,
  GENERATION_TIME_SECONDS: 28,
  
  // Technique
  PASSWORD_MIN_LENGTH: 8,
  AUTO_UPDATE_SECONDS: 30,
  SUPPORT_HOURS: "24/7",
  COOKIE_DURATION_DAYS: 30,
  
  // GPT Model
  GPT_MODEL: "GPT-4o",
  
  // Discounts et offres
  ANNUAL_DISCOUNT_PERCENT: 30,
  FIRST_SIGNUPS_COUNT: 50
};

// Multilingual Support - Complete Translations (FRANÇAIS ET ANGLAIS UNIQUEMENT)
const TRANSLATIONS = {
  fr: {
    // Navigation & Header
    connection: "Connexion",
    register: "S'inscrire", 
    logout: "Déconnexion",
    
    // Landing Page
    heroTitle: "Générez des Fiches Produits Parfaites avec l'IA",
    heroSubtitle: "Transformez vos descriptions de produits en fiches e-commerce professionnelles et optimisées SEO en quelques secondes. Alimenté par une technologie IA avancée.",
    tryFree: "Essai Gratuit",
    
    // Features
    featuresTitle: "Fonctionnalités Puissantes",
    aiGeneration: "Génération IA",
    aiGenerationDesc: "IA avancée pour créer des fiches produits optimisées",
    analyticsDashboard: "Tableau de Bord Analytique", 
    analyticsDashboardDesc: "Suivez vos performances et optimisez vos résultats",
    easyExport: "Export Facile",
    easyExportDesc: "Exportez vos fiches dans plusieurs formats populaires",
    
    // New Features 2024
    bulkPublication: "Publication en Lot",
    bulkPublicationDesc: "Publiez plusieurs fiches simultanément sur vos boutiques",
    multiPlatform: "Multi-Plateformes",
    multiPlatformDesc: "Connectez Shopify, WooCommerce, Amazon, eBay, Etsy, Facebook et Google Shopping",
    advancedAI: "IA Premium",
    advancedAIDesc: "SEO intelligent, analyse concurrentielle, optimisation prix et traduction multilingue",
    smartSelection: "Sélection Intelligente",
    smartSelectionDesc: "Sélection optimisée par IA pour des résultats personnalisés",
    readyToBoost: "Prêt à booster votre e-commerce ?",
    
    // Pricing
    pricingTitle: "Tarifs Transparents",
    planFree: "Gratuit",
    planPro: "Pro",
    planPremium: "Premium",
    planFreePriceDesc: `${PLATFORM_CONFIG.FREE_SHEETS_LIMIT} fiche par mois`,
    planProPriceDesc: `${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois`,
    planPremiumPriceDesc: `Fiches ${PLATFORM_CONFIG.PREMIUM_SHEETS_UNLIMITED}`,
    mostChosen: "Le Plus Choisi",
    chooseThisPlan: "Choisir ce Plan",
    
    // Dashboard Tabs
    aiGenerator: "Générateur IA",
    dashboard: "Tableau de Bord",
    subscription: "Abonnement",
    history: "Historique",
    accountManagement: "Gestion de Compte", 
    admin: "Admin",
    
    // NEW PREMIUM TABS
    aiFeatures: "IA Avancée",
    ecommerceIntegrations: "Intégrations",
    premiumAnalytics: "Analytics Pro",
    
    // AI Features
    seoAnalysis: "Analyse SEO",
    competitorAnalysis: "Analyse Concurrentielle",
    priceOptimization: "Optimisation Prix",
    multilingualTranslation: "Traduction Multi-Langue",
    productVariants: "Variantes Produits",
    
    // E-commerce Integrations
    connectStore: "Connecter une Boutique",
    manageStores: "Gérer les Boutiques",
    publishProduct: "Publier Produit",
    integrationLogs: "Logs d'Intégration",
    
    // Premium Analytics
    productPerformance: "Performance Produits",
    integrationPerformance: "Performance Intégrations",
    userEngagement: "Engagement Utilisateur",
    businessIntelligence: "Business Intelligence",
    
    // Premium Features Messages
    premiumRequired: "Fonctionnalité Premium",
    premiumRequiredDesc: "Cette fonctionnalité nécessite un abonnement Pro ou Premium",
    tryFree: "Essayer gratuitement",
    upgradeToProPrice: `Passer à Pro - ${PLATFORM_CONFIG.PRO_PRICE}€/mois`,
    bulkSelectHelp: "Cochez les fiches pour publier ou exporter par lot, ou utilisez \"Publier tout\" pour tout publier",
    productToPublish: "Produit à publier:",
    
    // Publish to Store
    publishToStore: "Publier sur boutique",
    selectStore: "Sélectionnez une boutique",
    publishProduct: "Publier le produit",
    noStoresConnected: "Aucune boutique connectée",
    connectStoresFirst: "Connectez d'abord vos boutiques dans l'onglet Intégrations",
    publishingToStore: "Publication en cours sur",
    publishedSuccessfully: "Produit publié avec succès sur",
    publishError: "Erreur lors de la publication",
    
    // Bulk Publishing
    bulkPublish: "Publier sélection",
    selectSheets: "Sélectionner des fiches",
    selectedSheetsCount: "fiches sélectionnées",
    selectAll: "Tout sélectionner",
    deselectAll: "Tout désélectionner",
    publishSelectedSheets: "Publier les fiches sélectionnées",
    bulkPublishSuccess: "Publication en lot réussie",
    bulkPublishPartial: "Publication en lot partiellement réussie",
    bulkPublishFailed: "Échec de la publication en lot",
    
    // New Pricing Features
    ecommercePlateforms: `Connexion ${PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes e-commerce`,
    bulkPublishFeature: "Publication en lot",
    advancedAiFeatures: "IA Premium (SEO, analyse, prix)",
    smartSelectionFeature: "Sélection multiple intelligente",
    realTimeAnalytics: "Analytics temps réel",
    multilingualTranslation: "Traduction multilingue",
    competitiveAnalysis: "Analyse concurrentielle",
    priceOptimization: "Optimisation des prix",
    
    // Enhanced Plan Features
    basicPlanFeatures: "Fonctionnalités de base",
    proPlanFeatures: "Fonctionnalités Pro + Intégrations",
    premiumPlanFeatures: "Toutes fonctionnalités + Support dédié",
    
    noPayments: "Aucun paiement",
    noPaymentsText: "Aucun paiement enregistré",
    noUsers: "Aucun utilisateur",
    noActivity: "Aucune activité",
    noContacts: "Aucun contact",
    loading: "Chargement...",
    action: "Action",
    message: "Message",
    date: "Date",
    status: "Statut",
    responded: "Répondu",
    pending: "En attente",
    aiGenerateImages: "L'IA générera des images professionnelles avec différents angles de vue",
    professionalProductImages: "Images professionnelles du produit",
    optimizedImagesForEcommerce: "image(s) optimisée(s) pour l'e-commerce",
    optimizedTitle: "Titre Optimisé",
    marketingDescription: "Description Marketing",
    seoTags: "Tags SEO",
    priceSuggestions: "Suggestions de Prix",
    targetAudience: "Audience Cible",
    callToAction: "Appel à l'Action",
    
    // Forms & Inputs
    email: "Email",
    password: "Mot de passe",
    confirmPassword: "Confirmer le mot de passe",
    currentPassword: "Mot de passe actuel",
    newPassword: "Nouveau mot de passe",
    name: "Nom",
    productName: "Nom du produit",
    productDescription: "Description du produit",
    productCategory: "Catégorie du produit",
    productUseCase: "Scénario d'usage",
    useCaseHelpsContext: "Décrivez le contexte d'utilisation pour personnaliser le contenu",
    enterUseCase: "Ex: Cadeau d'anniversaire, usage professionnel, sport en extérieur...",
    imageStyle: "Style d'image",
    imageStyleHelps: "Choisissez le style de présentation pour vos images",
    imageStyleStudio: "Studio - Fond blanc professionnel",
    imageStyleLifestyle: "Lifestyle - Mise en situation réelle", 
    imageStyleDetailed: "Détaillé - Plan serré haute définition",
    imageStyleTechnical: "Technique - Documentation précise",
    imageStyleEmotional: "Émotionnel - Impact visuel fort",
    customCategory: "Catégorie personnalisée",
    selectCategory: "Sélectionnez une catégorie",
    categoryHelpsTargetSeo: "La sélection d'une catégorie aide à cibler le SEO et optimiser les tags",
    enterCustomCategory: "Entrez votre catégorie personnalisée...",
    numberOfImages: "Nombre d'images à générer",
    generateSheet: "Générer la Fiche",
    
    // Buttons & Actions
    login: "Se connecter",
    signup: "S'inscrire",
    save: "Enregistrer",
    cancel: "Annuler",
    delete: "Supprimer",
    edit: "Modifier",
    export: "Exporter",
    upgrade: "Mettre à niveau",
    downgrade: "Rétrograder",
    submit: "Soumettre",
    publish: "PUBLIER",
    exportAll: "EXPORT TOUT",
    close: "Fermer",
    confirm: "Confirmer",
    preview: "Aperçu",
    
    // Messages & Status
    welcome: "Bienvenue",
    loading: "Chargement...",
    error: "Erreur",
    success: "Succès",
    warning: "Attention",
    info: "Information",
    processing: "Traitement en cours...",
    completed: "Terminé",
    failed: "Échec",
    
    // Language Selection
    selectLanguage: "Choisir la langue",
    currentLanguage: "Langue actuelle",
    languageChanged: "Langue modifiée avec succès",
    
    // Dashboard Content
    welcomeMessage: "Bienvenue sur votre tableau de bord ECOMSIMPLY",
    generateFirstSheet: "Générez votre fiche produit",
    totalSheets: "Fiches totales",
    thisMonth: "Ce mois",
    upgradeToUnlock: "Mettre à niveau pour débloquer plus de fonctionnalités",
    monthlyUsage: "Utilisation mensuelle",
    accountAge: "Ancienneté du compte", 
    upgradeDescription: "Débloquez plus de fiches, l'IA avancée et des fonctionnalités premium",
    seeFullPlansOnHomepage: "Voir tous les plans sur la page d'accueil",
    
    // Product Sheet
    generatedTitle: "Titre généré",
    marketingDescription: "Description marketing",
    keyFeatures: "Caractéristiques clés",
    seoTags: "Tags SEO",
    priceSuggestions: "Suggestions de prix",
    targetAudience: "Audience cible",
    callToAction: "Appel à l'action",
    
    describeProduct: "Décrivez votre produit",
    
    // Progress Messages
    analysisDone: "Analyse du produit terminée",
    creatingFeatures: "Création des caractéristiques clés...",
    generatingImage: "Génération de l'image optimisée",
    sheetGenerated: "Fiche produit générée",
    seoOptimized: "Optimisé SEO – prêt pour Shopify",
    
    // Progress Messages (continued)
    productAnalysis: "Analyse du produit...",
    aiContentGeneration: "Génération du contenu IA...",
    characteristicsCreation: "Création des caractéristiques...",
    imageGeneration: "Génération des images...",
    finalization: "Finalisation...",
    noSheetsGenerated: "Aucune fiche produit générée pour le moment.",
    exportThisSheet: "Exporter cette fiche",
    exportSheets: "Exporter les fiches",
    chooseExportFormat: "Choisissez le format d'export pour cette fiche produit :",
    chooseExportFormatMultiple: "Choisissez le format d'export pour vos fiches produits :",
    includeImages: "Inclure les images dans l'export",
    onlyProductInfo: "Seulement les informations produit",
    exportInProgress: "Export en cours...",
    exportAll: "Exporter tout",
    exportSelected: "Exporter sélectionné",
    newFeature: "Nouveauté",
    imagesIncluded: "Les images générées sont maintenant incluses dans tous les exports !",
    individualExport: "Export d'une fiche individuelle seulement",
    productImages: "Images du Produit",
    lastUpdate: "Dernière mise à jour",
    whyUpgradeToPremium: "Pourquoi passer à un plan premium ?",
    whyUpgradeToHigher: "Pourquoi améliorer votre plan ?",
    whyDowngradeWarning: "Attention au changement de plan",
    changeSubscriptionPlan: "Changer de plan d'abonnement",
    upgradeToPro: "Passer au Pro",
    upgradeToPremium: "Passer au Premium", 
    downgradeTo: "Rétrograder vers",
    currentPlanBenefits: "Avantages de votre plan actuel",
    planChangeOptions: "Options de changement de plan",
    moreSheets: "Plus de fiches",
    advancedAi: "IA avancée",
    analytics: "Analytics",
    generateUpTo100Sheets: `Générez jusqu'à ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois avec le plan Pro`,
    accessGpt4oModel: `Accès au modèle ${PLATFORM_CONFIG.GPT_MODEL} pour un contenu plus précis`,
    detailedDashboardInsights: "Tableaux de bord détaillés et insights avancés",
    subscriptionManagement: "Gestion de l'Abonnement",
    
    // Product Description
    optimizedDescription: "Description optimisée",
    keyCharacteristics: "Caractéristiques clés",
    
    // Missing French texts I spotted
    ourAiThinking: "Notre IA réfléchit à la meilleure fiche pour vous...",
    generateAnother: "Générer une autre fiche",
    everything: "Tout ce dont vous avez besoin pour créer des fiches produits parfaites",
    aiPoweredGeneration: "Génération Alimentée par l'IA",
    aiPoweredDesc: "L'IA avancée crée instantanément des descriptions de produits professionnelles, des caractéristiques et du contenu marketing.",
    analyticsBoard: "Tableau de Bord Analytique",
    analyticsBoardDesc: "Suivez vos fiches générées, surveillez les performances et analysez votre catalogue de produits.",
    easyExportTitle: "Export Facile",
    easyExportLongDesc: "Exportez vos fiches produits en CSV, PDF, ou intégrez directement avec votre plateforme e-commerce.",
    viewShopify: "Publier sur plateforme",
    instantGeneration: "IA Premium Avancée",
    instantDesc: `SEO automatique, analyse concurrentielle et optimisation des prix avec ${PLATFORM_CONFIG.GPT_MODEL} pour maximiser vos ventes.`,
    professionalQuality: "Publication Multi-Plateformes",
    professionalDesc: `Connectez ${PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes e-commerce (Shopify, Amazon, eBay, WooCommerce...) et publiez en lot instantanément.`,
    multipleExport: "Suivi Dynamique Temps Réel",
    multipleExportDesc: `Statistiques d'utilisation, ancienneté du compte et données mises à jour automatiquement toutes les ${PLATFORM_CONFIG.AUTO_UPDATE_SECONDS} secondes.`,
    guaranteedResults: "Résultats Garantis",
    guaranteedDesc: `Plus de ${PLATFORM_CONFIG.TOTAL_SHEETS_GENERATED.toLocaleString()} fiches produits générées avec un taux de satisfaction client de ${PLATFORM_CONFIG.CUSTOMER_SATISFACTION_RATE}%.`,
    avgGenerationTime: "Temps moyen de génération",
    seconds28: `${PLATFORM_CONFIG.GENERATION_TIME_SECONDS} secondes`,
    pricing: "Tarifs",
    plansAdapted: "Des plans adaptés à vos besoins",
    freeDesc: "Pour tester sans engagement",
    proDesc: "Idéal pour boutique en croissance", 
    premiumDesc: "Performance maximale pour gros volumes",
    startFree: "Commencer Gratuitement",
    choosePro: "Choisir Pro",
    choosePremium: "Choisir Premium",
    testimonials: "Témoignages",
    whatClientsSay: "Ce que disent nos clients",
    discoverWhy: `Découvrez pourquoi plus de ${PLATFORM_CONFIG.TRUSTED_CUSTOMERS.toLocaleString()} e-commerçants font confiance à ECOMSIMPLY`,
    satisfiedClients: "Clients satisfaits",
    averageRating: "Note moyenne",
    satisfactionRate: "Taux de satisfaction",
    shareExperience: "Partagez votre expérience",
    helpOthers: "Vous utilisez ECOMSIMPLY ? Aidez d'autres entrepreneurs en partageant votre avis",
    leaveTestimonial: "Laisser un témoignage",
    imageGeneratedByAi: "Image générée par IA",
    
    // Additional translations for remaining hardcoded texts
    loginConnection: "🔐 Connexion",
    enjoyPremiumFeatures: "Vous pouvez maintenant profiter de toutes les fonctionnalités premium !",
    cancelSubscriptionWarning: "Si vous souhaitez annuler votre abonnement, vous reviendrez au plan gratuit et perdrez l'accès aux fonctionnalités premium.",
    cancelSubscriptionInfo: `En annulant votre abonnement, vous reviendrez au plan gratuit (${PLATFORM_CONFIG.FREE_SHEETS_LIMIT} fiche/mois). Vous perdrez l'accès aux fonctionnalités premium.`,
    subscriptionCancelledSuccess: "Abonnement annulé avec succès. Vous êtes maintenant sur le plan gratuit.",
    freePlan: "Plan Gratuit",
    chatbotTechnicalError: "Désolé, je rencontre un problème technique. Puis-je vous aider autrement ? Vous pouvez me demander des infos sur les tarifs, l'utilisation, ou les fonctionnalités !",
    connectionFailed: "Connexion échouée",
    chatbotWelcome: "Bonjour ! Je suis votre assistant ECOMSIMPLY. Comment puis-je vous aider aujourd'hui ?",
    createAccountFirst: "Pour continuer, veuillez d'abord créer un compte gratuit. Vous pourrez ensuite mettre à niveau vers ce plan depuis votre tableau de bord.",
    subscriptionFreeDesc: `Vous bénéficiez actuellement de ${PLATFORM_CONFIG.FREE_SHEETS_LIMIT} fiche produit par mois avec notre générateur IA basique.`,
    subscriptionProDesc: `Vous bénéficiez de ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches produits par mois avec notre générateur IA avancé.`,
    subscriptionPremiumDesc: "Vous bénéficiez de fiches produits illimitées avec notre générateur IA premium.",
    usedThisMonth: "Utilisées ce mois",
    currentPlan: "Plan Actuel",
    premium: "Premium",
    basicAiGeneration: "Génération IA basique",
    registering: "Inscription...",
    choosePro: "Choisir Pro",
    averageRating: "Note moyenne",
    satisfactionRate: "Taux de satisfaction",
    discover: "Découvrez",
    downloadCsv: "Télécharger en CSV",
    viewOnShopify: "Publier sur plateforme",
    edit: "Modifier",
    
    generatedDescriptionTitle: "Description générée",
    keyCharacteristicsTitle: "Caractéristiques principales",
    aiGeneratedImage: "Image générée par IA",
    
    // Dashboard translations
    totalSheets: "Total des Fiches",
    thisMonth: "Ce Mois",
    thisWeek: "Cette Semaine",
    categoryBreakdown: "Répartition par Catégories",
    generationType: "Type de Génération",
    artificialIntelligence: "Intelligence Artificielle",
    simulatedGeneration: "Génération Simulée",
    averageCharacteristics: "Moyenne de caractéristiques/fiche",
    popularKeywords: "Mots-clés Populaires",
    generationTrends: `Tendances de Génération (${PLATFORM_CONFIG.TRENDS_DAYS} derniers jours)`,
    mostProductiveDay: "Jour le plus productif",
    
    // Subscription management
    subscriptionManagement: "Gestion de l'Abonnement",
    priceSuggestions: "Suggestions de Prix",
    targetAudience: "Audience Cible",
    callToAction: "Appel à l'Action",
    emailSupport: "Support par email",
    
    // Admin Panel
    adminPanelTitle: "Administration ECOMSIMPLY",
    adminPanelSubtitle: "Panneau de contrôle administrateur - Accès complet à la plateforme",
    stats: "Statistiques",
    users: "Utilisateurs",
    activity: "Activité",
    messages: "Messages",
    globalStats: "Statistiques Globales",
    totalUsers: "Total Utilisateurs",
    administrators: "Administrateurs",
    regularUsers: "Utilisateurs Réguliers",
    subscriptions: "Abonnements",
    totalRevenue: "Revenus Total",
    monthlyRevenue: "Revenus ce Mois",
    activityLast30Days: `Activité (${PLATFORM_CONFIG.ANALYTICS_DAYS} derniers jours)`,
    deletedAccounts: "Comptes Supprimés",
    upgrades: "Mises à Niveau",
    cancellations: "Annulations",
    userList: "Liste des Utilisateurs",
    subscriptionPlan: "Plan d'abonnement",
    registeredOn: "Inscrit le",
    lastConnection: "Dernière connexion",
    activityLogs: "Journaux d'Activité",
    contactMessages: "Messages de Contact",
    replyTo: "Répondre à",
    reply: "Répondre",
    replyResponseSent: "Réponse envoyée avec succès !",
    noContacts: "Aucun message de contact.",
    createNewAdmin: "Créer un Nouvel Administrateur",
    adminCreated: "Administrateur créé avec succès",
    createAdmin: "Créer Admin",
    revenue: "Revenus",
    userManagement: "Gestion des Utilisateurs",
    user: "Utilisateur",
    plan: "Plan",
    sheets: "Fiches",
    payments: "Paiements",
    registration: "Inscription",
    role: "Rôle",
    admin: "Admin",
    recommended: "Recommandé",
    idealForGrowingStore: "Idéal pour boutique en croissance",
    maxPerformanceHighVolume: "Performance maximale pour gros volumes",
    whyUpgradePremium: "Pourquoi passer à un plan premium ?",
    moreSheets: "Plus de fiches",
    advancedAi: "IA avancée",
    analytics: "Analytics",
    generateUpTo100: `Générez jusqu'à ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois avec le plan Pro`,
    accessGpt4o: `Accès au modèle ${PLATFORM_CONFIG.GPT_MODEL} pour un contenu plus précis`,
    detailedDashboard: "Tableau de bord détaillé et insights avancés",
    
    // Account management
    accountManagement: "Gestion de Compte",
    accountInfo: "Informations du Compte",
    subscriptionPlan: "Plan d'abonnement",
    generatedSheets: "Fiches générées",
    accountSecurity: "Sécurité du Compte",
    changePasswordSecurity: "Modifiez votre mot de passe pour sécuriser votre compte",
    changePassword: "Changer le Mot de Passe",
    accountDeletion: "Suppression de Compte",
    deleteAccountWarning: "Supprimez définitivement votre compte et toutes vos données. Cette action est irréversible.",
    deleteAccount: "Supprimer le Compte",
    securityTips: "Conseils de Sécurité",
    passwordTip: `Utilisez un mot de passe fort avec au moins ${PLATFORM_CONFIG.PASSWORD_MIN_LENGTH} caractères`,
    dataTip: "Exportez régulièrement vos fiches pour les sauvegarder",
    emailTip: "Gardez votre adresse email à jour pour recevoir les notifications",
    loginTip: "Déconnectez-vous toujours après utilisation sur un appareil partagé",
    
    // History
    historyTitle: "Historique des Fiches Générées",
    generatedOn: "Généré le",
    viewDetails: "Voir détails",
    
    // Admin panel
    adminTitle: "Administration ECOMSIMPLY",
    adminSubtitle: "Panneau de contrôle administrateur - Accès complet à la plateforme",
    globalStats: "Statistiques Globales",
    users: "Utilisateurs",
    activity: "Activité",
    messages: "Messages",
    totalUsers: "Total Utilisateurs",
    administrators: "Administrateurs",
    regularUsers: "Utilisateurs Réguliers",
    subscriptions: "Abonnements",
    totalRevenue: "Revenus Total",
    monthlyRevenue: "Revenus ce Mois",
    activityLast30Days: `Activité (${PLATFORM_CONFIG.ANALYTICS_DAYS} derniers jours)`,
    deletedAccounts: "Comptes Supprimés",
    upgrades: "Mises à Niveau",
    cancellations: "Annulations",
    
    // Contact form
    contactUs: "Nous Contacter",
    contactQuestion: "Une question ? Nous sommes là pour vous aider !",
    yourName: "Votre nom",
    yourEmail: "Votre email",
    chooseSubject: "Choisir un sujet",
    yourMessage: "Votre message...",
    sendMessage: "Envoyer le Message",
    
    // Chatbot
    chatbotTitle: "Assistant ECOMSIMPLY",
    chatbotSupport: `IA Support – Disponible ${PLATFORM_CONFIG.SUPPORT_HOURS}`,
    typeMessage: "Tapez votre message...",
    
    // Pricing specific
    mostChosen: "Le plus choisi",
    testWithoutCommitment: "Pour tester sans engagement",
    oneSheetPerMonth: `${PLATFORM_CONFIG.FREE_SHEETS_LIMIT} fiche par mois`,
    hundredSheetsPerMonth: `${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois`,
    unlimitedSheets: `Fiches ${PLATFORM_CONFIG.PREMIUM_SHEETS_UNLIMITED}`,
    advancedAiGpt4o: `IA avancée (${PLATFORM_CONFIG.GPT_MODEL})`,
    highQualityImages: "Images haute qualité (fal.ai Flux Pro)",
    multiFormatExport: "Export multi-format",
    prioritySupport: "Support prioritaire",
    aiAccessPriority: "Priorité d'accès IA",
    dedicatedSupport: "Support dédié",
    
    // Other
    unsubscribe: "Se Désabonner",
    resetPassword: "Réinitialiser le mot de passe",
    
    // Contact form additional translations
    generalQuestion: "Question générale",
    technicalSupport: "Support technique", 
    commercialRequest: "Demande commerciale",
    paymentIssue: "Problème de paiement",
    improvementSuggestion: "Suggestion d'amélioration",
    other: "Autre",
    messageSent: "Message Envoyé !",
    respondSoon: "Nous vous répondrons dans les plus brefs délais.",
    sending: "Envoi...",
    data: "Données",
    loginTip: "Déconnexion",
    loginTipText: "Déconnectez-vous toujours après utilisation sur un appareil partagé",
    noSheetsGenerated: "Aucune fiche produit générée pour le moment.",
    
    // Feedback System
    feedbackTitle: "📊 Votre avis nous intéresse",
    feedbackQuestion: "Cette fiche produit vous a-t-elle été utile ?",
    feedbackUseful: "👍 Utile",
    feedbackNotUseful: "👎 Pas utile",
    feedbackThanks: "Merci pour votre retour !",
    feedbackSubmitting: "Envoi en cours...",
    feedbackError: "Erreur lors de l'envoi du feedback",
    feedbackHelp: "Votre feedback nous aide à améliorer la qualité des fiches générées"
  },
  en: {
    // Navigation & Header
    connection: "Login",
    register: "Sign Up",
    logout: "Logout",
    
    // Landing Page  
    heroTitle: "Generate Perfect Product Sheets with AI",
    heroSubtitle: "Transform your product descriptions into professional, SEO-optimized e-commerce sheets in seconds. Powered by advanced AI technology.",
    tryFree: "Try Free",
    
    // Features
    featuresTitle: "Powerful Features",
    aiGeneration: "AI Generation",
    aiGenerationDesc: "Advanced AI to create optimized product sheets",
    analyticsDashboard: "Analytics Dashboard",
    analyticsDashboardDesc: "Track your performance and optimize your results",
    easyExport: "Easy Export",
    easyExportDesc: "Export your sheets in multiple popular formats",
    
    // New Features 2024
    bulkPublication: "Bulk Publication",
    bulkPublicationDesc: "Publish multiple sheets simultaneously to your stores",
    multiPlatform: "Multi-Platform",
    multiPlatformDesc: "Connect Shopify, WooCommerce, Amazon, eBay, Etsy, Facebook and Google Shopping",
    advancedAI: "Premium AI",
    advancedAIDesc: "Smart SEO, competitive analysis, price optimization and multilingual translation",
    smartSelection: "Smart Selection",
    smartSelectionDesc: "AI-optimized selection for personalized results",
    readyToBoost: "Ready to boost your e-commerce?",
    
    // Pricing
    pricingTitle: "Transparent Pricing",
    planFree: "Free",
    planPro: "Pro", 
    planPremium: "Premium",
    planFreePriceDesc: `${PLATFORM_CONFIG.FREE_SHEETS_LIMIT} sheet per month`,
    planProPriceDesc: `${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} sheets per month`,
    planPremiumPriceDesc: `${PLATFORM_CONFIG.PREMIUM_SHEETS_UNLIMITED} sheets`,
    mostChosen: "Most Chosen",
    chooseThisPlan: "Choose This Plan",
    
    // Dashboard Tabs
    aiGenerator: "AI Generator",
    dashboard: "Dashboard", 
    subscription: "Subscription",
    history: "History",
    accountManagement: "Account Management",
    admin: "Admin",
    
    // NEW PREMIUM TABS
    aiFeatures: "Advanced AI",
    ecommerceIntegrations: "Integrations",
    premiumAnalytics: "Pro Analytics",
    
    // AI Features
    seoAnalysis: "SEO Analysis",
    competitorAnalysis: "Competitor Analysis",
    priceOptimization: "Price Optimization",
    multilingualTranslation: "Multi-Language Translation",
    productVariants: "Product Variants",
    
    // E-commerce Integrations
    connectStore: "Connect Store",
    manageStores: "Manage Stores",
    publishProduct: "Publish Product",
    integrationLogs: "Integration Logs",
    
    // Premium Analytics
    productPerformance: "Product Performance",
    integrationPerformance: "Integration Performance",
    userEngagement: "User Engagement",
    businessIntelligence: "Business Intelligence",
    
    // Premium Features Messages
    premiumRequired: "Premium Feature",
    premiumRequiredDesc: "This feature requires a Pro or Premium subscription",
    tryFree: "Try for free",
    bulkSelectHelp: "Check sheets to publish or export in bulk, or use \"Publish All\" to publish everything",
    productToPublish: "Product to publish:",
    
    // Publish to Store
    publishToStore: "Publish to Store",
    selectStore: "Select a store",
    publishProduct: "Publish product",
    noStoresConnected: "No stores connected",
    connectStoresFirst: "First connect your stores in the Integrations tab",
    publishingToStore: "Publishing to",
    publishedSuccessfully: "Product published successfully to",
    publishError: "Error during publication",
    
    // Bulk Publishing
    bulkPublish: "Publish Selection",
    selectSheets: "Select sheets",
    selectedSheetsCount: "sheets selected",
    selectAll: "Select all",
    deselectAll: "Deselect all",
    publishSelectedSheets: "Publish selected sheets",
    bulkPublishSuccess: "Bulk publish successful",
    bulkPublishPartial: "Bulk publish partially successful",
    bulkPublishFailed: "Bulk publish failed",
    
    noPayments: "No payments",
    noPaymentsText: "No payments recorded",
    noUsers: "No users",
    noActivity: "No activity",
    noContacts: "No contacts",
    loading: "Loading...",
    action: "Action",
    message: "Message",
    date: "Date",
    status: "Status",
    responded: "Responded",
    pending: "Pending",
    aiGenerateImages: "AI will generate professional images with different viewing angles",
    professionalProductImages: "Professional product images",
    optimizedImagesForEcommerce: "optimized image(s) for e-commerce",
    optimizedTitle: "Optimized Title",
    marketingDescription: "Marketing Description",
    seoTags: "SEO Tags",
    priceSuggestions: "Price Suggestions",
    targetAudience: "Target Audience",
    callToAction: "Call to Action",
    
    // Forms & Inputs
    email: "Email",
    password: "Password",
    confirmPassword: "Confirm Password",
    currentPassword: "Current Password",
    newPassword: "New Password",
    name: "Name",
    productName: "Product name",
    productDescription: "Product description",
    productCategory: "Product Category",
    customCategory: "Custom Category",
    selectCategory: "Select a category",
    categoryHelpsTargetSeo: "Selecting a category helps target SEO and optimize tags",
    enterCustomCategory: "Enter your custom category...",
    numberOfImages: "Number of images to generate",
    generateSheet: "Generate Sheet",
    
    // Buttons & Actions
    login: "Log In",
    signup: "Sign Up",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    export: "Export",
    upgrade: "Upgrade",
    downgrade: "Downgrade",
    submit: "Submit",
    publish: "PUBLISH",
    exportAll: "EXPORT ALL",
    close: "Close",
    confirm: "Confirm",
    preview: "Preview",
    
    // Messages & Status
    welcome: "Welcome",
    loading: "Loading...",
    error: "Error",
    success: "Success",
    warning: "Warning",
    info: "Information",
    processing: "Processing...",
    completed: "Completed",
    failed: "Failed",
    
    // Language Selection
    selectLanguage: "Select language",
    currentLanguage: "Current language",
    languageChanged: "Language changed successfully",
    
    // Dashboard Content
    welcomeMessage: "Welcome to your ECOMSIMPLY dashboard",
    generateFirstSheet: "Generate your product sheet",
    totalSheets: "Total sheets",
    thisMonth: "This month",
    upgradeToUnlock: "Upgrade to unlock more features", 
    monthlyUsage: "Monthly usage",
    accountAge: "Account age",
    upgradeDescription: "Unlock more sheets, advanced AI and premium features",
    seeFullPlansOnHomepage: "See full plans on homepage",
    
    // Product Sheet
    generatedTitle: "Generated title",
    marketingDescription: "Marketing description",
    keyFeatures: "Key features",
    seoTags: "SEO tags",
    priceSuggestions: "Price suggestions",
    targetAudience: "Target audience",
    callToAction: "Call to action",
    
    describeProduct: "Describe your product",
    
    // Progress Messages
    analysisDone: "Product analysis completed",
    creatingFeatures: "Creating key features...",
    generatingImage: "Generating optimized image",
    sheetGenerated: "Product sheet generated",
    seoOptimized: "SEO Optimized – ready for Shopify",
    
    // Progress Messages (continued)
    productAnalysis: "Product analysis...",
    aiContentGeneration: "AI content generation...",
    characteristicsCreation: "Creating characteristics...",
    imageGeneration: "Image generation...",
    finalization: "Finalizing...",
    noSheetsGenerated: "No product sheets generated yet.",
    exportThisSheet: "Export this sheet",
    exportSheets: "Export sheets",
    chooseExportFormat: "Choose export format for this product sheet:",
    chooseExportFormatMultiple: "Choose export format for your product sheets:",
    includeImages: "Include images in export",
    onlyProductInfo: "Only product information",
    exportInProgress: "Export in progress...",
    exportAll: "Export all",
    exportSelected: "Export selected",
    newFeature: "New feature",
    imagesIncluded: "Generated images are now included in all exports!",
    individualExport: "Individual sheet export only",
    productImages: "Product Images",
    lastUpdate: "Last update",
    whyUpgradeToPremium: "Why upgrade to premium?",
    whyUpgradeToHigher: "Why upgrade your plan?",
    whyDowngradeWarning: "Plan downgrade warning",
    changeSubscriptionPlan: "Change subscription plan",
    tryFree: "Try for free",
    upgradeToProPrice: "Upgrade to Pro - €29/mo",
    upgradeToPremium: "Upgrade to Premium",
    downgradeTo: "Downgrade to",
    currentPlanBenefits: "Current plan benefits", 
    planChangeOptions: "Plan change options",
    moreSheets: "More sheets",
    advancedAi: "Advanced AI",
    analytics: "Analytics",
    generateUpTo100Sheets: "Generate up to 100 sheets per month with Pro plan",
    accessGpt4oModel: "Access to GPT-4o model for more precise content",
    detailedDashboardInsights: "Detailed dashboard and advanced insights",
    subscriptionManagement: "Subscription Management",
    
    // Product Description
    optimizedDescription: "Optimized description",
    keyCharacteristics: "Key characteristics",
    
    // Missing English texts I need to add
    ourAiThinking: "Our AI is thinking of the best sheet for you...",
    generateAnother: "Generate another sheet",
    everything: "Everything you need to create perfect product sheets",
    aiPoweredGeneration: "AI Powered Generation",
    aiPoweredDesc: "Advanced AI instantly creates professional product descriptions, features and marketing content.",
    analyticsBoard: "Analytics Dashboard",
    analyticsBoardDesc: "Track your generated sheets, monitor performance and analyze your product catalog.",
    easyExportTitle: "Easy Export",
    easyExportLongDesc: "Export your product sheets to CSV, PDF, or integrate directly with your e-commerce platform.",
    viewShopify: "Publish to platform",
    instantGeneration: "Advanced Premium AI",
    instantDesc: "Automatic SEO, competitive analysis and price optimization with GPT-4o to maximize your sales.",
    professionalQuality: "Multi-Platform Publishing",
    professionalDesc: "Connect 7 e-commerce platforms (Shopify, Amazon, eBay, WooCommerce...) and publish in bulk instantly.",
    multipleExport: "Real-Time Dynamic Tracking",
    multipleExportDesc: "Usage statistics, account age and data automatically updated every 30 seconds.",
    guaranteedResults: "Guaranteed Results",
    guaranteedDesc: "Over 10,000 product sheets generated with a 98% customer satisfaction rate.",
    avgGenerationTime: "Average generation time",
    seconds28: "28 seconds",
    pricing: "Pricing",
    plansAdapted: "Plans adapted to your needs",
    freeDesc: "To test without commitment",
    proDesc: "Ideal for growing store",
    premiumDesc: "Maximum performance for high volumes",
    startFree: "Start Free",
    choosePro: "Choose Pro",
    choosePremium: "Choose Premium",
    testimonials: "Testimonials",
    whatClientsSay: "What our customers say",
    discoverWhy: "Discover why over 10,000 e-merchants trust ECOMSIMPLY",
    satisfiedClients: "Satisfied clients",
    averageRating: "Average rating",
    satisfactionRate: "Satisfaction rate",
    shareExperience: "Share your experience",
    helpOthers: "Using ECOMSIMPLY? Help other entrepreneurs by sharing your review",
    leaveTestimonial: "Leave a testimonial",
    imageGeneratedByAi: "AI generated image",
    
    // Bulk Publishing
    bulkPublish: "Publish Selection",  
    selectSheets: "Select sheets",
    selectedSheetsCount: "sheets selected",
    selectAll: "Select all",
    deselectAll: "Deselect all",
    publishSelectedSheets: "Publish selected sheets",
    bulkPublishSuccess: "Bulk publish successful",
    bulkPublishPartial: "Bulk publish partially successful",  
    bulkPublishFailed: "Bulk publish failed",
    
    // New Pricing Features
    ecommercePlateforms: "Connect 7 e-commerce platforms",
    bulkPublishFeature: "Bulk publication",
    advancedAiFeatures: "Premium AI (SEO, analysis, pricing)",
    smartSelectionFeature: "Smart multi-selection",
    realTimeAnalytics: "Real-time analytics",
    multilingualTranslation: "Multilingual translation",
    competitiveAnalysis: "Competitive analysis",
    priceOptimization: "Price optimization",
    
    // Enhanced Plan Features
    basicPlanFeatures: "Basic features",
    proPlanFeatures: "Pro features + Integrations",
    premiumPlanFeatures: "All features + Dedicated support",
    
    // Additional translations for remaining hardcoded texts
    loginConnection: "🔐 Login",
    enjoyPremiumFeatures: "You can now enjoy all premium features!",
    cancelSubscriptionWarning: "If you wish to cancel your subscription, you will return to the free plan and lose access to premium features.",
    cancelSubscriptionInfo: "By canceling your subscription, you will return to the free plan (1 sheet/month). You will lose access to premium features.",
    subscriptionCancelledSuccess: "Subscription cancelled successfully. You are now on the free plan.",
    freePlan: "Free Plan",
    chatbotTechnicalError: "Sorry, I'm experiencing a technical issue. Can I help you with something else? You can ask me about pricing, usage, or features!",
    connectionFailed: "Connection failed",
    chatbotWelcome: "Hello! I'm your ECOMSIMPLY assistant. How can I help you today?",
    createAccountFirst: "To continue, please first create a free account. You can then upgrade to this plan from your dashboard.",
    subscriptionFreeDesc: "You currently have 1 product sheet per month with our basic AI generator.",
    subscriptionProDesc: "You have 100 product sheets per month with our advanced AI generator.",
    subscriptionPremiumDesc: "You have unlimited product sheets with our premium AI generator.",
    usedThisMonth: "Used this month",
    currentPlan: "Current Plan",
    premium: "Premium",
    basicAiGeneration: "Basic AI generation",
    registering: "Registering...",
    choosePro: "Choose Pro",
    averageRating: "Average rating",
    satisfactionRate: "Satisfaction rate",
    discover: "Discover",
    downloadCsv: "Download CSV",
    viewOnShopify: "Publish to platform",
    edit: "Edit",
    
    
    generatedDescriptionTitle: "Generated description",
    keyCharacteristicsTitle: "Key characteristics",
    aiGeneratedImage: "AI generated image",
    
    // Dashboard translations
    totalSheets: "Total Sheets",
    thisMonth: "This Month",
    thisWeek: "This Week",
    categoryBreakdown: "Category Breakdown",
    generationType: "Generation Type",
    artificialIntelligence: "Artificial Intelligence",
    simulatedGeneration: "Simulated Generation",
    averageCharacteristics: "Average characteristics/sheet",
    popularKeywords: "Popular Keywords",
    generationTrends: "Generation Trends (Last 7 days)",
    mostProductiveDay: "Most productive day",
    
    // Subscription management
    subscriptionManagement: "Subscription Management",
    priceSuggestions: "Price Suggestions",
    targetAudience: "Target Audience",
    callToAction: "Call to Action",
    emailSupport: "Email support",
    
    // Admin Panel
    adminPanelTitle: "ECOMSIMPLY Administration",
    adminPanelSubtitle: "Administrator control panel - Full platform access",
    stats: "Statistics",
    users: "Users",
    activity: "Activity",
    messages: "Messages",
    globalStats: "Global Statistics",
    totalUsers: "Total Users",
    administrators: "Administrators",
    regularUsers: "Regular Users",
    subscriptions: "Subscriptions",
    totalRevenue: "Total Revenue",
    monthlyRevenue: "Monthly Revenue",
    activityLast30Days: "Activity (Last 30 days)",
    deletedAccounts: "Deleted Accounts",
    upgrades: "Upgrades",
    cancellations: "Cancellations",
    userList: "User List",
    subscriptionPlan: "Subscription plan",
    registeredOn: "Registered on",
    lastConnection: "Last connection",
    activityLogs: "Activity Logs",
    contactMessages: "Contact Messages",
    replyTo: "Reply to",
    reply: "Reply",
    replyResponseSent: "Response sent successfully!",
    noContacts: "No contact messages.",
    createNewAdmin: "Create New Administrator",
    adminCreated: "Administrator created successfully",
    createAdmin: "Create Admin",
    revenue: "Revenue",
    userManagement: "User Management",
    user: "User",
    plan: "Plan",
    sheets: "Sheets",
    payments: "Payments",
    registration: "Registration",
    role: "Role",
    admin: "Admin",
    recommended: "Recommended",
    idealForGrowingStore: "Ideal for growing store",
    maxPerformanceHighVolume: "Maximum performance for high volume",
    whyUpgradePremium: "Why upgrade to premium?",
    moreSheets: "More sheets",
    advancedAi: "Advanced AI",
    analytics: "Analytics",
    generateUpTo100: "Generate up to 100 sheets per month with Pro plan",
    accessGpt4o: "Access to GPT-4o model for more precise content",
    detailedDashboard: "Detailed dashboard and advanced insights",
    
    // Account management
    accountManagement: "Account Management",
    accountInfo: "Account Information",
    subscriptionPlan: "Subscription plan",
    generatedSheets: "Generated sheets",
    accountSecurity: "Account Security",
    changePasswordSecurity: "Change your password to secure your account",
    changePassword: "Change Password",
    accountDeletion: "Account Deletion",
    deleteAccountWarning: "Permanently delete your account and all your data. This action is irreversible.",
    deleteAccount: "Delete Account",
    securityTips: "Security Tips",
    passwordTip: "Use a strong password with at least 8 characters",
    dataTip: "Regularly export your sheets to save them",
    emailTip: "Keep your email address up to date to receive notifications",
    loginTip: "Always log out after use on a shared device",
    
    // History
    historyTitle: "Generated Sheets History",
    generatedOn: "Generated on",
    viewDetails: "View details",
    
    // Admin panel
    adminTitle: "ECOMSIMPLY Administration",
    adminSubtitle: "Administrator control panel - Full platform access",
    globalStats: "Global Statistics",
    users: "Users",
    activity: "Activity",
    messages: "Messages",
    totalUsers: "Total Users",
    administrators: "Administrators",
    regularUsers: "Regular Users",
    subscriptions: "Subscriptions",
    totalRevenue: "Total Revenue",
    monthlyRevenue: "Monthly Revenue",
    activityLast30Days: "Activity (Last 30 days)",
    deletedAccounts: "Deleted Accounts",
    upgrades: "Upgrades",
    cancellations: "Cancellations",
    
    // Contact form
    contactUs: "Contact Us",
    contactQuestion: "Have a question? We're here to help!",
    yourName: "Your name",
    yourEmail: "Your email",
    chooseSubject: "Choose a subject",
    yourMessage: "Your message...",
    sendMessage: "Send Message",
    
    // Chatbot
    chatbotTitle: "ECOMSIMPLY Assistant",
    chatbotSupport: "AI Support – Available 24/7",
    typeMessage: "Type your message...",
    
    // Pricing specific
    mostChosen: "Most chosen",
    testWithoutCommitment: "To test without commitment",
    oneSheetPerMonth: "1 sheet per month",
    hundredSheetsPerMonth: "100 sheets per month",
    unlimitedSheets: "Unlimited sheets",
    advancedAiGpt4o: "Advanced AI (GPT-4o)",
    highQualityImages: "High quality images (fal.ai Flux Pro)",
    multiFormatExport: "Multi-format export",
    prioritySupport: "Priority support",
    aiAccessPriority: "AI access priority",
    dedicatedSupport: "Dedicated support",
    
    // Other
    unsubscribe: "Unsubscribe",
    
    // Contact form additional translations
    generalQuestion: "General question",
    technicalSupport: "Technical support",
    commercialRequest: "Commercial request", 
    paymentIssue: "Payment issue",
    improvementSuggestion: "Improvement suggestion",
    other: "Other",
    messageSent: "Message Sent!",
    respondSoon: "We will get back to you as soon as possible.",
    sending: "Sending...",
    data: "Data",
    loginTip: "Logout",
    loginTipText: "Always log out after use on a shared device",
    noSheetsGenerated: "No product sheets generated yet.",
    resetPassword: "Reset Password",
    
    // Feedback System
    feedbackTitle: "📊 Your opinion matters",
    feedbackQuestion: "Was this product sheet useful to you?",
    feedbackUseful: "👍 Useful",
    feedbackNotUseful: "👎 Not useful", 
    feedbackThanks: "Thank you for your feedback!",
    feedbackSubmitting: "Submitting...",
    feedbackError: "Error sending feedback",
    feedbackHelp: "Your feedback helps us improve the quality of generated sheets"
  }
};

// Language Context
const LanguageContext = createContext();

const LanguageProvider = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState(localStorage.getItem('language') || 'fr');
  const [supportedLanguages, setSupportedLanguages] = useState({});

  // Load supported languages from backend
  useEffect(() => {
    const loadSupportedLanguages = async () => {
      try {
        const response = await axios.get(`${API}/languages`);
        // ✅ CORRECTION 1: Fix parsing nested response structure
        setSupportedLanguages(response.data.supported_languages || response.data);
      } catch (error) {
        console.error('Error loading supported languages:', error);
        // Use default languages as fallback if backend fails
        setSupportedLanguages({
          fr: { name: "Français", flag: "🇫🇷" },
          en: { name: "English", flag: "🇺🇸" }
        });
      }
    };
    loadSupportedLanguages();
  }, []);

  const changeLanguage = async (newLanguage) => {
    try {
      // Update language preference in backend if user is authenticated
      const token = localStorage.getItem('token');
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        await axios.post(`${API}/auth/change-language`, { language: newLanguage });
      }
      
      // Update local state
      setCurrentLanguage(newLanguage);
      localStorage.setItem('language', newLanguage);
    } catch (error) {
      console.error('Error changing language:', error);
      // Still update locally even if backend update fails
      setCurrentLanguage(newLanguage);
      localStorage.setItem('language', newLanguage);
    }
  };

  // ✅ CORRECTION 2: Enhanced translation function with debug warnings
  const t = (key) => {
    const translation = TRANSLATIONS[currentLanguage]?.[key] || TRANSLATIONS['fr']?.[key];
    
    // Debug warning for missing translations in development
    if ((!translation || translation === key) && process.env.NODE_ENV === 'development') {
      console.warn(`🌍 Missing translation for key: "${key}" in language: ${currentLanguage}`);
    }
    
    return translation || key;
  };

  return (
    <LanguageContext.Provider value={{ 
      currentLanguage, 
      changeLanguage, 
      t, 
      supportedLanguages 
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

// Hook to use language context
const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

// Enhanced Language Selector Component - Sophisticated & User-friendly
const LanguageSelector = () => {
  const { currentLanguage, changeLanguage, supportedLanguages, t } = useLanguage();
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);

  // ✅ CORRECTION 5: Enhanced default languages for immediate display
  const defaultLanguages = {
    fr: { 
      name: "Français", 
      flag: "🇫🇷",
      ai_instruction: "Réponds en français de manière professionnelle et claire." 
    },
    en: { 
      name: "English", 
      flag: "🇺🇸",
      ai_instruction: "Reply in professional and clear English." 
    }
  };
  
  const languages = Object.keys(supportedLanguages).length > 0 ? supportedLanguages : defaultLanguages;
  const currentLang = languages[currentLanguage] || languages['fr'];

  return (
    <div className="relative">
      {/* Enhanced Language Selector Button */}
      <button
        onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
        className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm border border-white/20 hover:border-white/40 px-3 py-2 rounded-lg text-white hover:bg-white/20 transition-all duration-300 font-medium shadow-lg hover:shadow-xl"
        style={{ minWidth: '110px' }}
      >
        <span className="text-lg">{currentLang?.flag || '🌐'}</span>
        <span className="text-sm font-semibold">{currentLang?.name || 'Language'}</span>
        <svg 
          className={`w-4 h-4 transition-transform duration-200 ${showLanguageDropdown ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Enhanced Dropdown Menu */}
      {showLanguageDropdown && (
        <div className="absolute right-0 mt-3 w-48 bg-white rounded-xl shadow-2xl z-50 border border-gray-100 overflow-hidden">
          <div className="py-2">
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide border-b border-gray-100">
              {t('selectLanguage')}
            </div>
            {Object.entries(languages).map(([code, lang]) => (
              <button
                key={code}
                onClick={() => {
                  changeLanguage(code);
                  setShowLanguageDropdown(false);
                }}
                className={`w-full text-left px-4 py-3 text-sm flex items-center space-x-3 hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 transition-all duration-200 group ${
                  currentLanguage === code 
                    ? 'bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 font-medium' 
                    : 'text-gray-700 hover:text-purple-600'
                }`}
              >
                <span className="text-xl">{lang.flag}</span>
                <span className="flex-1 font-medium">{lang.name}</span>
                {currentLanguage === code && (
                  <div className="flex items-center space-x-1">
                    <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
                {currentLanguage !== code && (
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Initialize auth state on app startup
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('currentUser');
      
      console.log('🔧 AUTH INIT - Token:', !!storedToken, 'User:', !!storedUser);
      
      if (storedToken && storedUser) {
        try {
          const user = JSON.parse(storedUser);
          if (!user.email) {
            console.log('🔧 AUTH INIT - Invalid user data, logging out');
            logout();
            return;
          }
          
          // Set token and configure axios
          setToken(storedToken);
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Try to verify token is still valid, but if it fails, still restore user for offline usage
          try {
            const response = await axios.get(`${API}/health`);
            if (response.status === 200) {
              // Token is likely valid, restore user
              setUser(user);
              setLoading(false);
              console.log('🔧 AUTH RESTORED - User restored:', user.email, 'Admin:', user.is_admin);
              
              // Check for trial activation ONLY after successful authentication
              await checkTrialActivation();
              return;
            }
          } catch (tokenError) {
            console.log('🔧 AUTH INIT - Token validation failed, but restoring user anyway:', tokenError.message);
          }
          
          // Even if token validation fails, restore user state for better UX
          setUser(user);
          setLoading(false);
          console.log('🔧 AUTH RESTORED (FALLBACK) - User restored from localStorage:', user.email);
          
        } catch (error) {
          // User data corrupted, logout
          console.log('🔧 AUTH INIT - Error parsing user data, logging out:', error);
          logout();
        }
      } else {
        console.log('🔧 AUTH INIT - No stored credentials');
        setLoading(false);
        
        // For non-authenticated users, check trial activation but handle 403 gracefully
        await checkTrialActivationUnauthenticated();
      }
    };
    
    // Function to handle trial activation from URL parameters (for authenticated users)
    const checkTrialActivation = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const trialActivated = urlParams.get('trial_activated');
      const planType = urlParams.get('plan');
      const sessionId = urlParams.get('session_id');
      
      if (trialActivated === 'true' && planType && sessionId) {
        console.log('🎯 Trial activation detected in URL for authenticated user:', { planType, sessionId });
        
        try {
          // Call the backend to complete trial activation
          const token = localStorage.getItem('token');
          if (token) {
            const response = await axios.get(`${API}/payments/trial-success/${sessionId}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.data.status === 'success') {
              console.log('✅ Trial activation successful:', response.data);
              
              // Update user data to reflect trial status
              const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
              const updatedUser = {
                ...currentUser,
                subscription_plan: planType,
                is_trial_user: true,
                trial_days_remaining: 7
              };
              localStorage.setItem('currentUser', JSON.stringify(updatedUser));
              setUser(updatedUser);
              
              // Show success message using DOM manipulation
              setTimeout(() => {
                // Create success notification element
                const successElement = document.createElement('div');
                successElement.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50 max-w-md text-center';
                successElement.textContent = '🎉 Votre essai gratuit 3 jours a été activé avec succès! Profitez de toutes les fonctionnalités premium.';
                document.body.appendChild(successElement);
                
                // Clean URL parameters
                window.history.replaceState({}, document.title, window.location.pathname);
                
                // Remove success message and redirect after 3 seconds
                setTimeout(() => {
                  if (document.body.contains(successElement)) {
                    document.body.removeChild(successElement);
                  }
                  // Force page reload to refresh the dashboard view
                  window.location.reload();
                }, 3000);
              }, 500);
            }
          }
        } catch (error) {
          console.error('❌ Trial activation failed for authenticated user:', error);
          
          // Use setTimeout to set error after component mounts
          setTimeout(() => {
            const errorMessage = error.response?.data?.detail || 'Erreur lors de l\'activation de votre essai gratuit. Veuillez contacter le support.';
            console.error('Setting error:', errorMessage);
            
            // Try to find and display error in UI
            const errorElement = document.createElement('div');
            errorElement.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
            errorElement.textContent = 'Erreur lors de la vérification du paiement. Veuillez réessayer.';
            document.body.appendChild(errorElement);
            
            // Remove error after 5 seconds
            setTimeout(() => {
              if (document.body.contains(errorElement)) {
                document.body.removeChild(errorElement);
              }
            }, 5000);
            
            // Clean URL parameters even on error
            window.history.replaceState({}, document.title, window.location.pathname);
          }, 1000);
        }
      }
    };
    
    // Function to handle trial activation for unauthenticated users (just clean URL)
    const checkTrialActivationUnauthenticated = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const trialActivated = urlParams.get('trial_activated');
      const planType = urlParams.get('plan');
      const sessionId = urlParams.get('session_id');
      
      if (trialActivated === 'true' && planType && sessionId) {
        console.log('🔧 Trial activation detected for unauthenticated user - cleaning URL without API call');
        
        // For unauthenticated users, just clean the URL parameters
        // They should not see trial activation attempts
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Show a message to log in first if they want to complete trial
        setTimeout(() => {
          const infoElement = document.createElement('div');
          infoElement.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded z-50 max-w-md text-center';
          infoElement.textContent = '🔐 Veuillez vous connecter pour activer votre essai gratuit.';
          document.body.appendChild(infoElement);
          
          // Remove info after 4 seconds
          setTimeout(() => {
            if (document.body.contains(infoElement)) {
              document.body.removeChild(infoElement);
            }
          }, 4000);
        }, 500);
      }
    };
    
    initializeAuth();
  }, []);
  
  // Debug auth state changes
  useEffect(() => {
    console.log('🔧 AUTH STATE UPDATE - User:', user?.email || 'null', 'Token:', !!token, 'Loading:', loading);
  }, [user, token, loading]);

  // Configure axios interceptor for token management
  useEffect(() => {
    // Request interceptor to add token to requests
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        const currentToken = localStorage.getItem('token');
        if (currentToken) {
          config.headers.Authorization = `Bearer ${currentToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle expired tokens
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid, logout user
          console.log('Received 401, logging out user');
          logout();
        }
        return Promise.reject(error);
      }
    );

    // Cleanup interceptors on unmount
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  const checkAuth = async () => {
    try {
      // Get user stats to verify auth and get latest user data
      const statsResponse = await axios.get(`${API}/stats`);
      setLoading(false);
      
      // The stats response includes updated subscription info
      return statsResponse.data;
    } catch (error) {
      logout();
      throw error;
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      
      // Handle the API response structure with 'ok' field
      if (response.data.ok && response.data.token && response.data.user) {
        const { token, user } = response.data;
        
        // Store token and user data in localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('currentUser', JSON.stringify(user));  // Use 'currentUser' for consistency
        
        setToken(token);
        setUser(user);
        console.log('🔧 LOGIN SUCCESS - User set:', user.email, 'Admin:', user.is_admin);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        return { success: true };
      } else {
        console.error('❌ Invalid response structure:', response.data);
        return { success: false, error: 'Réponse serveur invalide' };
      }
    } catch (error) {
      console.error('❌ Login error:', error.response?.data);
      return { success: false, error: error.response?.data?.detail || 'Connexion échouée' };
    }
  };

  const register = async (name, email, password, planType = null) => {
    try {
      // ✅ SRE FIX: Always use working /api/auth/register endpoint
      // Trial plan logic handled after successful registration
      const requestData = { name, email, password };
      const endpoint = `${API}/auth/register`;
      
      const response = await axios.post(endpoint, requestData);
      const { token, user } = response.data;
      
      // Store token and user data in localStorage
      localStorage.setItem('token', token);
      localStorage.setItem('currentUser', JSON.stringify(user));
      
      // ✅ Store trial plan info for post-registration handling
      if (planType) {
        localStorage.setItem('pendingTrialPlan', planType);
        console.log(`🎯 Trial plan ${planType} stored for post-registration setup`);
      }
      
      // Update axios defaults
      setToken(token);
      setUser(user);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      return { 
        success: true, 
        user, 
        trialInfo: planType ? { plan_type: planType, status: 'pending_activation' } : null,
        message: response.data.message 
      };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Inscription échouée' 
      };
    }
  };

  const logout = () => {
    // Remove token and user data from localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('currentUser');  // Use 'currentUser' for consistency
    
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Contact Form Component
const ContactForm = () => {
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const submitContact = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/contact`, contactForm);
      setSuccess(true);
      setContactForm({ name: '', email: '', subject: '', message: '' });
      
      setTimeout(() => {
        setSuccess(false);
        setIsOpen(false);
      }, 3000);
      
    } catch (error) {
      console.error('Erreur envoi contact:', error);
      setError('Erreur lors de l\'envoi du message. Veuillez réessayer.');
    }
    setLoading(false);
  };

  return (
    <div className="fixed bottom-4 left-4 z-60">
      {isOpen && (
        <div className="bg-white rounded-lg shadow-2xl w-96 mb-4 border">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">📧 {t('contactUs')}</h3>
              <button onClick={() => setIsOpen(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <p className="text-xs opacity-90 mt-1">{t('contactQuestion')}</p>
          </div>
          
          <div className="p-4">
            {success ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{t('messageSent')}</h4>
                <p className="text-gray-600 text-sm">{t('respondSoon')}</p>
              </div>
            ) : (
              <form onSubmit={submitContact} className="space-y-4">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                    {error}
                  </div>
                )}
                
                <div>
                  <input
                    type="text"
                    placeholder={t('yourName')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    value={contactForm.name}
                    onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                    required
                  />
                </div>
                
                <div>
                  <input
                    type="email"
                    placeholder={t('yourEmail')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    value={contactForm.email}
                    onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                    required
                  />
                </div>
                
                <div>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    value={contactForm.subject}
                    onChange={(e) => setContactForm({...contactForm, subject: e.target.value})}
                    required
                  >
                    <option value="">{t('chooseSubject')}</option>
                    <option value="Question générale">{t('generalQuestion')}</option>
                    <option value="Support technique">{t('technicalSupport')}</option>
                    <option value="Demande commerciale">{t('commercialRequest')}</option>
                    <option value="Problème de paiement">{t('paymentIssue')}</option>
                    <option value="Suggestion d'amélioration">{t('improvementSuggestion')}</option>
                    <option value="Autre">{t('other')}</option>
                  </select>
                </div>
                
                <div>
                  <textarea
                    rows="4"
                    placeholder={t('yourMessage')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none"
                    value={contactForm.message}
                    onChange={(e) => setContactForm({...contactForm, message: e.target.value})}
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 transition-all duration-200"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {t('sending')}
                    </span>
                  ) : t('sendMessage')}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white p-3 rounded-full shadow-lg transition-all duration-300 transform hover:scale-110"
        title="Nous contacter"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </button>
    </div>
  );
};

// Chatbot Component (Fixed)
const Chatbot = () => {
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { type: 'bot', text: t('chatbotWelcome') }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { type: 'user', text: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // Call without authentication requirement
      const response = await axios.post(`${API}/chat`, { message: inputMessage });
      const botMessage = { type: 'bot', text: response.data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Erreur chatbot:', error);
      const errorMessage = { 
        type: 'bot', 
        text: t('chatbotTechnicalError') 
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    setLoading(false);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen && (
        <div className="bg-white rounded-lg shadow-2xl w-80 h-96 mb-4 flex flex-col">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 rounded-t-lg">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">🤖 {t('chatbotTitle')}</h3>
              <button onClick={() => setIsOpen(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <p className="text-xs opacity-90 mt-1">{t('chatbotSupport')}</p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs px-3 py-2 rounded-lg ${
                  message.type === 'user' 
                    ? 'bg-purple-600 text-white ml-4' 
                    : 'bg-white text-gray-800 mr-4 shadow-sm border'
                }`}>
                  {message.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 max-w-xs px-3 py-2 rounded-lg mr-4 shadow-sm border">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="p-4 border-t bg-white rounded-b-lg">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder={t('typeMessage')}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <button
                onClick={sendMessage}
                disabled={loading}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2 rounded-md disabled:opacity-50 transition-all duration-200"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-300 transform hover:scale-110"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>
    </div>
  );
};

// Landing Page Component
// 🚀 Premium Gamified Demo Component
const PremiumDemo = () => {
  const navigate = useNavigate();
  const [demoStage, setDemoStage] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const { currentLanguage } = useLanguage();

  const chapters = [
    {
      id: 1,
      title: "Chapitre 1 - Recherche et Publication automatique des SEO",
      icon: "🤖",
      description: "L'IA scanne le web, analyse les SEO, applique les optimisations et publie automatiquement",
      color: "from-cyan-500 to-blue-500"
    },
    {
      id: 2,
      title: "Chapitre 2 - Génération IA",
      icon: "✨",
      description: "Création automatique de fiches produits avec descriptions SEO optimisées",
      color: "from-purple-500 to-pink-500"
    },
    {
      id: 3,
      title: "Chapitre 3 - Publication Multi-Plateformes",
      icon: "🌐",
      description: "Publication simultanée sur Shopify, Amazon, eBay et autres marketplaces",
      color: "from-green-500 to-emerald-500"
    },
    {
      id: 4,
      title: "Chapitre 4 - Programme d'Affiliation",
      icon: "💰",
      description: "Système de commission et tracking avancé pour maximiser vos revenus",
      color: "from-orange-500 to-red-500"
    },
    {
      id: 5,
      title: "Chapitre 5 - Analytics HUD",
      icon: "📊",
      description: "Dashboard temps réel style gaming avec métriques et performances",
      color: "from-indigo-500 to-purple-500"
    }
  ];

  const currentChapter = chapters[demoStage - 1];

  // Auto-play functionality
  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setDemoStage(prev => {
          if (prev >= 5) {
            setIsPlaying(false);
            return 1;
          }
          return prev + 1;
        });
      }, 8000); // 8 seconds per chapter

      return () => clearInterval(interval);
    }
  }, [isPlaying]);

  const renderChapterContent = () => {
    switch(demoStage) {
      case 1:
        return (
          <div className="text-center">
            <div className="text-6xl mb-6 animate-bounce">{currentChapter.icon}</div>
            <h2 className="text-3xl font-bold mb-4">{currentChapter.title}</h2>
            <p className="text-gray-300 text-lg mb-8">{currentChapter.description}</p>
            
            {/* Premium AI Workflow Animation */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-8 max-w-4xl mx-auto shadow-2xl border border-gray-700">
              {/* Animation Timeline */}
              <div className="relative">
                {/* Flow Steps */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  {/* Step 1: Web Scan */}
                  <div className="flex flex-col items-center relative">
                    <div className="w-20 h-20 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center mb-4 animate-pulse shadow-lg shadow-cyan-500/25">
                      <svg className="w-10 h-10 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <h4 className="text-sm font-semibold text-cyan-300 mb-2">Scan du Web</h4>
                    <div className="text-xs text-gray-400 text-center">
                      <div className="animate-pulse delay-100">🌐 Analyse des tendances</div>
                      <div className="animate-pulse delay-200">📊 Collecte de données</div>
                    </div>
                    {/* Connecting Line */}
                    <div className="hidden md:block absolute top-10 left-full w-6 h-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 animate-pulse"></div>
                  </div>

                  {/* Step 2: SEO Analysis */}
                  <div className="flex flex-col items-center relative">
                    <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mb-4 animate-pulse delay-300 shadow-lg shadow-purple-500/25">
                      <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">Analyse SEO</h4>
                    <div className="text-xs text-gray-400 text-center">
                      <div className="animate-pulse delay-400">🎯 Mots-clés</div>
                      <div className="animate-pulse delay-500">📈 Optimisations</div>
                    </div>
                    {/* Connecting Line */}
                    <div className="hidden md:block absolute top-10 left-full w-6 h-0.5 bg-gradient-to-r from-purple-500 to-green-500 animate-pulse delay-300"></div>
                  </div>

                  {/* Step 3: Apply Optimizations */}
                  <div className="flex flex-col items-center relative">
                    <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mb-4 animate-pulse delay-600 shadow-lg shadow-green-500/25">
                      <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h4 className="text-sm font-semibold text-green-300 mb-2">Optimisation</h4>
                    <div className="text-xs text-gray-400 text-center">
                      <div className="animate-pulse delay-700">⚡ +Score SEO</div>
                      <div className="animate-pulse delay-800">🚀 Performance</div>
                    </div>
                    {/* Connecting Line */}
                    <div className="hidden md:block absolute top-10 left-full w-6 h-0.5 bg-gradient-to-r from-green-500 to-orange-500 animate-pulse delay-600"></div>
                  </div>

                  {/* Step 4: Auto Publication */}
                  <div className="flex flex-col items-center">
                    <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center mb-4 animate-pulse delay-900 shadow-lg shadow-orange-500/25">
                      <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                      </svg>
                    </div>
                    <h4 className="text-sm font-semibold text-orange-300 mb-2">Publication</h4>
                    <div className="text-xs text-gray-400 text-center">
                      <div className="animate-pulse delay-1000">🛒 Shopify ✓</div>
                      <div className="animate-pulse delay-1100">🏪 Amazon ✓</div>
                    </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 p-4 rounded-lg border border-cyan-500/20">
                    <div className="text-2xl font-bold text-cyan-400 animate-pulse">98%</div>
                    <div className="text-xs text-gray-400">Score SEO moyen</div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 p-4 rounded-lg border border-purple-500/20">
                    <div className="text-2xl font-bold text-purple-400 animate-pulse">2.4s</div>
                    <div className="text-xs text-gray-400">Temps de traitement</div>
                  </div>
                  <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 p-4 rounded-lg border border-green-500/20">
                    <div className="text-2xl font-bold text-green-400 animate-pulse">15+</div>
                    <div className="text-xs text-gray-400">Plateformes supportées</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="text-center">
            <div className="text-6xl mb-6 animate-pulse">{currentChapter.icon}</div>
            <h2 className="text-3xl font-bold mb-4">{currentChapter.title}</h2>
            <p className="text-gray-300 text-lg mb-8">{currentChapter.description}</p>
            
            {/* AI Generation Animation */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 max-w-2xl mx-auto">
              <div className="mb-6">
                <div className="text-left space-y-3">
                  <div className="bg-blue-900/30 p-3 rounded border-l-4 border-blue-400 animate-fadeInUp">
                    <strong className="text-blue-400">Titre généré:</strong>
                    <p className="text-white mt-1">"iPhone 15 Pro Max - Smartphone Premium 256GB Titanium"</p>
                  </div>
                  <div className="bg-green-900/30 p-3 rounded border-l-4 border-green-400 animate-fadeInUp delay-300">
                    <strong className="text-green-400">Description SEO:</strong>
                    <p className="text-white mt-1">Découvrez l'iPhone 15 Pro Max, le smartphone le plus avancé d'Apple avec processeur A17 Pro, système photo professionnel...</p>
                  </div>
                  <div className="bg-purple-900/30 p-3 rounded border-l-4 border-purple-400 animate-fadeInUp delay-500">
                    <strong className="text-purple-400">Tags SEO:</strong>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {['smartphone', 'iPhone', 'Apple', 'premium', 'titanium'].map((tag, i) => (
                        <span key={i} className="px-2 py-1 bg-purple-600 rounded text-xs">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="text-center">
            <div className="text-6xl mb-6 animate-spin-slow">{currentChapter.icon}</div>
            <h2 className="text-3xl font-bold mb-4">{currentChapter.title}</h2>
            <p className="text-gray-300 text-lg mb-8">{currentChapter.description}</p>
            
            {/* Multi-Platform Publication */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 max-w-4xl mx-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { name: 'Shopify', icon: '🛍️', status: 'published', delay: 0 },
                  { name: 'Amazon', icon: '📦', status: 'publishing', delay: 200 },
                  { name: 'eBay', icon: '🔨', status: 'queued', delay: 400 },
                  { name: 'Etsy', icon: '🎨', status: 'queued', delay: 600 }
                ].map((platform, index) => (
                  <div key={platform.name} className={`p-4 rounded-lg animate-fadeInUp bg-gray-800/50 border border-gray-700`} 
                       style={{animationDelay: `${platform.delay}ms`}}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{platform.icon}</span>
                        <span className="text-white font-semibold">{platform.name}</span>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                        platform.status === 'published' ? 'bg-green-600 text-white' :
                        platform.status === 'publishing' ? 'bg-yellow-600 text-white animate-pulse' :
                        'bg-gray-600 text-gray-300'
                      }`}>
                        {platform.status === 'published' ? '✅ Publié' :
                         platform.status === 'publishing' ? '⏳ En cours...' : '⏸️ En attente'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="text-center">
            <div className="text-6xl mb-6 animate-bounce">{currentChapter.icon}</div>
            <h2 className="text-3xl font-bold mb-4">{currentChapter.title}</h2>
            <p className="text-gray-300 text-lg mb-8">{currentChapter.description}</p>
            
            {/* Affiliate Dashboard */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 max-w-2xl mx-auto">
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gradient-to-br from-green-600 to-emerald-600 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-white">€2,847</div>
                  <div className="text-green-100 text-sm">Revenus ce mois</div>
                </div>
                <div className="bg-gradient-to-br from-blue-600 to-cyan-600 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-white">147</div>
                  <div className="text-blue-100 text-sm">Ventes générées</div>
                </div>
                <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-white">15%</div>
                  <div className="text-purple-100 text-sm">Taux commission</div>
                </div>
              </div>
              
              {/* Live activity */}
              <div className="space-y-2">
                <div className="flex items-center justify-between bg-green-900/30 p-2 rounded">
                  <span className="text-green-400">🎉 Nouvelle vente: €29 commission</span>
                  <span className="text-gray-400 text-xs">Il y a 2min</span>
                </div>
                <div className="flex items-center justify-between bg-blue-900/30 p-2 rounded">
                  <span className="text-blue-400">👥 Nouveau référé inscrit</span>
                  <span className="text-gray-400 text-xs">Il y a 5min</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="text-center">
            <div className="text-6xl mb-6 animate-pulse">{currentChapter.icon}</div>
            <h2 className="text-3xl font-bold mb-4">{currentChapter.title}</h2>
            <p className="text-gray-300 text-lg mb-8">{currentChapter.description}</p>
            
            {/* Gaming-style HUD */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 max-w-2xl mx-auto">
              {/* Top metrics bar */}
              <div className="grid grid-cols-4 gap-2 mb-6">
                {[
                  { label: 'XP', value: '8,547', color: 'text-yellow-400' },
                  { label: 'LVL', value: '23', color: 'text-green-400' },
                  { label: 'COMBO', value: 'x12', color: 'text-red-400' },
                  { label: 'RANK', value: '#1', color: 'text-purple-400' }
                ].map((stat, i) => (
                  <div key={i} className="bg-black/50 p-2 rounded border border-gray-700">
                    <div className="text-xs text-gray-400">{stat.label}</div>
                    <div className={`font-bold ${stat.color}`}>{stat.value}</div>
                  </div>
                ))}
              </div>
              
              {/* Health/Progress bars */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-green-400">VENTES</span>
                    <span className="text-white">847/1000</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-green-500 to-green-400 h-2 rounded-full" style={{width: '84.7%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-blue-400">ENGAGEMENT</span>
                    <span className="text-white">92%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-blue-500 to-blue-400 h-2 rounded-full" style={{width: '92%'}}></div>
                  </div>
                </div>
              </div>
              
              {/* Live stats */}
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div className="text-green-400 animate-pulse">💹 +€127 (dernière heure)</div>
                <div className="text-blue-400 animate-pulse">👥 +23 visiteurs actifs</div>
              </div>
            </div>
          </div>
        );

      default:
        return <div>Chapitre non trouvé</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 text-white relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-500/10 rounded-full blur-2xl"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 p-8">
        <div className="flex items-center justify-between">
          <button 
            onClick={() => {
              // Navigate to home and force landing page view
              navigate('/', { state: { forceHome: true } });
            }}
            className="flex items-center space-x-2 px-6 py-3 bg-white/10 backdrop-blur-md rounded-full border border-white/20 hover:bg-white/20 transition-all duration-300"
          >
            <span>←</span>
            <span>Retour à l'accueil</span>
          </button>
          
          <div className="text-center">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-300 via-purple-300 to-pink-300 bg-clip-text text-transparent">
              🚀 Démo Premium ECOMSIMPLY
            </h1>
            <p className="text-gray-300 mt-2">
              Découvrez l'IA e-commerce en action
            </p>
          </div>
          
          <div className="text-sm text-gray-400">
            Étape {demoStage}/5
          </div>
        </div>
      </div>

      {/* Chapter Navigation Tabs */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 mb-8">
        {/* Mobile: scroll container with start alignment, Desktop: centered */}
        <div className="flex justify-start md:justify-center space-x-2 overflow-x-auto pb-2 scrollbar-hide">
          {chapters.map((chapter) => (
            <button
              key={chapter.id}
              onClick={() => setDemoStage(chapter.id)}
              className={`flex items-center space-x-2 px-3 py-2 md:px-4 md:py-3 rounded-full border transition-all duration-300 whitespace-nowrap flex-shrink-0 ${
                demoStage === chapter.id
                  ? 'bg-gradient-to-r ' + chapter.color + ' text-white border-transparent shadow-lg scale-105'
                  : 'bg-white/10 text-gray-300 border-white/20 hover:bg-white/20 hover:scale-105'
              }`}
            >
              <span className="text-lg">{chapter.icon}</span>
              <span className="font-semibold text-xs md:text-sm">Chapitre {chapter.id}</span>
            </button>
          ))}
        </div>
        {/* Scroll indicator for mobile */}
        <div className="flex justify-center mt-2">
          <div className="text-xs text-gray-500 block md:hidden">← Faites défiler pour voir tous les chapitres →</div>
        </div>
      </div>

      {/* Demo Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-8 py-12">
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8 shadow-2xl">
          {renderChapterContent()}
          
          {/* Navigation Controls */}
          <div className="flex items-center justify-center space-x-4 mt-12">
            <button 
              onClick={() => setDemoStage(Math.max(1, demoStage - 1))}
              disabled={demoStage === 1}
              className="px-6 py-3 bg-gray-700 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
            >
              ← Précédent
            </button>
            
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`px-8 py-3 rounded-full transition-all transform hover:scale-105 ${
                isPlaying 
                  ? 'bg-gradient-to-r from-red-600 to-red-700 text-white' 
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700'
              }`}
            >
              {isPlaying ? '⏸️ Pause' : '▶️ Auto-Play'}
            </button>
            
            <button 
              onClick={() => setDemoStage(Math.min(5, demoStage + 1))}
              disabled={demoStage === 5}
              className="px-6 py-3 bg-gray-700 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
            >
              Suivant →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Landing Page Component (SIMPLIFIÉ - CTA DIRECT STRIPE)
const LandingPage = ({ 
  onShowAffiliateLogin, 
  showUserNavigation = false, 
  affiliateConfig = null,
  onDirectPremiumCheckout  // CTA DIRECT VERS STRIPE CHECKOUT
}) => {
  const { login, register, user } = useAuth();
  const { t, currentLanguage } = useLanguage();
  
  // Debug: Check if prop is defined
  console.log('🔍 LandingPage props:', { 
    onDirectPremiumCheckout: typeof onDirectPremiumCheckout
  });
  
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showHelpPage, setShowHelpPage] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [activeModalTab, setActiveModalTab] = useState('login'); // 'login' or 'register'
  
  // Expose login functions globally for trial flow
  useEffect(() => {
    window.setShowLoginModal = (show) => {
      console.log('🎯 Global setShowLoginModal called with:', show);
      setShowLogin(show);
    };
    
    window.setShowRegisterModal = (show) => {
      console.log('🎯 Global setShowRegisterModal called with:', show);
      if (show) {
        setActiveModalTab('register');
        setShowLogin(true);
      } else {
        setShowLogin(false);
      }
    };
    
    // Listen for custom login events
    const handleOpenLogin = () => {
      console.log('🎯 Custom login event received');
      setShowLogin(true);
    };
    
    window.addEventListener('openLogin', handleOpenLogin);
    
    return () => {
      delete window.setShowLoginModal;
      delete window.setShowRegisterModal;
      window.removeEventListener('openLogin', handleOpenLogin);
    };
  }, []);
  
  // Affiliate States
  const [showAffiliateModal, setShowAffiliateModal] = useState(false);
  const [affiliateForm, setAffiliateForm] = useState({
    email: '',
    name: '',
    company: '',
    website: '',
    social_media: {
      twitter: '',
      instagram: '',
      youtube: '',
      tiktok: ''
    },
    payment_method: 'bank_transfer',
    payment_details: {
      bank_name: '',
      iban: '',
      bic: ''
    },
    motivation: ''
  });
  const [affiliateLoading, setAffiliateLoading] = useState(false);
  const [affiliateSuccess, setAffiliateSuccess] = useState(false);
  const [registerForm, setRegisterForm] = useState({ name: '', email: '', password: '' });
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [showTestimonialForm, setShowTestimonialForm] = useState(false);
  const [testimonialForm, setTestimonialForm] = useState({
    name: '',
    title: '',
    rating: 5,
    comment: ''
  });

  // Function to get highest affiliate commission rate
  const getHighestCommissionRate = () => {
    if (!affiliateConfig) return 15; // Default fallback
    
    const proRate = affiliateConfig.default_commission_rate_pro || 10;
    const premiumRate = affiliateConfig.default_commission_rate_premium || 15;
    
    // If rates are equal, return Premium rate. Otherwise return the highest.
    if (proRate === premiumRate) {
      return premiumRate;
    }
    return Math.max(proRate, premiumRate);
  };
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Clear trial errors for non-authenticated users
  useEffect(() => {
    const token = localStorage.getItem('token');
    const currentUser = localStorage.getItem('currentUser');
    
    // If user is not authenticated, clear any trial-related errors
    if (!token || !currentUser) {
      setError(''); // Clear any existing error messages for non-auth users
      console.log('🔧 Non-authenticated user - clearing any trial errors');
    }
  }, []);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  
  // États pour le popup de choix connexion/création
  const [showPlanChoiceModal, setShowPlanChoiceModal] = useState(false);
  const [selectedPlanForChoice, setSelectedPlanForChoice] = useState(null);
  
  const [dynamicTestimonials, setDynamicTestimonials] = useState([]);
  const [loadingTestimonials, setLoadingTestimonials] = useState(true);
  const [publicStats, setPublicStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const [realSalesAnalytics, setRealSalesAnalytics] = useState({
    total_sales: 0,
    total_revenue: 0.0,
    conversion_rate: 0.0,
    sales_this_month: 0,
    revenue_this_month: 0.0,
    sales_this_week: 0,
    revenue_this_week: 0.0,
    platform_breakdown: {},
    last_updated: new Date()
  });
  const [loadingSalesAnalytics, setLoadingSalesAnalytics] = useState(false);
  
  // Dynamic pricing states
  const [dynamicPricing, setDynamicPricing] = useState({
    gratuit: { price: 0, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null },
    pro: { price: 29, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null },
    premium: { price: 99, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null }
  });
  const [loadingPricing, setLoadingPricing] = useState(false);

  // Sales Analytics Functions
  const loadRealSalesAnalytics = async () => {
    setLoadingSalesAnalytics(true);
    try {
      const response = await axios.get(`${API}/analytics/sales`);
      if (response.data.success) {
        setRealSalesAnalytics(response.data.metrics);
      }
    } catch (error) {
      console.error('Error loading sales analytics:', error);
      // Keep default values if error (already set in initial state)
    }
    setLoadingSalesAnalytics(false);
  };
  
  // Dynamic Pricing Functions avec système de retry et endpoints alternatifs
  const loadDynamicPricing = async () => {
    setLoadingPricing(true);
    
    // Liste des endpoints à essayer en cas d'erreur 404
    const endpoints = [
      `${API}/public/plans-pricing`,
      `${API}/public/plans-pricing-nocache`,
      `${API}/plans-pricing-alt`
    ];
    
    for (let i = 0; i < endpoints.length; i++) {
      try {
        console.log(`🔄 Tentative ${i + 1}/${endpoints.length}: ${endpoints[i]}`);
        
        const response = await axios.get(endpoints[i], {
          // Headers pour éviter le cache
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          },
          // Timeout de 10 secondes
          timeout: 10000
        });
        
        if (response.data.success && response.data.plans) {
          const plans = response.data.plans;
          const newPricing = {
            // Garder les valeurs par défaut
            gratuit: { price: 0, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null },
            pro: { price: 29, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null },
            premium: { price: 99, original_price: null, promotion_active: false, promotion_badge: null, promotional_text: null }
          };
          
          // Mettre à jour avec les données de l'API si disponibles
          plans.forEach(plan => {
            if (newPricing[plan.plan_name]) {
              newPricing[plan.plan_name] = {
                price: plan.price,
                original_price: plan.original_price,
                promotion_active: plan.promotion_active || false,
                promotion_badge: plan.promotion_badge || null,
                promotional_text: plan.promotional_text || null
              };
            }
          });
          
          setDynamicPricing(newPricing);
          console.log(`✅ Dynamic pricing loaded from ${endpoints[i]}:`, newPricing);
          setLoadingPricing(false);
          return; // Succès, on sort de la boucle
        }
      } catch (error) {
        console.error(`❌ Erreur endpoint ${i + 1}/${endpoints.length} (${endpoints[i]}):`, error.response?.status, error.message);
        
        // Si c'est le dernier endpoint et qu'il échoue aussi, on continue avec les valeurs par défaut
        if (i === endpoints.length - 1) {
          console.log('⚠️  Tous les endpoints ont échoué, utilisation des prix par défaut');
          // Les valeurs par défaut sont déjà définies dans l'état initial
        }
      }
    }
    
    setLoadingPricing(false);
  };
  
  // Customer reviews data (fallback si pas de témoignages dynamiques)
  const staticReviews = [
    {
      id: 1,
      rating: 5,
      name: "Fatou D.",
      title: "Fondatrice de BeautyZone Paris",
      comment: "ECOMSIMPLY m'a permis de générer des fiches produits en quelques clics, bien plus pro que celles que je rédigeais à la main. L'IA comprend parfaitement mes produits cosmétiques. Un vrai gain de temps.",
      avatar: "F"
    },
    {
      id: 2,
      rating: 5,
      name: "Yann B.",
      title: "Gérant de TechNomad Store",
      comment: "Je vends des gadgets tech sur Shopify, et j'avais toujours du mal avec les descriptions. Avec ECOMSIMPLY, j'ai généré 80 fiches en une après-midi, prêtes à être mises en ligne. Incroyable.",
      avatar: "Y"
    },
    {
      id: 3,
      rating: 4,
      name: "Salimata K.",
      title: "CEO de DressMe Africa",
      comment: "J'adore l'interface. Simple, rapide, efficace. L'export en CSV fonctionne super bien avec ma boutique WooCommerce. Seul point à améliorer : j'aimerais pouvoir générer des fiches en plusieurs langues.",
      avatar: "S"
    },
    {
      id: 4,
      rating: 5,
      name: "Hugo M.",
      title: "Revendeur sur Maison du Sport",
      comment: "Je suis bluffé par la qualité des fiches générées. Même mes fournisseurs m'ont demandé avec quel outil je travaillais. L'option 'description + bullet points' est top.",
      avatar: "H"
    },
    {
      id: 5,
      rating: 5,
      name: "Léa P.",
      title: "Dropshippeuse sur NovaStyle Shop",
      comment: "Parfait pour les débutants ! J'ai lancé ma boutique il y a un mois, et ECOMSIMPLY m'a littéralement sauvé la vie. Tout est optimisé, je gagne un temps fou. Je recommande à 100 %.",
      avatar: "L"
    }
  ];

  // Charger les témoignages dynamiques depuis l'API avec rafraîchissement automatique et retry sur 502
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fonction utilitaire pour retry automatique en cas d'erreur 502 avec endpoints alternatifs
        const fetchWithRetry = async (endpoint, maxRetries = 3) => {
          // Liste des endpoints à essayer (principal + alternatifs)
          const endpointVariants = {
            'testimonials': [`${API}/testimonials`, `${API}/testimonials-alt`],
            'stats': [`${API}/stats/public`, `${API}/stats/public-alt`]
          };
          
          const urls = endpointVariants[endpoint] || [`${API}/${endpoint}`];
          
          for (let urlIndex = 0; urlIndex < urls.length; urlIndex++) {
            const url = urls[urlIndex];
            
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
              try {
                console.log(`🔄 ${endpoint} - URL ${urlIndex + 1}/${urls.length}, tentative ${attempt}/${maxRetries}: ${url}`);
                
                const response = await axios.get(url, {
                  timeout: 15000, // Timeout de 15 secondes
                  headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                  }
                });
                
                console.log(`✅ Succès ${endpoint} via ${url} (tentative ${attempt})`);
                return response;
                
              } catch (error) {
                const statusCode = error.response?.status;
                const isServerError = statusCode >= 500 && statusCode <= 599;
                
                console.error(`❌ Échec ${endpoint} (${url}), tentative ${attempt}/${maxRetries}:`, statusCode, error.message);
                
                // Si c'est une erreur serveur (5xx) et qu'il reste des tentatives sur cette URL
                if (isServerError && attempt < maxRetries) {
                  console.log(`⏳ Retry dans ${1000 * attempt}ms...`);
                  await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                  continue;
                }
                
                // Si toutes les tentatives sur cette URL ont échoué, essayer l'URL suivante
                if (urlIndex < urls.length - 1) {
                  console.log(`🔄 Basculement vers l'endpoint alternatif ${urlIndex + 2}/${urls.length}`);
                  break; // Sort de la boucle des attempts pour essayer l'URL suivante
                }
                
                // Dernière URL et dernière tentative
                throw error;
              }
            }
          }
        };
        
        // Charger les témoignages, statistiques et prix en parallèle avec retry intelligent
        console.log('🔄 Chargement des données avec retry automatique et endpoints alternatifs...');
        console.log('🔍 DEBUG: API =', API);
        console.log('🔍 DEBUG: BACKEND_URL =', BACKEND_URL);
        
        const requests = [
          fetchWithRetry('testimonials'),
          fetchWithRetry('stats')
        ];
        
        const [testimonialsResponse, statsResponse] = await Promise.allSettled(requests);
        
        // Traiter les témoignages
        if (testimonialsResponse.status === 'fulfilled') {
          try {
            if (testimonialsResponse.value && testimonialsResponse.value.testimonials) {
              setDynamicTestimonials(testimonialsResponse.value.testimonials);
              console.log('✅ Témoignages chargés:', testimonialsResponse.value.testimonials.length);
            } else {
              console.log('⚠️ Format de réponse inattendu, utilisation des témoignages statiques');
              setDynamicTestimonials([]); // Force l'utilisation des statiques
            }
          } catch (e) {
            console.log('⚠️ Erreur parsing témoignages, utilisation des témoignages statiques');
            setDynamicTestimonials([]);
          }
        } else {
          console.log('⚠️ Utilisation des témoignages statiques (erreur API)', testimonialsResponse);
          setDynamicTestimonials([]); // Utilise les témoignages statiques définis plus bas
        }
        
        // Traiter les statistiques
        if (statsResponse.status === 'fulfilled' && statsResponse.value.stats) {
          setPublicStats(statsResponse.value.stats);
          console.log('✅ Statistiques chargées');
        } else {
          console.log('⚠️  Utilisation des statistiques par défaut (erreur API)', statsResponse);
          // Les statistiques par défaut sont définies dans l'état initial
        }
        
      } catch (error) {
        console.error('❌ Erreur chargement données (toutes les tentatives échouées):', error);
        console.log('⚠️  Utilisation des données statiques par défaut');
        // En cas d'erreur totale, on utilise les données statiques/par défaut
      } finally {
        setLoadingTestimonials(false);
        setLoadingStats(false);
      }
    };

    // Charger les données immédiatement
    fetchData();
    loadDynamicPricing(); // Charger les prix dynamiques
    
    // Puis rafraîchir automatiquement toutes les 30 secondes pour un suivi dynamique
    const interval = setInterval(() => {
      fetchData();
      loadDynamicPricing(); // Rafraîchir aussi les prix
    }, 30000); // 30 secondes

    // Nettoyer l'intervalle quand le composant est démonté
    return () => clearInterval(interval);
  }, []);

  // Fonction utilitaire pour générer la description des résultats garantis
  const getGuaranteedDescription = () => {
    if (loadingStats) {
      return t('loading') + '...';
    }
    
    const totalSheets = (publicStats?.total_product_sheets || 10000).toLocaleString('fr-FR');
    const satisfactionRate = publicStats?.satisfaction_rate || 98;
    
    // Utiliser la langue actuelle via le contexte
    return currentLanguage === 'fr'
      ? `Plus de ${totalSheets} fiches produits générées avec un taux de satisfaction client de ${satisfactionRate}%.`
      : `Over ${totalSheets.replace(/\s/g, ',')} product sheets generated with ${satisfactionRate}% customer satisfaction rate.`;
  };

  // Fonction utilitaire pour le temps de génération
  const getGenerationTime = () => {
    if (loadingStats) return '...';
    
    const avgTime = publicStats?.avg_generation_time || 28;
    return currentLanguage === 'fr'
      ? `${avgTime} secondes`
      : `${avgTime} seconds`;
  };

  // Fonction utilitaire pour le nombre d'e-commerçants
  const getEcommerceTrustText = () => {
    if (loadingStats) {
      return currentLanguage === 'fr'
        ? 'Chargement...'
        : 'Loading...';
    }
    
    const totalUsers = publicStats?.satisfied_clients || 10000;
    
    return currentLanguage === 'fr'
      ? `Rejoignez plus de ${totalUsers.toLocaleString('fr-FR')} e-commerçants qui utilisent ECOMSIMPLY pour optimiser leurs ventes`
      : `Join over ${totalUsers.toLocaleString('en-US')} e-merchants who use ECOMSIMPLY to optimize their sales`;
  };

  // Utiliser les témoignages dynamiques s'ils sont disponibles, sinon fallback sur les statiques
  const customerReviews = dynamicTestimonials.length > 0 ? dynamicTestimonials : staticReviews;

  // Show only first 5 reviews or all based on state
  const displayedReviews = showAllReviews ? customerReviews : customerReviews.slice(0, 5);

  const submitTestimonial = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await axios.post(`${API}/testimonials`, {
        name: testimonialForm.name,
        title: testimonialForm.title,
        rating: testimonialForm.rating,
        comment: testimonialForm.comment
      });
      
      if (response.status === 200) {
        alert('Merci pour votre témoignage ! Il sera examiné et publié prochainement.');
        setTestimonialForm({ name: '', title: '', rating: 5, comment: '' });
        setShowTestimonialForm(false);
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du témoignage:', error);
      alert('Erreur lors de l\'envoi du témoignage. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  // Affiliate Functions
  const handleAffiliateRegistration = async (e) => {
    e.preventDefault();
    setAffiliateLoading(true);
    
    try {
      const response = await axios.post(`${API}/affiliate/register`, affiliateForm);
      
      if (response.data.success) {
        setAffiliateSuccess(true);
        alert(`🎉 Inscription réussie ! Votre code d'affiliation est : ${response.data.affiliate_code}\n\nVotre demande sera examinée sous 24-48h. Vous recevrez un email de confirmation.`);
        setShowAffiliateModal(false);
        // Reset form
        setAffiliateForm({
          email: '',
          name: '',
          company: '',
          website: '',
          social_media: { twitter: '', instagram: '', youtube: '', tiktok: '' },
          payment_method: 'bank_transfer',
          payment_details: { bank_name: '', iban: '', bic: '' },
          motivation: ''
        });
      }
    } catch (error) {
      console.error('Erreur inscription affilié:', error);
      if (error.response?.status === 400) {
        alert('❌ Cette adresse email est déjà utilisée pour un compte affilié.');
      } else {
        alert('❌ Erreur lors de l\'inscription. Veuillez réessayer.');
      }
    } finally {
      setAffiliateLoading(false);
    }
  };
  
  const updateAffiliateForm = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setAffiliateForm(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setAffiliateForm(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };
  const [selectedPlan, setSelectedPlan] = useState('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedUpgradePlan, setSelectedUpgradePlan] = useState('');
  const [showUpgradeSuccess, setShowUpgradeSuccess] = useState(false);
  const [showDashboardHelp, setShowDashboardHelp] = useState(false);
  
  // Enhanced Plan Selection States
  const [showPlanRegistration, setShowPlanRegistration] = useState(false);
  const [selectedPlanForRegistration, setSelectedPlanForRegistration] = useState(null);
  const [planRegistrationData, setPlanRegistrationData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [planRegistrationLoading, setPlanRegistrationLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const result = await login(loginForm.email, loginForm.password);
    if (!result.success) {
      setError(result.error);
    } else {
      // Close login modal on successful login
      setShowLogin(false);
      setActiveModalTab('login'); // Reset tab to login for next time
      setLoginForm({ email: '', password: '' });
      
      // Check for post-login actions (trial flow)
      setTimeout(() => {
        const postLoginAction = localStorage.getItem('postLoginAction');
        if (postLoginAction) {
          try {
            const action = JSON.parse(postLoginAction);
            console.log('🎯 Executing post-login action after successful login:', action);
            
            if (action.action === 'startTrial') {
              console.log('✅ Starting trial subscription after login');
              localStorage.removeItem('postLoginAction'); // Clean up
              
              if (action.useTrialFunction && window.handleTrialSubscription) {
                // Use the trial function
                window.handleTrialSubscription(action.plan);
              } else if (action.redirectTo) {
                // Use redirect method
                window.location.href = action.redirectTo;
              } else {
                // Fallback
                window.location.href = `/payment?plan=${action.plan}&trial=true`;
              }
            }
          } catch (error) {
            console.error('Error handling post-login action:', error);
            localStorage.removeItem('postLoginAction');
          }
        }
      }, 500); // Small delay to ensure login state is updated
    }
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const result = await register(
      registerForm.name, 
      registerForm.email, 
      registerForm.password
    );
    
    if (!result.success) {
      setError(result.error);
    } else {
      // Close registration modal on successful registration
      setShowLogin(false); // Close the unified modal
      setActiveModalTab('login'); // Reset tab to login for next time
      setRegisterForm({ name: '', email: '', password: '' });
      
      // Show trial success message if applicable
      if (result.trialInfo) {
        console.log('Trial registration successful:', result);
      }
      
      // Check for post-login actions (trial flow)
      setTimeout(() => {
        const postLoginAction = localStorage.getItem('postLoginAction');
        if (postLoginAction) {
          try {
            const action = JSON.parse(postLoginAction);
            console.log('🎯 Executing post-registration action:', action);
            
            if (action.action === 'startTrial') {
              console.log('✅ Starting trial subscription after registration');
              localStorage.removeItem('postLoginAction'); // Clean up
              
              if (action.useTrialFunction && window.handleTrialSubscription) {
                // Use the trial function
                window.handleTrialSubscription(action.plan);
              } else if (action.redirectTo) {
                // Use redirect method
                window.location.href = action.redirectTo;
              } else {
                // Fallback
                window.location.href = `/payment?plan=${action.plan}&trial=true`;
              }
            }
          } catch (error) {
            console.error('Error handling post-registration action:', error);
            localStorage.removeItem('postLoginAction');
          }
        }
      }, 500); // Small delay to ensure registration state is updated
    }
    setLoading(false);
  };

  const changePasswordLanding = async (e) => {
    e.preventDefault();
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('Les nouveaux mots de passe ne correspondent pas');
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      setError('Le nouveau mot de passe doit contenir au moins 6 caractères');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });
      
      setShowPasswordModal(false);
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      setError('');
      alert('Mot de passe modifié avec succès !');
      
    } catch (error) {
      console.error('Erreur changement mot de passe:', error);
      setError(error.response?.data?.detail || 'Erreur lors du changement de mot de passe');
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/reset-password`, {
        email: resetEmail
      });
      
      setShowResetModal(false);
      setResetEmail('');
      setError('');
      alert('Un email de réinitialisation a été envoyé à votre adresse email !');
      
    } catch (error) {
      console.error('Erreur réinitialisation mot de passe:', error);
      setError(error.response?.data?.detail || 'Erreur lors de l\'envoi de l\'email de réinitialisation');
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSelection = (plan) => {
    // Check if user is logged in
    if (!user) {
      // Afficher le popup de choix au lieu d'ouvrir directement le modal de création
      setSelectedPlanForChoice(plan);
      setShowPlanChoiceModal(true);
      return;
    }

    setSelectedPlan(plan);
    setShowPlanModal(true);
  };

  // Fonctions pour gérer le popup de choix
  const closePlanChoiceModal = () => {
    setShowPlanChoiceModal(false);
    setSelectedPlanForChoice(null);
  };

  const handleChoiceLogin = () => {
    // Fermer le popup de choix et ouvrir le modal de connexion
    closePlanChoiceModal();
    setShowLogin(true);
  };

  const handleChoiceRegister = () => {
    // Fermer le popup de choix et ouvrir le modal de création de compte
    closePlanChoiceModal();
    setSelectedPlanForRegistration(selectedPlanForChoice);
    setShowPlanRegistration(true);
  };

  const handlePlanRegistration = async (e) => {
    e.preventDefault();
    
    if (planRegistrationData.password !== planRegistrationData.confirmPassword) {
      alert('Les mots de passe ne correspondent pas');
      return;
    }

    setPlanRegistrationLoading(true);
    
    try {
      // Register the user
      const registerResult = await register(
        planRegistrationData.name,
        planRegistrationData.email,
        planRegistrationData.password
      );

      if (registerResult.success) {
        // Close registration modal
        setShowPlanRegistration(false);
        
        // Show success message
        alert(`Compte créé avec succès ! Redirection vers le paiement ${selectedPlanForRegistration}...`);
        
        // Wait a moment for user to see the success message
        setTimeout(() => {
          // Proceed directly to payment for the selected plan
          handleUpgrade(selectedPlanForRegistration);
        }, 1000);
        
      } else {
        alert(registerResult.message || 'Erreur lors de la création du compte');
      }
    } catch (error) {
      console.error('Erreur lors de la création du compte:', error);
      alert('Erreur lors de la création du compte. Veuillez réessayer.');
    }
    
    setPlanRegistrationLoading(false);
  };

  const resetPlanRegistration = () => {
    setShowPlanRegistration(false);
    setSelectedPlanForRegistration(null);
    setPlanRegistrationData({
      name: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
  };

  const handleUpgrade = async (plan) => {
    // ⭐ NOUVEAU : Rediriger vers la modal d'essai gratuit au lieu du paiement direct
    console.log('🎯 handleUpgrade appelé pour plan:', plan);
    
    // Stocker le plan sélectionné pour l'essai
    localStorage.setItem('selectedTrialPlan', plan);
    
    // Ouvrir la modal d'essai gratuit
    if (typeof window.showTrialModal === 'function') {
      console.log('✅ Ouverture modal d\'essai gratuit via handleUpgrade');
      window.showTrialModal();
    } else {
      console.error('❌ showTrialModal function not available');
      // Fallback : essayer de déclencher directement l'essai
      if (typeof window.handleTrialSubscription === 'function') {
        try {
          await window.handleTrialSubscription(plan);
        } catch (error) {
          console.error('❌ Fallback trial subscription failed:', error);
          alert('Erreur lors de l\'ouverture de l\'essai gratuit. Veuillez recharger la page.');
        }
      } else {
        alert('Erreur système : fonctions d\'essai non disponibles. Veuillez recharger la page.');
      }
    }
  };

  // Handle trial subscription with 7-day free trial
  const handleTrialSubscription = async (plan) => {
    console.log('🎯 Starting trial subscription for plan:', plan);
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
      
      console.log('🔍 Debug - Token exists:', !!token);
      console.log('🔍 Debug - Current user:', currentUser);
      console.log('🔍 Debug - User email:', currentUser.email);
      
      if (!token || !currentUser.email) {
        console.log('❌ Authentication failed - redirecting to login');
        // Instead of throwing error, redirect to login
        setError('');
        setLoading(false);
        
        // Store trial plan for after login
        localStorage.setItem('postLoginAction', JSON.stringify({
          action: 'startTrial',
          plan: plan,
          useTrialFunction: true
        }));
        
        // Open login modal
        if (window.setShowLoginModal) {
          window.setShowLoginModal(true);
        }
        return;
      }
      
      console.log('✅ User authenticated - proceeding with trial API call');
      
      // Create Stripe checkout session for trial (with 7-day free trial)
      console.log('🎯 Creating Stripe checkout for trial subscription');
      const checkoutResponse = await axios.post(`${API}/payments/checkout`, {
        plan_type: plan,
        origin_url: window.location.origin,
        trial_subscription: true, // Flag to indicate this is a trial
        affiliate_code: new URLSearchParams(window.location.search).get('ref') || null
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('🔍 Debug - Checkout response:', checkoutResponse);
      
      if (checkoutResponse.data.checkout_url) {
        console.log('✅ Redirecting to Stripe checkout for trial');
        window.location.href = checkoutResponse.data.checkout_url;
      } else {
        throw new Error('URL de checkout trial non reçue');
      }
    } catch (error) {
      console.error('Erreur lors de la création de l\'essai gratuit:', error);
      console.error('🔍 Debug - Error response:', error.response);
      
      // Check if it's a 401 error (authentication issue)
      if (error.response && error.response.status === 401) {
        console.log('🔍 401 error - clearing invalid auth and redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('currentUser');
        setError('');
        setLoading(false);
        
        // Store trial plan for after login
        localStorage.setItem('postLoginAction', JSON.stringify({
          action: 'startTrial',
          plan: plan,
          useTrialFunction: true
        }));
        
        // Open login modal
        if (window.setShowLoginModal) {
          window.setShowLoginModal(true);
        }
        return;
      }
      
      // Check if it's a 400 error (business logic issue like already used trial)
      if (error.response && error.response.status === 400) {
        // Display the exact error message from backend
        const backendMessage = error.response.data.detail || error.response.data.message || 'Erreur lors de l\'initialisation de l\'essai gratuit.';
        console.log('❌ Backend error 400:', backendMessage);
        
        // Show user-friendly message in UI
        if (backendMessage.includes('déjà utilisé')) {
          setError('🚫 Vous avez déjà bénéficié de votre essai gratuit 7 jours. Choisissez un plan payant pour continuer à profiter de nos services premium.');
        } else if (backendMessage.includes('7 jours')) {
          setError('🚫 L\'essai gratuit n\'est disponible que pour les nouveaux utilisateurs (compte créé depuis moins de 7 jours).');
        } else {
          setError(backendMessage);
        }
      }
      // Check if it's a 502 error (infrastructure issue)
      else if (error.response && error.response.status === 502) {
        setError('Problème de connexion temporaire. Veuillez réessayer dans quelques instants.');
      } 
      // Handle network errors or other issues
      else if (!error.response) {
        setError('Problème de connexion. Vérifiez votre connexion internet et réessayez.');
      }
      else {
        // Fallback: try to get message from backend or use generic message
        const backendMessage = error.response?.data?.detail || error.response?.data?.message;
        setError(backendMessage || 'Erreur lors de l\'initialisation de l\'essai gratuit. Veuillez réessayer.');
      }
    }
    
    setLoading(false);
  };

  // Expose trial function globally for modal access
  useEffect(() => {
    window.handleTrialSubscription = handleTrialSubscription;
  }, []);
  

  // Check for payment success/failure on page load
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      // Handle payment success
      checkPaymentStatus(sessionId);
    }
  }, []);

  const checkPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attempts >= maxAttempts) {
      setError('Vérification du paiement expirée. Veuillez vérifier votre email pour confirmation.');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`);
      const paymentData = response.data;
      
      if (paymentData.payment_status === 'paid') {
        // Payment successful
        setShowUpgradeSuccess(true);
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      } else if (paymentData.stripe_status === 'expired') {
        setError('Session de paiement expirée. Veuillez réessayer.');
        return;
      }

      // If payment is still pending, continue polling
      setTimeout(() => checkPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error('Erreur vérification paiement:', error);
      setError('Erreur lors de la vérification du paiement. Veuillez réessayer.');
    }
  };

  // Render Help Page
  if (showHelpPage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Navigation - Header XXL avec logo ULTRA VISIBLE */}
        <nav className="sticky top-0 z-50 h-20 md:h-32 lg:h-44 px-4 md:px-6 bg-white/10 backdrop-blur-md border-b border-white/20">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center h-full gap-4 md:gap-6">
              <div className="flex items-center gap-4 flex-shrink-0">
                <HeaderLogo 
                  onClick={() => setShowHelpPage(false)}
                  className="hover:scale-105 transition-transform duration-300"
                />
                <span className="text-gray-300 hidden md:inline">•</span>  
                <span className="text-sm md:text-lg text-purple-200">📚 Centre d'Aide</span>
              </div>
              <button
                onClick={() => setShowHelpPage(false)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-3 md:px-4 py-2 rounded-lg text-sm md:text-base font-medium transition duration-300 whitespace-nowrap"
              >
                ← Retour
              </button>
            </div>
          </div>
        </nav>

        {/* Help Content */}
        <div className="pt-20 pb-12 px-4">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-6">
                🚀 Guide Complet ECOMSIMPLY
              </h1>
              <p className="text-xl text-gray-300 max-w-3xl mx-auto">
                Découvrez toutes les fonctionnalités de votre plateforme IA pour maximiser vos ventes e-commerce
              </p>
            </div>

            {/* Quick Navigation */}
            <div className="bg-white/5 rounded-2xl p-6 mb-12 border border-white/10">
              <h2 className="text-2xl font-bold text-white mb-6 text-center">🧭 Navigation Rapide</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <a href="#getting-started" className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-lg p-4 text-center hover:from-green-500/30 hover:to-emerald-500/30 transition-all">
                  <div className="text-2xl mb-2">🚀</div>
                  <div className="text-white font-medium">Démarrage</div>
                </a>
                <a href="#ai-features" className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-4 text-center hover:from-blue-500/30 hover:to-purple-500/30 transition-all">
                  <div className="text-2xl mb-2">🤖</div>
                  <div className="text-white font-medium">IA Avancée</div>
                </a>
                <a href="#automation" className="bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30 rounded-lg p-4 text-center hover:from-orange-500/30 hover:to-red-500/30 transition-all">
                  <div className="text-2xl mb-2">⚙️</div>
                  <div className="text-white font-medium">Automatisation</div>
                </a>
                <a href="#affiliate" className="bg-gradient-to-r from-pink-500/20 to-rose-500/20 border border-pink-500/30 rounded-lg p-4 text-center hover:from-pink-500/30 hover:to-rose-500/30 transition-all">
                  <div className="text-2xl mb-2">💰</div>
                  <div className="text-white font-medium">Affiliation</div>
                </a>
              </div>
            </div>

            {/* Getting Started Section */}
            <section id="getting-started" className="mb-16">
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-8 flex items-center">
                  <span className="bg-gradient-to-r from-green-500 to-emerald-500 w-12 h-12 rounded-full flex items-center justify-center mr-4 text-2xl">🚀</span>
                  Démarrage Rapide
                </h2>
                
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-green-300 mb-4">📋 Étapes pour commencer :</h3>
                    <div className="space-y-4">
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold">1</span>
                        <div>
                          <div className="text-white font-medium">Créer votre compte</div>
                          <div className="text-gray-300 text-sm">Inscription gratuite en 30 secondes</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold">2</span>
                        <div>
                          <div className="text-white font-medium">Générer votre première fiche</div>
                          <div className="text-gray-300 text-sm">Essayez avec n'importe quel produit</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold">3</span>
                        <div>
                          <div className="text-white font-medium">Exporter vers votre boutique</div>
                          <div className="text-gray-300 text-sm">Shopify, WooCommerce, CSV, JSON</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold">4</span>
                        <div>
                          <div className="text-white font-medium">Profiter des fonctionnalités Premium</div>
                          <div className="text-gray-300 text-sm">Essai gratuit 7 jours disponible</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white/5 rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-4">🎯 Plans Disponibles</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-green-300">✅ Gratuit</span>
                        <span className="text-gray-300">3 fiches/mois</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-blue-300">🔥 Pro</span>
                        <span className="text-gray-300">Illimité + IA</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-purple-300">💎 Premium</span>
                        <span className="text-gray-300">Tout + Automatisation</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* AI Features Section */}
            <section id="ai-features" className="mb-16">
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-8 flex items-center">
                  <span className="bg-gradient-to-r from-blue-500 to-purple-500 w-12 h-12 rounded-full flex items-center justify-center mr-4 text-2xl">🤖</span>
                  Fonctionnalités IA Avancées
                </h2>
                
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">🎯</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Analyse SEO Intelligente</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Optimisez automatiquement vos titres et descriptions pour un meilleur référencement.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Mots-clés optimaux
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Score de qualité
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Suggestions d'amélioration
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">🏆</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Étude Concurrentielle</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Analysez vos concurrents et découvrez les opportunités du marché.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Analyse de marché
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Positionnement prix
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Opportunités détectées
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">💎</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Optimisation Prix</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      L'IA calcule le prix optimal pour maximiser vos profits.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Prix recommandé
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Marge optimale
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Stratégie pricing
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">🌍</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Traduction Multilingue</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Traduisez vos fiches dans plus de 50 langues instantanément.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>50+ langues
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Qualité native
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Score de confiance
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">🎨</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Génération Variantes</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Créez automatiquement des variantes de vos produits.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Couleurs, tailles
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Descriptions uniques
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Prix différenciés
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="text-3xl mb-4">📸</div>
                    <h3 className="text-lg font-semibold text-white mb-3">Génération Images</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Créez des images professionnelles avec Flux Pro AI.
                    </p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Qualité studio
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Styles variés
                      </div>
                      <div className="flex items-center text-green-300">
                        <span className="mr-2">✅</span>Haute résolution
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Automation Section */}
            <section id="automation" className="mb-16">
              <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-8 flex items-center">
                  <span className="bg-gradient-to-r from-orange-500 to-red-500 w-12 h-12 rounded-full flex items-center justify-center mr-4 text-2xl">⚙️</span>
                  Automatisation Intelligente
                </h2>
                
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-orange-300 mb-4">🔄 Processus Automatiques</h3>
                    
                    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                      <h4 className="text-white font-medium mb-2">📊 Scraping SEO Quotidien</h4>
                      <p className="text-gray-300 text-sm">
                        Collecte automatique des tendances, mots-clés et prix concurrents chaque jour.
                      </p>
                    </div>

                    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                      <h4 className="text-white font-medium mb-2">🚀 Optimisation Produits</h4>
                      <p className="text-gray-300 text-sm">
                        Amélioration automatique de vos fiches basée sur les données collectées.
                      </p>
                    </div>

                    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                      <h4 className="text-white font-medium mb-2">📤 Publication Multi-Boutiques</h4>
                      <p className="text-gray-300 text-sm">
                        Envoi automatique vers Shopify, WooCommerce, Amazon, eBay.
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-4">⏰ Fréquences Configurables</h4>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Scraping données</span>
                        <span className="text-orange-300 font-medium">Quotidien</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Optimisation IA</span>
                        <span className="text-orange-300 font-medium">24h après scraping</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Publication auto</span>
                        <span className="text-orange-300 font-medium">Toutes les 2h</span>
                      </div>
                      <div className="border-t border-white/20 pt-4">
                        <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-lg p-3">
                          <div className="text-green-300 font-medium text-sm">✅ Configuration personnalisable</div>
                          <div className="text-gray-300 text-xs">Activez/désactivez par boutique</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Affiliate Section */}
            <section id="affiliate" className="mb-16">
              <div className="bg-gradient-to-r from-pink-500/10 to-rose-500/10 border border-pink-500/20 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-8 flex items-center">
                  <span className="bg-gradient-to-r from-pink-500 to-rose-500 w-12 h-12 rounded-full flex items-center justify-center mr-4 text-2xl">💰</span>
                  Programme d'Affiliation
                </h2>
                
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-pink-300 mb-4">🤝 Comment ça marche ?</h3>
                    
                    <div className="space-y-4">
                      <div className="flex items-start space-x-3">
                        <span className="bg-pink-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">1</span>
                        <div>
                          <div className="text-white font-medium">Inscrivez-vous comme affilié</div>
                          <div className="text-gray-300 text-sm">Formulaire simple avec vos informations</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-pink-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">2</span>
                        <div>
                          <div className="text-white font-medium">Obtenez votre code unique</div>
                          <div className="text-gray-300 text-sm">Code de parrainage personnalisé</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-pink-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">3</span>
                        <div>
                          <div className="text-white font-medium">Partagez et gagnez</div>
                          <div className="text-gray-300 text-sm">Commission sur chaque vente générée</div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-xl p-4 border border-green-500/30">
                      <h4 className="text-green-300 font-semibold mb-2">💎 Commissions Attractives</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-300">Plan Pro:</span>
                          <span className="text-green-300 font-bold">10% récurrent</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-300">Plan Premium:</span>
                          <span className="text-green-300 font-bold">15% récurrent</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-4">📊 Outils d'Affiliation</h4>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <div className="bg-blue-500/20 w-8 h-8 rounded-lg flex items-center justify-center">📈</div>
                        <div>
                          <div className="text-white font-medium">Dashboard analytics</div>
                          <div className="text-gray-300 text-xs">Suivi en temps réel</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="bg-green-500/20 w-8 h-8 rounded-lg flex items-center justify-center">🔗</div>
                        <div>
                          <div className="text-white font-medium">Liens de parrainage</div>
                          <div className="text-gray-300 text-xs">Tracking automatique</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="bg-purple-500/20 w-8 h-8 rounded-lg flex items-center justify-center">💳</div>
                        <div>
                          <div className="text-white font-medium">Paiements mensuels</div>
                          <div className="text-gray-300 text-xs">Virement automatique</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="bg-orange-500/20 w-8 h-8 rounded-lg flex items-center justify-center">📝</div>
                        <div>
                          <div className="text-white font-medium">Ressources marketing</div>
                          <div className="text-gray-300 text-xs">Bannières, textes, guides</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Integration & Support Section */}
            <section className="mb-16">
              <div className="grid md:grid-cols-2 gap-8">
                <div className="bg-gradient-to-r from-indigo-500/10 to-blue-500/10 border border-indigo-500/20 rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <span className="bg-gradient-to-r from-indigo-500 to-blue-500 w-10 h-10 rounded-full flex items-center justify-center mr-3 text-xl">🔗</span>
                    Intégrations
                  </h2>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="bg-green-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">🛒</div>
                      <span className="text-white">Shopify - Export direct</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-blue-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">🔧</div>
                      <span className="text-white">WooCommerce - Plugin</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-orange-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">📦</div>
                      <span className="text-white">Amazon - Seller Central</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-yellow-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">🏷️</div>
                      <span className="text-white">eBay - Listing auto</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-gray-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">📊</div>
                      <span className="text-white">CSV/JSON - Export</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-emerald-500/10 to-green-500/10 border border-emerald-500/20 rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                    <span className="bg-gradient-to-r from-emerald-500 to-green-500 w-10 h-10 rounded-full flex items-center justify-center mr-3 text-xl">🆘</span>
                    Support
                  </h2>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="bg-blue-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">💬</div>
                      <span className="text-white">Chat en direct - 24/7</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-purple-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">📧</div>
                      <span className="text-white">Email support premium</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-green-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">📚</div>
                      <span className="text-white">Base de connaissances</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-orange-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">🎥</div>
                      <span className="text-white">Tutoriels vidéo</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="bg-pink-500/20 w-8 h-8 rounded-lg flex items-center justify-center text-sm">🎓</div>
                      <span className="text-white">Formation personnalisée</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* FAQ Section */}
            <section className="mb-16">
              <div className="bg-white/5 rounded-2xl p-8 border border-white/10">
                <h2 className="text-3xl font-bold text-white mb-8 text-center">❓ Questions Fréquentes</h2>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Combien de fiches puis-je générer ?</h3>
                      <p className="text-gray-300 text-sm">Gratuit: 3/mois • Pro: Illimité • Premium: Illimité + IA</p>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Les images sont-elles incluses ?</h3>
                      <p className="text-gray-300 text-sm">Oui, génération d'images professionnelles avec Flux Pro AI dans les plans payants.</p>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Puis-je annuler à tout moment ?</h3>
                      <p className="text-gray-300 text-sm">Absolument, aucun engagement. Annulation en 1 clic depuis votre dashboard.</p>
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Le système automatique fonctionne-t-il vraiment ?</h3>
                      <p className="text-gray-300 text-sm">Oui, scraping quotidien + optimisation IA + publication auto vers vos boutiques.</p>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Mes données sont-elles sécurisées ?</h3>
                      <p className="text-gray-300 text-sm">Cryptage SSL, stockage sécurisé, conformité RGPD. Vos données ne sont jamais partagées.</p>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-purple-300 mb-2">Y a-t-il une formation ?</h3>
                      <p className="text-gray-300 text-sm">Oui, tutoriels vidéo, documentation complète et support personnalisé inclus.</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Call to Action */}
            <div className="text-center">
              <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-4">🚀 Prêt à Révolutionner Votre E-commerce ?</h2>
                <p className="text-xl text-gray-300 mb-8">Rejoignez plus de 1000 entrepreneurs qui nous font confiance</p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <button
                    onClick={() => {
                      setShowHelpPage(false);
                      onDirectPremiumCheckout && onDirectPremiumCheckout('premium');
                    }}
                    className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold py-4 px-8 rounded-xl text-lg transition-all transform hover:scale-105"
                  >
                    ✨ Essai Gratuit 7 Jours
                  </button>
                  <button
                    onClick={() => {
                      setShowHelpPage(false);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-4 px-8 rounded-xl text-lg transition-all transform hover:scale-105"
                  >
                    🎯 Voir les Plans
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 overflow-x-hidden main-content">
      {/* Navigation - Header XXL avec logo MEGA ULTRA VISIBLE */}
      <nav className="sticky top-0 z-50 h-24 md:h-44 lg:h-52 px-4 md:px-6 bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="w-full mx-auto overflow-hidden">
          <div className="flex justify-between items-center h-full gap-4 md:gap-6 min-w-0">
            <div className="flex items-center flex-shrink-0">
              <HeaderLogo 
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className="hover:scale-105 transition-transform duration-300"
              />
            </div>
            <div className="flex items-center gap-2 md:gap-4 flex-shrink">
              <LanguageSelector />
              
              {/* Bouton Aide - toujours visible */}
              <button
                onClick={() => setShowHelpPage(true)}
                className="text-blue-600 hover:text-blue-800 px-2 md:px-3 py-1 md:py-2 rounded-md text-xs md:text-sm font-medium transition duration-300 whitespace-nowrap"
                style={{color: '#2563eb !important'}}
              >
                <span className="hidden md:inline" style={{color: '#2563eb !important'}}>❓ Aide</span>
                <span className="md:hidden" style={{color: '#2563eb !important'}}>❓</span>
              </button>
              
              {showUserNavigation && (
                <button
                  onClick={() => window.location.href = '/'}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-2 md:px-4 py-1 md:py-2 rounded-md text-xs md:text-sm font-medium transition duration-300 whitespace-nowrap"
                >
                  <span className="hidden md:inline">📊 {t('dashboard')}</span>
                  <span className="md:hidden">📊</span>
                </button>
              )}
              {!showUserNavigation && (
                <>
                  <button
                    onClick={onShowAffiliateLogin}
                    className="text-yellow-500 hover:text-yellow-400 px-2 md:px-3 py-1 md:py-2 rounded-md text-xs md:text-sm font-medium transition duration-300 whitespace-nowrap"
                    style={{color: '#eab308 !important'}}
                  >
                    <span className="hidden md:inline" style={{color: '#eab308 !important'}}>💰 Affiliation</span>
                    <span className="md:hidden" style={{color: '#eab308 !important'}}>💰</span>
                  </button>
                  <button
                    onClick={() => setShowLogin(true)}
                    className="text-blue-600 hover:text-blue-800 px-2 md:px-3 py-1 md:py-2 rounded-md text-xs md:text-sm font-medium transition duration-300 whitespace-nowrap"
                    style={{color: '#2563eb !important', display: 'block !important', visibility: 'visible !important'}}
                  >
                    <span className="hidden md:inline" style={{color: '#2563eb !important'}}>{t('connection')}</span>
                    <span className="md:hidden" style={{color: '#2563eb !important'}}>🔑</span>
                  </button>
                  <button
                    onClick={() => {
                      setActiveModalTab('register');
                      setShowLogin(true);
                    }}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-2 md:px-4 py-1 md:py-2 rounded-md text-xs md:text-sm font-medium transition duration-300 whitespace-nowrap"
                  >
                    <span className="hidden md:inline">{t('register')}</span>
                    <span className="md:hidden">➕</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* ✅ NOUVEAU: Hero 3D Section Immersive - AVEC SUSPENSE SÉCURISÉ */}
      {/* Hero Section avec animations CSS */}
      <HeroSection 
        onDirectPremiumCheckout={onDirectPremiumCheckout}
        currentLanguage={currentLanguage}
        PLATFORM_CONFIG={PLATFORM_CONFIG}
        className="mt-[76px]" // Marge pour navigation fixe
      />

      {/* ✅ NOUVEAU: Bento Features Section */}
      <BentoFeatures />

      {/* ✅ NOUVEAU: Premium Pricing Section */}
      <PremiumPricing 
        dynamicPricing={dynamicPricing}
        t={t}
        currentLanguage={currentLanguage}
        onDirectPremiumCheckout={onDirectPremiumCheckout}
      />

      {/* Affiliate Call-to-Action Section */}
      <div className="py-16 bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center px-6 py-3 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 mb-8">
              <svg className="w-5 h-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              <span className="text-blue-300 font-medium text-sm">
                {currentLanguage === 'fr' ? '🛡️ Tous nos plans incluent une garantie satisfait ou remboursé de 14 jours' : '🛡️ All plans include a 14-day money-back guarantee'}
              </span>
            </div>
            
            {/* Affiliate Call-to-Action */}
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-8 max-w-2xl mx-auto">
              <h3 className="text-2xl font-bold text-white mb-3">
                💰 {currentLanguage === 'fr' ? 'Gagnez avec ECOMSIMPLY' : 'Earn with ECOMSIMPLY'}
              </h3>
              <p className="text-gray-300 text-lg mb-6">
                {currentLanguage === 'fr' 
                  ? 'Rejoignez notre programme d\'affiliation et gagnez jusqu\'à 15% de commission récurrente sur chaque vente !'
                  : 'Join our affiliate program and earn up to 15% recurring commission on every sale!'
                }
              </p>
              <button
                onClick={() => setShowAffiliateModal(true)}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                🚀 {currentLanguage === 'fr' ? 'Devenir Affilié' : 'Become an Affiliate'}
              </button>
              <p className="text-sm text-gray-400 mt-4">
                {currentLanguage === 'fr' ? 'Inscription gratuite • Approuvé en 24-48h' : 'Free registration • Approved in 24-48h'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Login/Register Modal with Tabs */}
      {showLogin && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => {
            setShowLogin(false);
            setActiveModalTab('login'); // Reset tab
          }}
        >
          <div 
            className="bg-white rounded-lg p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()} // Empêcher la fermeture du modal quand on clique sur le contenu
          >
            {/* Tab Navigation */}
            <div className="flex border-b mb-4">
              <button
                onClick={() => setActiveModalTab('login')}
                className={`flex-1 py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeModalTab === 'login'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Connexion
              </button>
              <button
                onClick={() => setActiveModalTab('register')}
                className={`flex-1 py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeModalTab === 'register'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                S'inscrire
              </button>
            </div>

            {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>}

            {/* Login Tab Content */}
            {activeModalTab === 'login' && (
              <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-900">{t('connection')}</h2>
                <form onSubmit={handleLogin}>
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-bold mb-2">{t('email')}</label>
                    <input
                      type="email"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-gray-700 text-sm font-bold mb-2">{t('password')}</label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                      required
                    />
                    <div className="mt-2 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          setShowLogin(false);
                          setShowResetModal(true);
                        }}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        {t('resetPassword') || "Réinitialiser le mot de passe"}
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
                    >
                      {loading ? `${t('loading')}` : t('login')}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowLogin(false);
                        setActiveModalTab('login'); // Reset tab
                      }}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      {t('cancel')}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Register Tab Content */}
            {activeModalTab === 'register' && (
              <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-900">{t('register')}</h2>
                <form onSubmit={handleRegister}>
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-bold mb-2">{t('name')}</label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
                      value={registerForm.name}
                      onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-bold mb-2">{t('email')}</label>
                    <input
                      type="email"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-gray-700 text-sm font-bold mb-2">{t('password')}</label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
                    >
                      {loading ? t('registering') : t('signup')}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowLogin(false);
                        setActiveModalTab('login'); // Reset tab
                      }}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      {t('cancel')}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Plan Selection Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">
              Plan {selectedPlan === 'pro' ? 'Pro' : 'Entreprise'} Sélectionné
            </h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                {selectedPlan === 'pro' 
                  ? 'Vous avez choisi le plan Pro à 29€/mois avec 100 fiches par mois et IA avancée.'
                  : 'Vous avez choisi le plan Entreprise à 99€/mois avec fiches illimitées et IA personnalisée.'
                }
              </p>
              <p className="text-sm text-gray-600">
                {t('createAccountFirst')}
              </p>
            </div>
            <div className="flex items-center justify-between space-x-3">
              <button
                onClick={() => {
                  setShowPlanModal(false);
                  setActiveModalTab('register');
                  setShowLogin(true);
                }}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              >
                Créer un Compte
              </button>
              <button
                onClick={() => setShowPlanModal(false)}
                className="flex-1 text-gray-600 hover:text-gray-800 border border-gray-300 py-2 px-4 rounded"
              >
                Retour
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plan Registration Modal */}
      {showPlanRegistration && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4 relative">
            <button
              onClick={resetPlanRegistration}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                {selectedPlanForRegistration === 'pro' ? '⭐' : '👑'}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                🚀 Créer un Compte {selectedPlanForRegistration === 'pro' ? 'Pro' : 'Premium'}
              </h2>
              <p className="text-gray-600 text-sm">
                Créez votre compte pour accéder au plan <strong>{selectedPlanForRegistration === 'pro' ? 'Pro (29€/mois)' : 'Premium (99€/mois)'}</strong>
              </p>
              
              {/* Plan Features Quick Preview */}
              <div className="bg-gray-50 rounded-lg p-3 mt-4 text-left">
                <h4 className="font-semibold text-gray-800 mb-2">✨ Ce que vous obtiendrez :</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {selectedPlanForRegistration === 'pro' ? (
                    <>
                      <li>✅ Génération de ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois</li>
                      <li>✅ Export multiformat</li>
                      <li>✅ Intégration de ${PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes E-commerce</li>
                      <li>✅ Publication automatique par lot sur la plateforme E-commerce</li>
                      <li>✅ IA avancée intégrée (Optimisation SEO, Analyse Concurrentielle, optimisation des prix, Variantes produits, Traduction multilingue)</li>
                      <li>✅ Analytics Pro intégré (Performance Produits, Performance Intégrations, Engagement des clients)</li>
                      <li>✅ Dashboard complet (Taux de conversion, Vente total, Mots-clés Populaires, ...)</li>
                    </>
                  ) : (
                    <>
                      <li>Génération de fiche illimitée</li>
                      <li>Intégration 7 plateformes e-commerce (Shopify, WooCommerce, Amazon, eBay, Etsy)</li>
                      <li>Scraping automatique des SEO</li>
                      <li>Analyse concurrentielle & optimisation des SEO et Prix</li>
                      <li>Publication automatique sur les boutiques connectées</li>
                      <li>Analytics Premium & Dashboard intelligent avec Business Intelligence</li>
                      <li>Publication en lot sur 7 boutiques connectées</li>
                      <li>Export multiformat (Excel, CSV, PDF, ...)</li>
                    </>
                  )}
                </ul>
              </div>
            </div>

            <form onSubmit={handlePlanRegistration} className="space-y-4">
              <div>
                <input
                  type="text"
                  placeholder="Nom complet"
                  value={planRegistrationData.name}
                  onChange={(e) => setPlanRegistrationData({...planRegistrationData, name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <input
                  type="email"
                  placeholder="Adresse email"
                  value={planRegistrationData.email}
                  onChange={(e) => setPlanRegistrationData({...planRegistrationData, email: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <input
                  type="password"
                  placeholder="Mot de passe (minimum 6 caractères)"
                  value={planRegistrationData.password}
                  onChange={(e) => setPlanRegistrationData({...planRegistrationData, password: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  minLength={6}
                  required
                />
              </div>
              
              <div>
                <input
                  type="password"
                  placeholder="Confirmer le mot de passe"
                  value={planRegistrationData.confirmPassword}
                  onChange={(e) => setPlanRegistrationData({...planRegistrationData, confirmPassword: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Terms and Security Notice */}
              <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
                <p>🔒 En créant ce compte, vous acceptez nos conditions d'utilisation.</p>
                <p>💳 Vous serez redirigé vers notre partenaire de paiement sécurisé Stripe après la création du compte.</p>
                <p>❌ Vous pouvez annuler votre abonnement à tout moment.</p>
              </div>

              <div className="space-y-3">
                <button
                  type="button"
                  onClick={resetPlanRegistration}
                  className="w-full py-3 px-4 rounded-lg font-semibold text-gray-700 bg-gray-200 hover:bg-gray-300 transition-all duration-200"
                >
                  ❌ Annuler
                </button>
                
                <button
                  type="submit"
                  disabled={planRegistrationLoading}
                  className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200 ${
                    planRegistrationLoading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 transform hover:scale-105'
                  }`}
                >
                  {planRegistrationLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 818-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Création en cours...
                    </span>
                  ) : (
                    `🚀 Créer le Compte et Accéder au Plan ${selectedPlanForRegistration === 'pro' ? 'Pro' : 'Premium'}`
                  )}
                </button>
              </div>
            </form>

            {/* Alternative Options */}
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600">
                Vous avez déjà un compte ?{' '}
                <button
                  onClick={() => {
                    resetPlanRegistration();
                    setShowLogin(true);
                  }}
                  className="text-purple-600 hover:text-purple-800 font-semibold"
                >
                  Se connecter
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Plan Choice Modal - Connexion ou Création de Compte */}
      {showPlanChoiceModal && selectedPlanForChoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4 relative">
            {/* Bouton de fermeture */}
            <button
              onClick={closePlanChoiceModal}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors"
              title="Fermer"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* En-tête du modal */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                {selectedPlanForChoice === 'pro' ? '⭐' : '👑'}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedPlanForChoice === 'pro' ? '⭐ Plan Pro' : '👑 Plan Premium'}
              </h2>
              <p className="text-gray-600 text-sm">
                Choisissez comment vous souhaitez accéder au plan{' '}
                <strong>
                  {selectedPlanForChoice === 'pro' ? 'Pro (29€/mois)' : 'Premium (99€/mois)'}
                </strong>
              </p>
              
              {/* Aperçu des fonctionnalités */}
              <div className="bg-gray-50 rounded-lg p-3 mt-4 text-left">
                <h4 className="font-semibold text-gray-800 mb-2">✨ Ce plan inclut :</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {selectedPlanForChoice === 'pro' ? (
                    <>
                      <li>✅ Génération de ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois</li>
                      <li>✅ Export multiformat</li>
                      <li>✅ Intégration de ${PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes E-commerce</li>
                      <li>✅ Publication automatique par lot sur la plateforme E-commerce</li>
                      <li>✅ IA avancée intégrée (Optimisation SEO, Analyse Concurrentielle, optimisation des prix, Variantes produits, Traduction multilingue)</li>
                      <li>✅ Analytics Pro intégré (Performance Produits, Performance Intégrations, Engagement des clients)</li>
                      <li>✅ Dashboard complet (Taux de conversion, Vente total, Mots-clés Populaires, ...)</li>
                    </>
                  ) : (
                    <>
                      <li>Génération de fiche illimitée</li>
                      <li>Intégration 7 plateformes e-commerce (Shopify, WooCommerce, Amazon, eBay, Etsy)</li>
                      <li>Scraping automatique des SEO</li>
                      <li>Analyse concurrentielle & optimisation des SEO et Prix</li>
                      <li>Publication automatique sur les boutiques connectées</li>
                      <li>Analytics Premium & Dashboard intelligent avec Business Intelligence</li>
                      <li>Publication en lot sur 7 boutiques connectées</li>
                      <li>Export multiformat (Excel, CSV, PDF, ...)</li>
                    </>
                  )}
                </ul>
              </div>
            </div>

            {/* Options de choix */}
            <div className="space-y-3">
              {/* Option Se connecter */}
              <button
                onClick={handleChoiceLogin}
                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white py-3 px-6 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                <span>🔑 J'ai déjà un compte - Se connecter</span>
              </button>

              {/* Option Créer un compte */}
              <button
                onClick={handleChoiceRegister}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white py-3 px-6 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                <span>🚀 Nouveau client - Créer un compte</span>
              </button>
            </div>

            {/* Information supplémentaire */}
            <div className="mt-6 text-center">
              <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
                <p>💡 <strong>Nouveau chez nous ?</strong> Créez votre compte pour commencer immédiatement.</p>
                <p>🔄 <strong>Déjà client ?</strong> Connectez-vous pour mettre à niveau votre plan.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Success Modal */}
      {showUpgradeSuccess && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-4 text-gray-900">
                🎉 Paiement Réussi !
              </h2>
              <p className="text-gray-700 mb-6">
                Votre abonnement au plan {selectedUpgradePlan === 'pro' ? 'Pro' : 'Entreprise'} a été activé avec succès. 
                {t('enjoyPremiumFeatures')}
              </p>
              <button
                onClick={() => {
                  setShowUpgradeSuccess(false);
                  // L'utilisateur sera automatiquement redirigé vers le dashboard une fois connecté
                }}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              >
                Parfait !
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
          <div className="flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError('')} className="ml-4 text-red-700 hover:text-red-900">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">
              Mise à niveau vers le Plan {selectedUpgradePlan === 'pro' ? 'Pro' : 'Entreprise'}
            </h2>
            
            <div className="mb-6">
              <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg mb-4">
                <h3 className="font-semibold text-gray-900 mb-2">
                  {selectedUpgradePlan === 'pro' ? '🚀 Plan Pro - 29€/mois' : '🏢 Plan Entreprise - 99€/mois'}
                </h3>
                <ul className="text-sm text-gray-700 space-y-1">
                  {selectedUpgradePlan === 'pro' ? (
                    <>
                      <li>✅ Génération de ${PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches par mois</li>
                      <li>✅ Export multiformat</li>
                      <li>✅ Intégration de ${PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes E-commerce</li>
                      <li>✅ Publication automatique par lot sur la plateforme E-commerce</li>
                      <li>✅ IA avancée intégrée (Optimisation SEO, Analyse Concurrentielle, optimisation des prix, Variantes produits, Traduction multilingue)</li>
                      <li>✅ Analytics Pro intégré (Performance Produits, Performance Intégrations, Engagement des clients)</li>
                      <li>✅ Dashboard complet (Taux de conversion, Vente total, Mots-clés Populaires, ...)</li>
                    </>
                  ) : (
                    <>
                      <li>✅ Fiches produits illimitées</li>
                      <li>✅ IA personnalisée et API dédiée</li>
                      <li>✅ Support 24/7 avec formation</li>
                      <li>✅ Analytics avancées et intégrations</li>
                    </>
                  )}
                </ul>
              </div>
              
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-4">
                <p className="text-sm text-red-800">
                  <strong>⚠️ Erreur de paiement :</strong> {error}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between space-x-3">
              <button
                onClick={() => handleUpgrade(selectedUpgradePlan)}
                disabled={loading}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
              >
                {loading ? 'Redirection...' : 'Réessayer'}
              </button>
              <button
                onClick={() => {
                  setShowUpgradeModal(false);
                  setError('');
                }}
                className="flex-1 text-gray-600 hover:text-gray-800 border border-gray-300 py-2 px-4 rounded"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Customer Reviews Section */}
      <div className="py-16 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-base text-purple-300 font-semibold tracking-wide uppercase">{t('testimonials')}</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-white sm:text-4xl">
              {t('whatClientsSay')}
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-300 mx-auto">
              {getEcommerceTrustText()}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {displayedReviews.map((review) => (
              <div 
                key={review.id} 
                className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-300 transform hover:-translate-y-1"
              >
                {/* Rating Stars */}
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className={`w-5 h-5 ${
                        i < review.rating ? 'text-yellow-400' : 'text-gray-600'
                      }`}
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>

                {/* Review Comment */}
                <p className="text-gray-200 text-sm leading-relaxed mb-4 italic">
                  "{review.comment}"
                </p>

                {/* Author Info */}
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-sm mr-4">
                    {review.avatar}
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm">{review.name}</div>
                    <div className="text-purple-300 text-xs">{review.title}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* View All Reviews Button */}
          {!showAllReviews && customerReviews.length > 5 && (
            <div className="text-center mt-12">
              <button
                onClick={() => setShowAllReviews(true)}
                className="bg-white/10 hover:bg-white/20 text-white border border-white/30 px-8 py-3 rounded-full font-medium transition-all duration-300 backdrop-blur-md"
              >
                Voir tous les avis ({customerReviews.length})
              </button>
            </div>
          )}

          {/* Show Less Button */}
          {showAllReviews && (
            <div className="text-center mt-12">
              <button
                onClick={() => setShowAllReviews(false)}
                className="bg-white/10 hover:bg-white/20 text-white border border-white/30 px-8 py-3 rounded-full font-medium transition-all duration-300 backdrop-blur-md"
              >
                Voir moins d'avis
              </button>
            </div>
          )}

          {/* Trust Indicators */}
          <div className="mt-16 pt-8 border-t border-white/20">
            <div className="text-center mb-4">
              <span className="inline-flex items-center px-3 py-1 text-xs bg-green-500/20 text-green-300 rounded-full border border-green-500/30">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                {currentLanguage === 'fr' ? 'Données en temps réel' : 'Real-time data'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-white mb-2">
                  {loadingStats ? '...' : (publicStats?.satisfied_clients?.toLocaleString('fr-FR') || '10,000')}+
                </div>
                <div className="text-purple-300 text-sm">{t('satisfiedClients')}</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-white mb-2">
                  {loadingStats ? '...' : `${publicStats?.average_rating || 4.8}/5`}
                </div>
                <div className="text-purple-300 text-sm">{t('averageRating')}</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-white mb-2">
                  {loadingStats ? '...' : `${publicStats?.satisfaction_rate || 98}%`}
                </div>
                <div className="text-purple-300 text-sm">{t('satisfactionRate')}</div>
              </div>
            </div>
          </div>

          {/* Add Testimonial Section */}
          <div className="mt-12 pt-8 border-t border-white/20">
            <div className="text-center">
              <h3 className="text-xl font-bold text-white mb-4">{t('shareExperience')}</h3>
              <p className="text-gray-300 mb-6">{t('helpOthers')}</p>
              
              {!showTestimonialForm ? (
                <button
                  onClick={() => setShowTestimonialForm(true)}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3 rounded-full font-medium transition-all duration-300 transform hover:scale-105 shadow-lg"
                >
                  ✍️ {t('leaveTestimonial')}
                </button>
              ) : (
                <div className="max-w-2xl mx-auto">
                  <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20">
                    <form onSubmit={submitTestimonial} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-white text-sm font-medium mb-2">
                            {t('name')} <span className="text-red-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={testimonialForm.name}
                            onChange={(e) => setTestimonialForm({...testimonialForm, name: e.target.value})}
                            className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-white/20 transition-all"
                            placeholder="Ex: Fatou D."
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-white text-sm font-medium mb-2">
                            Entreprise / Poste <span className="text-red-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={testimonialForm.title}
                            onChange={(e) => setTestimonialForm({...testimonialForm, title: e.target.value})}
                            className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-white/20 transition-all"
                            placeholder="Ex: Fondatrice de BeautyZone Paris"
                            required
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-white text-sm font-medium mb-2">
                          Note <span className="text-red-400">*</span>
                        </label>
                        <div className="flex items-center space-x-2">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star}
                              type="button"
                              onClick={() => setTestimonialForm({...testimonialForm, rating: star})}
                              className={`text-3xl transition-colors ${
                                star <= testimonialForm.rating 
                                  ? 'text-yellow-400 hover:text-yellow-300' 
                                  : 'text-gray-600 hover:text-gray-500'
                              }`}
                            >
                              ★
                            </button>
                          ))}
                          <span className="text-white ml-4">({testimonialForm.rating}/5)</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-white text-sm font-medium mb-2">
                          Votre témoignage <span className="text-red-400">*</span>
                        </label>
                        <textarea
                          value={testimonialForm.comment}
                          onChange={(e) => setTestimonialForm({...testimonialForm, comment: e.target.value})}
                          rows={4}
                          className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-white/20 transition-all resize-none"
                          placeholder={currentLanguage === 'fr' ? 
                            "Partagez votre expérience avec ECOMSIMPLY..." :
                            "Share your experience with ECOMSIMPLY..."
                          }
                          required
                        />
                        <div className="text-xs text-gray-400 mt-1">
                          Décrivez comment ECOMSIMPLY vous a aidé dans votre business
                        </div>
                      </div>

                      <div className="flex justify-center space-x-4">
                        <button
                          type="button"
                          onClick={() => {
                            setShowTestimonialForm(false);
                            setTestimonialForm({ name: '', title: '', rating: 5, comment: '' });
                          }}
                          className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/30 rounded-lg transition-all"
                        >
                          Annuler
                        </button>
                        <button
                          type="submit"
                          disabled={loading}
                          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {loading ? 
                            (currentLanguage === 'fr' ? 'Envoi...' : 'Sending...') : 
                            (currentLanguage === 'fr' ? 'Publier mon témoignage' : 'Publish my testimonial')
                          }
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Affiliate Registration Modal */}
      {showAffiliateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-8 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-900">
                🚀 Rejoindre le Programme d'Affiliation
              </h2>
              <button
                onClick={() => setShowAffiliateModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-green-800 mb-2">
                💰 Gagnez jusqu'à 15% de commission récurrente !
              </h3>
              <ul className="text-green-700 text-sm space-y-1">
                <li>• 10% sur les abonnements Pro (29€ → 2.90€/mois)</li>
                <li>• 15% sur les abonnements Premium (99€ → 14.85€/mois)</li>
                <li>• Commissions récurrentes chaque mois</li>
                <li>• Tracking avancé et dashboard personnel</li>
                <li>• Paiements automatiques mensuels</li>
              </ul>
            </div>

            <form onSubmit={handleAffiliateRegistration} className="space-y-6">
              {/* Informations personnelles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email * <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={affiliateForm.email}
                    onChange={(e) => updateAffiliateForm('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="votre@email.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom complet * <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={affiliateForm.name}
                    onChange={(e) => updateAffiliateForm('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="Ex: Sarah Dubois"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Entreprise / Marque
                  </label>
                  <input
                    type="text"
                    value={affiliateForm.company}
                    onChange={(e) => updateAffiliateForm('company', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="Ex: BeautyZone Paris"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Site web / Blog
                  </label>
                  <input
                    type="url"
                    value={affiliateForm.website}
                    onChange={(e) => updateAffiliateForm('website', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="https://votre-site.com"
                  />
                </div>
              </div>

              {/* Réseaux sociaux */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Réseaux sociaux (optionnel)
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <span className="text-blue-500 mr-2">🐦</span>
                      <input
                        type="text"
                        value={affiliateForm.social_media.twitter}
                        onChange={(e) => updateAffiliateForm('social_media.twitter', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                        placeholder="@votre_twitter"
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center">
                      <span className="text-pink-500 mr-2">📷</span>
                      <input
                        type="text"
                        value={affiliateForm.social_media.instagram}
                        onChange={(e) => updateAffiliateForm('social_media.instagram', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                        placeholder="@votre_instagram"
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center">
                      <span className="text-red-500 mr-2">🎥</span>
                      <input
                        type="text"
                        value={affiliateForm.social_media.youtube}
                        onChange={(e) => updateAffiliateForm('social_media.youtube', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                        placeholder="Chaîne YouTube"
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center">
                      <span className="text-black mr-2">🎵</span>
                      <input
                        type="text"
                        value={affiliateForm.social_media.tiktok}
                        onChange={(e) => updateAffiliateForm('social_media.tiktok', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                        placeholder="@votre_tiktok"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Informations de paiement */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Méthode de paiement préférée * <span className="text-red-500">*</span>
                </label>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="payment_method"
                      value="bank_transfer"
                      checked={affiliateForm.payment_method === 'bank_transfer'}
                      onChange={(e) => updateAffiliateForm('payment_method', e.target.value)}
                      className="mr-3"
                    />
                    <span>🏦 Virement bancaire (SEPA)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="payment_method"
                      value="paypal"
                      checked={affiliateForm.payment_method === 'paypal'}
                      onChange={(e) => updateAffiliateForm('payment_method', e.target.value)}
                      className="mr-3"
                    />
                    <span>💳 PayPal</span>
                  </label>
                </div>

                {affiliateForm.payment_method === 'bank_transfer' && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nom de la banque *
                      </label>
                      <input
                        type="text"
                        value={affiliateForm.payment_details.bank_name}
                        onChange={(e) => updateAffiliateForm('payment_details.bank_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                        placeholder="Ex: Crédit Agricole"
                        required={affiliateForm.payment_method === 'bank_transfer'}
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          IBAN *
                        </label>
                        <input
                          type="text"
                          value={affiliateForm.payment_details.iban}
                          onChange={(e) => updateAffiliateForm('payment_details.iban', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                          placeholder="FR76 1234 5678 9012 3456 7890 123"
                          required={affiliateForm.payment_method === 'bank_transfer'}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          BIC/SWIFT *
                        </label>
                        <input
                          type="text"
                          value={affiliateForm.payment_details.bic}
                          onChange={(e) => updateAffiliateForm('payment_details.bic', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                          placeholder="AGRIFRPP"
                          required={affiliateForm.payment_method === 'bank_transfer'}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Motivation */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pourquoi souhaitez-vous devenir affilié ECOMSIMPLY ? * <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={affiliateForm.motivation}
                  onChange={(e) => updateAffiliateForm('motivation', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="Expliquez brièvement comment vous comptez promouvoir ECOMSIMPLY et pourquoi vous seriez un bon affilié..."
                  required
                />
              </div>

              {/* Boutons d'action */}
              <div className="flex justify-end space-x-4 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowAffiliateModal(false)}
                  className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={affiliateLoading}
                  className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-md font-semibold disabled:opacity-50"
                >
                  {affiliateLoading ? '⏳ Inscription...' : '🚀 Rejoindre le Programme'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Chatbot */}
      <Chatbot />
      
      {/* Contact Form - Always accessible */}
      <ContactForm />

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">🔒 Changer le Mot de Passe</h2>
            <p className="text-gray-600 mb-4 text-sm">
              Vous devez être connecté pour changer votre mot de passe. Veuillez vous connecter d'abord, puis accédez à cette fonction depuis votre tableau de bord.
            </p>
            {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>}
            <form onSubmit={changePasswordLanding} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mot de passe actuel
                </label>
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({...passwordForm, current_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({...passwordForm, new_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmer le nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={6}
                />
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-md"
                >
                  {loading ? 'Modification...' : 'Modifier le Mot de Passe'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                    setError('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Reset Modal */}
      {showResetModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">🔄 Réinitialiser le Mot de Passe</h2>
            <p className="text-gray-600 mb-4 text-sm">
              Entrez votre adresse email pour recevoir un lien de réinitialisation de mot de passe.
            </p>
            {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>}
            <form onSubmit={resetPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Adresse email
                </label>
                <input
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="votre@email.com"
                  required
                />
                <div className="text-xs text-gray-500 mt-1">
                  Nous enverrons un lien de réinitialisation à cette adresse
                </div>
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-md"
                >
                  {loading ? 'Envoi...' : 'Envoyer le Lien'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowResetModal(false);
                    setResetEmail('');
                    setError('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Affiliate Dashboard Component
const AffiliateDashboard = ({ affiliateCode, onLogout }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    loadAffiliateStats();
  }, [affiliateCode]);
  
  const loadAffiliateStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/affiliate/${affiliateCode}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Erreur chargement stats:', error);
      setError('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };
  
  const copyAffiliateLink = (page = '') => {
    const baseUrl = window.location.origin;
    const affiliateUrl = `${baseUrl}/?ref=${affiliateCode}&utm_source=affiliate&utm_medium=referral&utm_campaign=${affiliateCode}${page ? `&page=${page}` : ''}`;
    
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(affiliateUrl);
      alert('✅ Lien copié dans le presse-papiers !');
    } else {
      // Fallback pour les anciens navigateurs
      const textArea = document.createElement('textarea');
      textArea.value = affiliateUrl;
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        alert('✅ Lien copié dans le presse-papiers !');
      } catch (err) {
        alert('❌ Impossible de copier automatiquement. Voici votre lien:\n' + affiliateUrl);
      }
      document.body.removeChild(textArea);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-green-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Chargement de votre dashboard...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-red-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-6xl mb-4">❌</div>
          <p className="text-white text-lg mb-4">{error}</p>
          <button
            onClick={onLogout}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg"
          >
            Retour
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-green-900 to-slate-900">
      {/* Header */}
      <nav className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">
                💰 Dashboard Affilié
              </h1>
              <span className="ml-4 bg-green-500/20 text-green-300 px-3 py-1 rounded-full text-sm font-medium">
                {affiliateCode}
              </span>
            </div>
            <button
              onClick={onLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🚪 Déconnexion
            </button>
          </div>
        </div>
      </nav>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center">
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <span className="text-2xl">👆</span>
              </div>
              <div className="ml-4">
                <p className="text-gray-300 text-sm">Total Clics</p>
                <p className="text-white text-2xl font-bold">{stats?.total_clicks || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center">
              <div className="bg-green-500/20 p-3 rounded-lg">
                <span className="text-2xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-gray-300 text-sm">Conversions</p>
                <p className="text-white text-2xl font-bold">{stats?.total_conversions || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center">
              <div className="bg-purple-500/20 p-3 rounded-lg">
                <span className="text-2xl">📈</span>
              </div>
              <div className="ml-4">
                <p className="text-gray-300 text-sm">Taux de Conversion</p>
                <p className="text-white text-2xl font-bold">{stats?.conversion_rate || 0}%</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center">
              <div className="bg-yellow-500/20 p-3 rounded-lg">
                <span className="text-2xl">💰</span>
              </div>
              <div className="ml-4">
                <p className="text-gray-300 text-sm">Gains Totaux</p>
                <p className="text-white text-2xl font-bold">{stats?.total_earnings?.toFixed(2) || '0.00'}€</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Performance This Month */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">📅 Performance ce mois</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-300">Clics ce mois</span>
                <span className="text-white font-semibold">{stats?.clicks_this_month || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Conversions ce mois</span>
                <span className="text-white font-semibold">{stats?.conversions_this_month || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Gains ce mois</span>
                <span className="text-green-400 font-bold">{stats?.earnings_this_month?.toFixed(2) || '0.00'}€</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">💳 Commissions</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-300">En attente</span>
                <span className="text-yellow-400 font-semibold">{stats?.pending_commissions?.toFixed(2) || '0.00'}€</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Payées</span>
                <span className="text-green-400 font-semibold">{stats?.paid_commissions?.toFixed(2) || '0.00'}€</span>
              </div>
              <div className="bg-green-500/20 rounded-lg p-3 mt-4">
                <p className="text-green-300 text-sm">
                  💡 <strong>Commission:</strong> 10% sur Pro, 15% sur Premium
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Affiliate Links */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 mb-8">
          <h3 className="text-xl font-semibold text-white mb-4">🔗 Vos Liens d'Affiliation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Lien Principal</label>
              <div className="flex">
                <input
                  type="text"
                  value={`${window.location.origin}/?ref=${affiliateCode}`}
                  readOnly
                  className="flex-1 bg-white/5 border border-white/30 rounded-l-lg px-3 py-2 text-white text-sm"
                />
                <button
                  onClick={() => copyAffiliateLink()}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-r-lg transition-colors text-sm"
                >
                  📋 Copier
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Lien vers Pricing</label>
              <div className="flex">
                <input
                  type="text"
                  value={`${window.location.origin}/?ref=${affiliateCode}#pricing`}
                  readOnly
                  className="flex-1 bg-white/5 border border-white/30 rounded-l-lg px-3 py-2 text-white text-sm"
                />
                <button
                  onClick={() => copyAffiliateLink('pricing')}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-r-lg transition-colors text-sm"
                >
                  📋 Copier
                </button>
              </div>
            </div>
          </div>
          
          <div className="mt-4 bg-blue-500/20 rounded-lg p-3">
            <p className="text-blue-300 text-sm">
              💡 <strong>Astuce:</strong> Ajoutez ?ref={affiliateCode} à n'importe quelle URL ECOMSIMPLY pour tracker vos référencements
            </p>
          </div>
        </div>
        
        {/* Recent Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Landing Pages */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">📊 Pages les Plus Visitées</h3>
            {stats?.top_landing_pages?.length > 0 ? (
              <div className="space-y-3">
                {stats.top_landing_pages.map((page, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-300 text-sm truncate">{page.page}</span>
                    <span className="text-white font-semibold">{page.clicks} clics</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-4">Aucune donnée pour le moment</p>
            )}
          </div>
          
          {/* Recent Conversions */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">🎉 Conversions Récentes</h3>
            {stats?.recent_conversions?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_conversions.map((conversion, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <div>
                      <p className="text-white text-sm font-medium">Plan {conversion.plan}</p>
                      <p className="text-gray-400 text-xs">{new Date(conversion.date).toLocaleDateString()}</p>
                    </div>
                    <span className="text-green-400 font-bold">+{conversion.commission.toFixed(2)}€</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-4">Aucune conversion pour le moment</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Panel Component
const AdminPanel = ({ affiliateConfig, loadingAffiliateConfig, loadAffiliateConfig }) => {
  const { t } = useLanguage();
  const [adminStats, setAdminStats] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [users, setUsers] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);
  const [deletedAccounts, setDeletedAccounts] = useState([]);
  const [subscriptionChanges, setSubscriptionChanges] = useState([]);
  const [activeAdminTab, setActiveAdminTab] = useState('stats');
  const [loading, setLoading] = useState(false);
  const [newAdminForm, setNewAdminForm] = useState({
    email: '',
    name: '',
    password: ''
  });
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [showReplyModal, setShowReplyModal] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [replyForm, setReplyForm] = useState({ message: '' });
  const [sendingReply, setSendingReply] = useState(false);
  
  // Gestion des suppression d'utilisateurs
  const [showDeleteUserModal, setShowDeleteUserModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [deletingUser, setDeletingUser] = useState(false);
  
  // Gestion des témoignages
  const [testimonials, setTestimonials] = useState([]);
  const [showTestimonialReplyModal, setShowTestimonialReplyModal] = useState(false);
  const [selectedTestimonial, setSelectedTestimonial] = useState(null);
  const [testimonialReplyForm, setTestimonialReplyForm] = useState({ message: '' });
  const [sendingTestimonialReply, setSendingTestimonialReply] = useState(false);

  // Gestion des prix et promotions - NOUVEAU
  const [plansConfig, setPlansConfig] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [loadingPlansConfig, setLoadingPlansConfig] = useState(false);
  const [loadingPromotions, setLoadingPromotions] = useState(false);
  const [showPriceEditModal, setShowPriceEditModal] = useState(false);
  const [selectedPlanForEdit, setSelectedPlanForEdit] = useState(null);
  const [priceEditForm, setPriceEditForm] = useState({
    price: '',
    original_price: '',
    features: {},
    limits: {}
  });
  const [showPromotionModal, setShowPromotionModal] = useState(false);
  const [selectedPromotionForEdit, setSelectedPromotionForEdit] = useState(null);
  const [promotionForm, setPromotionForm] = useState({
    title: '',
    description: '',
    target_plans: [],
    discount_type: 'percentage',
    discount_value: '',
    badge_text: '',
    promotional_text: '',
    start_date: '',
    end_date: '',
    is_active: true
  });
  const [savingPrice, setSavingPrice] = useState(false);
  const [savingPromotion, setSavingPromotion] = useState(false);

  // Gestion des affiliés - NOUVEAU
  const [affiliates, setAffiliates] = useState([]);
  const [loadingAffiliates, setLoadingAffiliates] = useState(false);
  const [affiliateStats, setAffiliateStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    suspended: 0
  });
  const [selectedAffiliateForDetails, setSelectedAffiliateForDetails] = useState(null);
  const [showAffiliateDetailsModal, setShowAffiliateDetailsModal] = useState(false);
  const [affiliateDetailsData, setAffiliateDetailsData] = useState(null);
  const [updatingAffiliateStatus, setUpdatingAffiliateStatus] = useState(false);
  const [affiliateFilters, setAffiliateFilters] = useState({
    status: 'all',
    search: '',
    page: 1,
    limit: 20
  });

  // Configuration d'affiliation - NOUVEAU (moved to main App component)
  // const [affiliateConfig, setAffiliateConfig] = useState(null); // Now passed as prop
  // const [loadingAffiliateConfig, setLoadingAffiliateConfig] = useState(false); // Now passed as prop
  const [showAffiliateConfigModal, setShowAffiliateConfigModal] = useState(false);
  const [affiliateConfigForm, setAffiliateConfigForm] = useState({
    default_commission_rate_pro: 10.0,
    default_commission_rate_premium: 15.0,
    commission_type: 'recurring',
    payment_frequency: 'monthly',
    minimum_payout: 50.0,
    program_enabled: true,
    auto_approval: false,
    cookie_duration_days: 30,
    welcome_message: 'Bienvenue dans notre programme d\'affiliation !',
    terms_and_conditions: ''
  });
  const [savingAffiliateConfig, setSavingAffiliateConfig] = useState(false);

  // ✅ NOUVEAU: Gestion PriceTruth - États pour l'administration
  const [priceTruthStats, setPriceTruthStats] = useState(null);
  const [loadingPriceTruthStats, setLoadingPriceTruthStats] = useState(false);
  const [priceTruthHealth, setPriceTruthHealth] = useState(null);
  const [refreshingPrices, setRefreshingPrices] = useState(false);
  const [applyingConfig, setApplyingConfig] = useState(false);

  useEffect(() => {
    loadAdminData();
  }, [activeAdminTab]);

  // Effect pour charger les données selon l'onglet admin actif
  React.useEffect(() => {
    if (activeAdminTab === 'pricing') {
      loadPlansConfig();
    } else if (activeAdminTab === 'promotions') {
      loadPromotions();
    } else if (activeAdminTab === 'affiliates') {
      loadAffiliates();
    } else if (activeAdminTab === 'price-truth') {
      loadPriceTruthData();
    }
  }, [activeAdminTab, affiliateFilters]);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      // Charger différentes données selon l'onglet actif
      switch (activeAdminTab) {
        case 'stats':
          const [statsRes, enhancedStatsRes] = await Promise.all([
            axios.get(`${API}/admin/stats`),
            axios.get(`${API}/admin/enhanced-stats`)
          ]);
          setAdminStats({...statsRes.data, ...enhancedStatsRes.data});
          break;
        
        case 'users':
          const usersRes = await axios.get(`${API}/admin/users-detailed?limit=100`);
          setUsers(usersRes.data.users);
          break;
        
        case 'activity':
          const [logsRes, deletedRes, changesRes] = await Promise.all([
            axios.get(`${API}/admin/activity-logs?limit=50`),
            axios.get(`${API}/admin/deleted-accounts?limit=50`),
            axios.get(`${API}/admin/subscription-changes?limit=50`)
          ]);
          setActivityLogs(logsRes.data.logs);
          setDeletedAccounts(deletedRes.data.deleted_accounts);
          setSubscriptionChanges(changesRes.data.subscription_changes);
          break;
        
        case 'contacts':
          const contactsRes = await axios.get(`${API}/admin/contacts`);
          setContacts(contactsRes.data.contacts);
          break;
        
        case 'testimonials':
          const testimonialsRes = await axios.get(`${API}/admin/testimonials?admin_key=ECOMSIMPLY_ADMIN_2025`);
          setTestimonials(testimonialsRes.data.testimonials || []);
          break;
        
        case 'affiliate-config':
          loadAffiliateConfig();
          break;
        
        default:
          break;
      }
    } catch (error) {
      console.error('Erreur chargement données admin:', error);
    }
    setLoading(false);
  };

  // Fonctions pour la gestion des témoignages
  const openTestimonialReplyModal = (testimonial) => {
    setSelectedTestimonial(testimonial);
    setTestimonialReplyForm({ message: '' });
    setShowTestimonialReplyModal(true);
  };

  const closeTestimonialReplyModal = () => {
    setShowTestimonialReplyModal(false);
    setSelectedTestimonial(null);
    setTestimonialReplyForm({ message: '' });
  };

  const sendTestimonialReply = async (e) => {
    e.preventDefault();
    if (!selectedTestimonial || !testimonialReplyForm.message.trim()) return;

    setSendingTestimonialReply(true);
    try {
      await axios.post(`${API}/admin/testimonials/${selectedTestimonial.id}/reply?admin_key=ECOMSIMPLY_ADMIN_2025`, {
        reply_message: testimonialReplyForm.message.trim()
      });

      // Recharger les témoignages pour voir le statut mis à jour
      await loadAdminData();
      closeTestimonialReplyModal();
      
      alert('Réponse envoyée avec succès !');
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la réponse:', error);
      alert('Erreur lors de l\'envoi de la réponse. Veuillez réessayer.');
    } finally {
      setSendingTestimonialReply(false);
    }
  };

  // ✅ NOUVEAU: Fonction de chargement des données PriceTruth
  const loadPriceTruthData = async () => {
    setLoadingPriceTruthStats(true);
    try {
      const [statsResponse, healthResponse] = await Promise.all([
        axios.get(`${API}/price-truth/stats`),
        axios.get(`${API}/price-truth/health`)
      ]);
      
      setPriceTruthStats(statsResponse.data);
      setPriceTruthHealth(healthResponse.data);
    } catch (error) {
      console.error('Erreur chargement données PriceTruth:', error);
      setPriceTruthStats(null);
      setPriceTruthHealth(null);
    } finally {
      setLoadingPriceTruthStats(false);
    }
  };

  // NOUVELLES FONCTIONS POUR LA GESTION DES PRIX ET PROMOTIONS
  
  const loadPlansConfig = async () => {
    setLoadingPlansConfig(true);
    try {
      const response = await axios.get(`${API}/admin/plans-config?admin_key=ECOMSIMPLY_ADMIN_2025`);
      if (response.data.success) {
        setPlansConfig(response.data.plans_config);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des plans:', error);
    }
    setLoadingPlansConfig(false);
  };

  const loadPromotions = async () => {
    setLoadingPromotions(true);
    try {
      const response = await axios.get(`${API}/admin/promotions?admin_key=ECOMSIMPLY_ADMIN_2025`);
      if (response.data.success) {
        setPromotions(response.data.promotions);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des promotions:', error);
    }
    setLoadingPromotions(false);
  };

  const openPriceEditModal = (plan) => {
    setSelectedPlanForEdit(plan);
    setPriceEditForm({
      price: plan.price.toString(),
      original_price: plan.original_price?.toString() || '',
      features: plan.features || {},
      limits: plan.limits || {}
    });
    setShowPriceEditModal(true);
  };

  const closePriceEditModal = () => {
    setShowPriceEditModal(false);
    setSelectedPlanForEdit(null);
    setPriceEditForm({
      price: '',
      original_price: '',
      features: {},
      limits: {}
    });
  };

  const savePlanPrice = async (e) => {
    e.preventDefault();
    if (!selectedPlanForEdit) return;

    setSavingPrice(true);
    try {
      const updateData = {
        price: parseFloat(priceEditForm.price),
        features: priceEditForm.features,
        limits: priceEditForm.limits
      };

      if (priceEditForm.original_price) {
        updateData.original_price = parseFloat(priceEditForm.original_price);
      }

      await axios.put(
        `${API}/admin/plans-config/${selectedPlanForEdit.plan_name}?admin_key=ECOMSIMPLY_ADMIN_2025`,
        updateData
      );

      alert(`Prix du plan ${selectedPlanForEdit.plan_name} mis à jour avec succès !`);
      closePriceEditModal();
      
    } catch (error) {
      console.error('Erreur lors de la mise à jour du prix:', error);
      alert('Erreur lors de la mise à jour du prix');
    }
    setSavingPrice(false);
  };

  const openPromotionModal = (promotion = null) => {
    if (promotion) {
      setSelectedPromotionForEdit(promotion);
      setPromotionForm({
        title: promotion.title || '',
        description: promotion.description || '',
        target_plans: promotion.target_plans || [],
        discount_type: promotion.discount_type || 'percentage',
        discount_value: promotion.discount_value?.toString() || '',
        badge_text: promotion.badge_text || '',
        promotional_text: promotion.promotional_text || '',
        start_date: promotion.start_date ? new Date(promotion.start_date).toISOString().slice(0, 16) : '',
        end_date: promotion.end_date ? new Date(promotion.end_date).toISOString().slice(0, 16) : '',
        is_active: promotion.is_active !== false
      });
    } else {
      setSelectedPromotionForEdit(null);
      setPromotionForm({
        title: '',
        description: '',
        target_plans: [],
        discount_type: 'percentage',
        discount_value: '',
        badge_text: '',
        promotional_text: '',
        start_date: '',
        end_date: '',
        is_active: true
      });
    }
    setShowPromotionModal(true);
  };

  const closePromotionModal = () => {
    setShowPromotionModal(false);
    setSelectedPromotionForEdit(null);
  };

  const savePromotion = async (e) => {
    e.preventDefault();
    setSavingPromotion(true);
    
    try {
      const promotionData = {
        ...promotionForm,
        discount_value: parseFloat(promotionForm.discount_value),
        start_date: new Date(promotionForm.start_date).toISOString(),
        end_date: new Date(promotionForm.end_date).toISOString()
      };

      if (selectedPromotionForEdit) {
        // Mise à jour d'une promotion existante
        await axios.put(
          `${API}/admin/promotions/${selectedPromotionForEdit.id}?admin_key=ECOMSIMPLY_ADMIN_2025`,
          promotionData
        );
        alert('Promotion mise à jour avec succès !');
      } else {
        // Création d'une nouvelle promotion
        await axios.post(
          `${API}/admin/promotions?admin_key=ECOMSIMPLY_ADMIN_2025`,
          promotionData
        );
        alert('Promotion créée avec succès !');
      }

      await loadPromotions();
      closePromotionModal();
      
    } catch (error) {
      console.error('Erreur lors de la sauvegarde de la promotion:', error);
      alert('Erreur lors de la sauvegarde de la promotion');
    }
    setSavingPromotion(false);
  };

  const deletePromotion = async (promotionId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette promotion ?')) return;

    try {
      await axios.delete(`${API}/admin/promotions/${promotionId}?admin_key=ECOMSIMPLY_ADMIN_2025`);
      alert('Promotion supprimée avec succès !');
      await loadPromotions();
    } catch (error) {
      console.error('Erreur lors de la suppression de la promotion:', error);
      alert('Erreur lors de la suppression de la promotion');
    }
  };

  const updateTestimonialStatus = async (testimonialId, status) => {
    try {
      await axios.post(`${API}/admin/testimonials/${testimonialId}/status?admin_key=ECOMSIMPLY_ADMIN_2025`, {
        status: status
      });

      // Recharger les témoignages
      await loadAdminData();
      
      const statusText = {
        'approved': 'approuvé',
        'rejected': 'rejeté',
        'pending': 'en attente'
      };
      
      alert(`Témoignage ${statusText[status]} avec succès !`);
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut:', error);
      alert('Erreur lors de la mise à jour du statut. Veuillez réessayer.');
    }
  };

  const createNewAdmin = async () => {
    try {
      await axios.post(`${API}/admin/create-admin`, newAdminForm);
      alert('Nouveau compte administrateur créé avec succès !');
      setShowCreateAdminModal(false);
      setNewAdminForm({ email: '', name: '', password: '' });
      if (activeAdminTab === 'users') {
        loadAdminData(); // Recharger la liste des utilisateurs
      }
    } catch (error) {
      alert(`Erreur lors de la création: ${error.response?.data?.detail || error.message}`);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('fr-FR');
  };

  const getPlanLabel = (plan) => {
    const labels = {
      'gratuit': 'Gratuit',
      'pro': 'Pro (29€/mois)', 
      'premium': 'Premium (99€/mois)'
    };
    return labels[plan] || plan;
  };

  // Fonctions de gestion des affiliés
  // Test de diagnostic du système d'affiliation
  const runAffiliateSystemDiagnostic = async () => {
    try {
      const response = await axios.get(`${API}/debug/affiliate-system`);
      
      if (response.data.system_status.includes('✅')) {
        alert(`✅ Diagnostic système d'affiliation:\n\n` +
              `Statut: ${response.data.system_status}\n` +
              `Base de données: ${response.data.database_connection}\n` +
              `Total affiliés: ${response.data.affiliates_collection.total_count}\n` +
              `Clé admin: ${response.data.configuration.admin_key_format}\n` +
              `Configuration: ${response.data.configuration.exists ? '✅ Présente' : '❌ Manquante'}`);
      } else {
        alert(`❌ Erreur système d'affiliation:\n${response.data.error}`);
      }
    } catch (error) {
      console.error('Erreur diagnostic affiliation:', error);
      alert('❌ Impossible d\'exécuter le diagnostic du système d\'affiliation');
    }
  };

  const loadAffiliates = async () => {
    setLoadingAffiliates(true);
    try {
      const params = new URLSearchParams({
        admin_key: 'ECOMSIMPLY_ADMIN_2025',
        skip: ((affiliateFilters.page - 1) * affiliateFilters.limit).toString(),
        limit: affiliateFilters.limit.toString()
      });
      
      if (affiliateFilters.status !== 'all') {
        params.append('status', affiliateFilters.status);
      }
      
      const response = await axios.get(`${API}/admin/affiliates?${params}`);
      
      if (response.data.success) {
        setAffiliates(response.data.affiliates);
        
        // Calculer les statistiques
        const stats = response.data.affiliates.reduce((acc, affiliate) => {
          acc.total++;
          acc[affiliate.status] = (acc[affiliate.status] || 0) + 1;
          return acc;
        }, { total: 0, pending: 0, approved: 0, rejected: 0, suspended: 0 });
        
        setAffiliateStats(stats);
      }
    } catch (error) {
      console.error('❌ Erreur chargement affiliés:', error);
      
      // Gestion d'erreurs spécifiques
      if (error.response?.status === 403) {
        alert('❌ Erreur d\'authentification: Clé admin invalide');
      } else if (error.response?.status === 500) {
        alert('❌ Erreur serveur lors du chargement des affiliés. Réessayez dans quelques instants.');
      } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        alert('❌ Timeout: Le chargement prend trop de temps. Vérifiez votre connexion.');
      } else {
        alert(`❌ Erreur lors du chargement des affiliés: ${error.response?.data?.error || error.message}`);
      }
      
      // Réinitialiser les données en cas d'erreur
      setAffiliates([]);
      setAffiliateStats({ total: 0, pending: 0, approved: 0, rejected: 0, suspended: 0 });
    } finally {
      setLoadingAffiliates(false);
    }
  };

  const updateAffiliateStatus = async (affiliateId, newStatus) => {
    setUpdatingAffiliateStatus(true);
    try {
      const response = await axios.put(
        `${API}/admin/affiliates/${affiliateId}/status?admin_key=ECOMSIMPLY_ADMIN_2025`,
        null,
        { params: { status: newStatus } }
      );
      
      if (response.data.success) {
        alert(`Statut mis à jour avec succès !`);
        loadAffiliates(); // Recharger la liste
      }
    } catch (error) {
      console.error('Erreur mise à jour statut:', error);
      alert('Erreur lors de la mise à jour du statut');
    } finally {
      setUpdatingAffiliateStatus(false);
    }
  };

  const loadAffiliateDetails = async (affiliateId) => {
    try {
      const response = await axios.get(
        `${API}/admin/affiliates/${affiliateId}/detailed-stats?admin_key=ECOMSIMPLY_ADMIN_2025`
      );
      
      if (response.data.success) {
        setAffiliateDetailsData(response.data);
        setShowAffiliateDetailsModal(true);
      }
    } catch (error) {
      console.error('Erreur chargement détails affilié:', error);
      alert('Erreur lors du chargement des détails');
    }
  };

  const closeAffiliateDetailsModal = () => {
    setShowAffiliateDetailsModal(false);
    setSelectedAffiliateForDetails(null);
    setAffiliateDetailsData(null);
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      suspended: 'bg-gray-100 text-gray-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending: 'En attente',
      approved: 'Approuvé',
      rejected: 'Rejeté',
      suspended: 'Suspendu'
    };
    return labels[status] || status;
  };

  // Fonctions de configuration d'affiliation (use props from parent)
  const loadAffiliateConfigData = async () => {
    if (loadAffiliateConfig) {
      await loadAffiliateConfig();
      // Update form with loaded config
      if (affiliateConfig) {
        setAffiliateConfigForm({
          default_commission_rate_pro: affiliateConfig.default_commission_rate_pro || 10.0,
          default_commission_rate_premium: affiliateConfig.default_commission_rate_premium || 15.0,
          commission_type: affiliateConfig.commission_type || 'recurring',
          payment_frequency: affiliateConfig.payment_frequency || 'monthly',
          minimum_payout: affiliateConfig.minimum_payout || 50.0,
          program_enabled: affiliateConfig.program_enabled !== undefined ? affiliateConfig.program_enabled : true,
          auto_approval: affiliateConfig.auto_approval || false,
          cookie_duration_days: affiliateConfig.cookie_duration_days || 30,
          welcome_message: affiliateConfig.welcome_message || 'Bienvenue dans notre programme d\'affiliation !',
          terms_and_conditions: affiliateConfig.terms_and_conditions || ''
        });
      }
    }
  };

  const saveAffiliateConfig = async () => {
    setSavingAffiliateConfig(true);
    try {
      const response = await axios.put(
        `${API}/admin/affiliate-config?admin_key=ECOMSIMPLY_ADMIN_2025`,
        affiliateConfigForm
      );
      
      if (response.data.success) {
        alert('Configuration d\'affiliation sauvegardée avec succès !');
        setShowAffiliateConfigModal(false);
        if (loadAffiliateConfig) {
          loadAffiliateConfig();
        }
      }
    } catch (error) {
      console.error('Erreur sauvegarde config affiliation:', error);
      alert('Erreur lors de la sauvegarde de la configuration');
    } finally {
      setSavingAffiliateConfig(false);
    }
  };

  // Wrapper for form handling  
  const handleSaveAffiliateConfig = async () => {
    await saveAffiliateConfig();
  };

  const applyConfigToExistingAffiliates = async () => {
    if (!confirm('Êtes-vous sûr de vouloir appliquer cette configuration à tous les affiliés existants ?')) {
      return;
    }
    
    setApplyingConfig(true);
    try {
      const response = await axios.post(
        `${API}/admin/affiliate-bulk-update?admin_key=ECOMSIMPLY_ADMIN_2025`,
        {
          default_commission_rate_pro: affiliateConfigForm.default_commission_rate_pro,
          default_commission_rate_premium: affiliateConfigForm.default_commission_rate_premium,
          commission_type: affiliateConfigForm.commission_type
        }
      );
      
      if (response.data.success) {
        alert(`Configuration appliquée avec succès à ${response.data.updated_count} affiliés !`);
      }
    } catch (error) {
      console.error('Erreur application config aux affiliés:', error);
      alert('Erreur lors de l\'application de la configuration aux affiliés existants');
    } finally {
      setApplyingConfig(false);
    }
  };

  const bulkUpdateAffiliateCommissions = async () => {
    if (!confirm('Êtes-vous sûr de vouloir appliquer ces taux de commission à tous les affiliés existants ?')) {
      return;
    }

    try {
      const response = await axios.post(`${API}/admin/affiliate-bulk-update?admin_key=ECOMSIMPLY_ADMIN_2025`, {
        commission_rate_pro: affiliateConfigForm.default_commission_rate_pro,
        commission_rate_premium: affiliateConfigForm.default_commission_rate_premium,
        commission_type: affiliateConfigForm.commission_type
      });
      
      if (response.data.success) {
        alert(`✅ ${response.data.message}`);
      }
    } catch (error) {
      console.error('Erreur mise à jour commissions:', error);
      alert('Erreur lors de la mise à jour des commissions');
    }
  };

  // Fonctions de suppression d'utilisateurs
  const confirmDeleteUser = (user) => {
    setUserToDelete(user);
    setShowDeleteUserModal(true);
  };

  const closeDeleteUserModal = () => {
    setShowDeleteUserModal(false);
    setUserToDelete(null);
  };

  const deleteUser = async () => {
    if (!userToDelete) return;
    
    setDeletingUser(true);
    try {
      const response = await axios.post(`${API}/admin/delete-user-by-email`, {
        email: userToDelete.email,
        admin_key: "ECOMSIMPLY_ADMIN_2024"
      });
      
      if (response.data.success) {
        alert(`Utilisateur ${userToDelete.name} (${userToDelete.email}) supprimé avec succès !`);
        
        // Recharger la liste des utilisateurs
        loadAdminData();
        
        // Fermer le modal
        closeDeleteUserModal();
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert(`Erreur lors de la suppression: ${error.response?.data?.detail || error.message}`);
    }
    setDeletingUser(false);
  };

  const openReplyModal = (contact) => {
    setSelectedContact(contact);
    setReplyForm({ message: '' });
    setShowReplyModal(true);
  };

  const closeReplyModal = () => {
    setShowReplyModal(false);
    setSelectedContact(null);
    setReplyForm({ message: '' });
  };

  const sendReply = async (e) => {
    e.preventDefault();
    if (!selectedContact || !replyForm.message.trim()) return;

    setSendingReply(true);
    try {
      await axios.post(`${API}/admin/contacts/${selectedContact.id}/reply`, {
        reply_message: replyForm.message.trim()
      });

      // Recharger les contacts pour voir le statut mis à jour
      await loadAdminData();
      closeReplyModal();
      
      // Optionnel: afficher un message de succès
      alert(t('replyResponseSent') || 'Réponse envoyée avec succès !');
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la réponse:', error);
      alert('Erreur lors de l\'envoi de la réponse. Veuillez réessayer.');
    } finally {
      setSendingReply(false);
    }
  };

  if (loading && !adminStats && !users.length && !activityLogs.length) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-red-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Chargement des données administrateur...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6 max-w-full overflow-hidden">
      {/* Header Admin */}
      <div className="bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-lg p-4 md:p-6">
        <h2 className="text-xl md:text-3xl font-bold mb-2">🛡️ {t('adminPanelTitle')}</h2>
        <p className="text-red-100 text-sm md:text-base">{t('adminPanelSubtitle')}</p>
      </div>

      {/* Onglets Admin */}
      <div className="bg-white rounded-lg shadow max-w-full">
        <div className="border-b border-gray-200">
          <nav 
            className="flex space-x-2 md:space-x-8 px-2 md:px-6 overflow-x-auto overflow-y-hidden pb-2"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: '#ef4444 #f1f5f9'
            }}
          >
            {[
              { id: 'stats', label: `📊 ${t('stats')}`, icon: '📊' },
              { id: 'users', label: `👥 ${t('users')}`, icon: '👥' },
              { id: 'activity', label: `📝 ${t('activity')}`, icon: '📝' },
              { id: 'contacts', label: `📧 ${t('messages')}`, icon: '📧' },
              { id: 'testimonials', label: `⭐ ${t('testimonials')}`, icon: '⭐' },
              { id: 'pricing', label: `💰 Prix`, icon: '💰' },
              { id: 'promotions', label: `🎯 Promotions`, icon: '🎯' },
              { id: 'price-truth', label: `🔍 PriceTruth`, icon: '🔍' },
              { id: 'affiliates', label: `🤝 Affiliation`, icon: '🤝' },
              { id: 'affiliate-config', label: `⚙️ Config Affiliation`, icon: '⚙️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveAdminTab(tab.id)}
                className={`py-3 md:py-4 px-1 md:px-2 border-b-2 font-medium text-xs md:text-sm whitespace-nowrap flex-shrink-0 ${
                  activeAdminTab === tab.id
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-3 md:p-6 max-w-full overflow-hidden">
          {/* Onglet Statistiques */}
          {activeAdminTab === 'stats' && adminStats && (
            <div className="space-y-4 md:space-y-6">
              <h3 className="text-lg md:text-xl font-bold text-gray-900">{t('globalStats')}</h3>
              
              {/* Statistiques Utilisateurs */}
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3">👥 {t('users')}</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{adminStats.user_stats?.total_users || adminStats.total_users}</div>
                    <div className="text-sm text-blue-800">{t('totalUsers')}</div>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">{adminStats.user_stats?.admin_users || 0}</div>
                    <div className="text-sm text-green-800">{t('administrators')}</div>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">{adminStats.user_stats?.regular_users || 0}</div>
                    <div className="text-sm text-purple-800">{t('regularUsers')}</div>
                  </div>
                </div>
              </div>

              {/* Statistiques Abonnements */}
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3">💳 {t('subscriptions')}</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-600">{adminStats.subscription_stats?.gratuit || 0}</div>
                    <div className="text-sm text-gray-800">{t('planFree')}</div>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-yellow-600">{adminStats.subscription_stats?.pro || 0}</div>
                    <div className="text-sm text-yellow-800">{t('planPro')} (29€)</div>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-red-600">{adminStats.subscription_stats?.premium || 0}</div>
                    <div className="text-sm text-red-800">{t('planPremium')} (99€)</div>
                  </div>
                </div>
              </div>

              {/* Statistiques Revenus */}
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3">💰 {t('revenue')}</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">{adminStats.revenue_stats?.total_revenue || adminStats.revenue_total}€</div>
                    <div className="text-sm text-green-800">{t('totalRevenue')}</div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{adminStats.revenue_stats?.monthly_revenue || adminStats.revenue_this_month}€</div>
                    <div className="text-sm text-blue-800">{t('monthlyRevenue')}</div>
                  </div>
                </div>
              </div>

              {/* Statistiques d'Activité */}
              {adminStats.activity_stats && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">📈 {t('activityLast30Days')}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="text-2xl font-bold text-red-600">{adminStats.activity_stats.recent_deletions}</div>
                      <div className="text-sm text-red-800">{t('deletedAccounts')}</div>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="text-2xl font-bold text-green-600">{adminStats.activity_stats.recent_upgrades}</div>
                      <div className="text-sm text-green-800">{t('upgrades')}</div>
                    </div>
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                      <div className="text-2xl font-bold text-orange-600">{adminStats.activity_stats.recent_cancellations}</div>
                      <div className="text-sm text-orange-800">{t('cancellations')}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Onglet Utilisateurs */}
          {activeAdminTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">{t('userManagement')}</h3>
                <button
                  onClick={() => setShowCreateAdminModal(true)}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  ➕ {t('createAdmin')}
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('user')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('email')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('plan')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('sheets')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('payments')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('registration')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('role')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.subscription_plan === 'premium' ? 'bg-red-100 text-red-800' :
                            user.subscription_plan === 'pro' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {getPlanLabel(user.subscription_plan)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {user.sheet_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {user.payment_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {user.is_admin ? (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              👑 Admin
                            </span>
                          ) : (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              👤 User
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex space-x-2">
                            {!user.is_admin && (
                              <button
                                onClick={() => confirmDeleteUser(user)}
                                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                                title="Supprimer cet utilisateur"
                              >
                                🗑️ Supprimer
                              </button>
                            )}
                            {user.is_admin && (
                              <span className="text-xs text-gray-400 px-3 py-1">
                                Admin protégé
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Onglet Activité */}
          {activeAdminTab === 'activity' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-gray-900">Logs d'Activité</h3>
              
              {/* Sous-onglets pour les différents types d'activité */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8">
                  <button className="py-2 px-1 border-b-2 border-red-500 text-red-600 font-medium text-sm">
                    Tous les Logs
                  </button>
                </nav>
              </div>

              <div className="space-y-4">
                {activityLogs.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Aucun log d'activité trouvé.</p>
                ) : (
                  activityLogs.map((log) => (
                    <div key={log.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              log.action_type === 'account_deletion' ? 'bg-red-100 text-red-800' :
                              log.action_type === 'subscription_upgrade' ? 'bg-green-100 text-green-800' :
                              log.action_type === 'subscription_cancellation' ? 'bg-orange-100 text-orange-800' :
                              log.action_type === 'admin_creation' ? 'bg-purple-100 text-purple-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {log.action_type}
                            </span>
                            <span className="text-sm text-gray-500">{formatDate(log.created_at)}</span>
                          </div>
                          <p className="text-sm text-gray-900 mt-1">{log.description}</p>
                          {log.metadata && Object.keys(log.metadata).length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-gray-500 cursor-pointer">Détails</summary>
                              <pre className="text-xs text-gray-600 mt-1 bg-white p-2 rounded border">
                                {JSON.stringify(log.metadata, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Section Comptes Supprimés */}
              <div className="mt-8">
                <h4 className="text-lg font-semibold text-gray-800 mb-4">🗑️ Comptes Supprimés Récents</h4>
                <div className="space-y-3">
                  {deletedAccounts.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">Aucun compte supprimé récemment.</p>
                  ) : (
                    deletedAccounts.slice(0, 5).map((account) => (
                      <div key={account.id} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-medium text-red-900">{account.user_name}</span>
                            <span className="text-red-700 ml-2">({account.user_email})</span>
                          </div>
                          <div className="text-sm text-red-600">
                            {formatDate(account.deleted_at)}
                          </div>
                        </div>
                        {account.reason && (
                          <p className="text-sm text-red-800 mt-1">Raison: {account.reason}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Onglet Messages/Contacts */}
          {activeAdminTab === 'contacts' && (
            <div className="space-y-4 md:space-y-6 max-w-full">
              <h3 className="text-lg md:text-xl font-bold text-gray-900 break-words">{t('contactMessages')}</h3>
              
              <div className="space-y-3 md:space-y-4">
                {contacts.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">{t('noContacts')}</p>
                ) : (
                  contacts.map((contact) => (
                    <div key={contact.id} className="bg-white border border-gray-200 rounded-lg p-3 md:p-4 hover:shadow-md transition-shadow max-w-full overflow-hidden">
                      <div className="flex flex-col md:flex-row md:justify-between md:items-start">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-col md:flex-row md:items-center space-y-1 md:space-y-0 md:space-x-2 mb-2">
                            <h4 className="font-semibold text-gray-900 text-sm md:text-base truncate">{contact.subject}</h4>
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full w-fit flex-shrink-0 ${
                              contact.status === 'nouveau' ? 'bg-blue-100 text-blue-800' :
                              contact.status === 'lu' ? 'bg-yellow-100 text-yellow-800' :
                              contact.status === 'répondu' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {contact.status === 'nouveau' ? 'Nouveau' : 
                               contact.status === 'lu' ? 'Lu' : 
                               contact.status === 'répondu' ? 'Répondu' : contact.status}
                            </span>
                          </div>
                          <p className="text-xs md:text-sm text-gray-600 mb-2 break-words">
                            <span className="font-medium">De:</span> <span className="break-all">{contact.name} ({contact.email})</span>
                          </p>
                          <div className="bg-gray-50 p-2 md:p-3 rounded-md mb-3 max-w-full overflow-hidden">
                            <p className="text-xs md:text-sm text-gray-800 break-words">{contact.message}</p>
                          </div>
                          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
                            <p className="text-xs text-gray-500 break-words">
                              {formatDate(contact.created_at)}
                            </p>
                            <div className="flex justify-end flex-shrink-0">
                              <button
                                onClick={() => openReplyModal(contact)}
                                className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                              >
                                <svg className="w-3 h-3 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                                </svg>
                                {t('reply')}
                              </button>
                            </div>
                          </div>
                          {/* Afficher la réponse existante si elle existe */}
                          {contact.admin_reply && (
                            <div className="mt-3 p-2 md:p-3 bg-blue-50 border border-blue-200 rounded-md max-w-full overflow-hidden">
                              <p className="text-xs md:text-sm font-medium text-blue-900 mb-1 break-words">
                                📧 Votre réponse ({contact.replied_by}):
                              </p>
                              <p className="text-xs md:text-sm text-blue-800 break-words">{contact.admin_reply}</p>
                              <p className="text-xs text-blue-600 mt-1 break-words">
                                Répondu le {formatDate(contact.replied_at)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Onglet Témoignages */}
          {activeAdminTab === 'testimonials' && (
            <div className="space-y-4 md:space-y-6 max-w-full">
              <h3 className="text-lg md:text-xl font-bold text-gray-900 break-words">{t('testimonials')}</h3>
              
              <div className="space-y-3 md:space-y-4">
                {testimonials.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Aucun témoignage soumis.</p>
                ) : (
                  testimonials.map((testimonial) => (
                    <div key={testimonial.id} className="bg-white border border-gray-200 rounded-lg p-3 md:p-4 hover:shadow-md transition-shadow max-w-full overflow-hidden">
                      <div className="flex flex-col md:flex-row md:justify-between md:items-start">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-col md:flex-row md:items-center space-y-1 md:space-y-0 md:space-x-2 mb-2">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-semibold text-gray-900 text-sm md:text-base truncate">{testimonial.name}</h4>
                              <div className="flex items-center">
                                {[...Array(5)].map((_, i) => (
                                  <span key={i} className={`text-sm ${i < testimonial.rating ? 'text-yellow-400' : 'text-gray-300'}`}>★</span>
                                ))}
                                <span className="text-xs text-gray-500 ml-1">({testimonial.rating}/5)</span>
                              </div>
                            </div>
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full w-fit flex-shrink-0 ${
                              testimonial.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              testimonial.status === 'approved' ? 'bg-green-100 text-green-800' :
                              testimonial.status === 'rejected' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {testimonial.status === 'pending' ? 'En attente' : 
                               testimonial.status === 'approved' ? 'Approuvé' : 
                               testimonial.status === 'rejected' ? 'Rejeté' : testimonial.status}
                            </span>
                          </div>
                          <p className="text-xs md:text-sm text-gray-600 mb-2 break-words">
                            <span className="font-medium">Poste:</span> <span className="break-all">{testimonial.title}</span>
                          </p>
                          <div className="bg-gray-50 p-2 md:p-3 rounded-md mb-3 max-w-full overflow-hidden">
                            <p className="text-xs md:text-sm text-gray-800 break-words">{testimonial.comment}</p>
                          </div>
                          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
                            <p className="text-xs text-gray-500 break-words">
                              {formatDate(testimonial.created_at)}
                            </p>
                            <div className="flex flex-wrap gap-2 justify-end flex-shrink-0">
                              {testimonial.status === 'pending' && (
                                <>
                                  <button
                                    onClick={() => updateTestimonialStatus(testimonial.id, 'approved')}
                                    className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 transition-colors"
                                  >
                                    ✓ Approuver
                                  </button>
                                  <button
                                    onClick={() => updateTestimonialStatus(testimonial.id, 'rejected')}
                                    className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 transition-colors"
                                  >
                                    ✗ Rejeter
                                  </button>
                                </>
                              )}
                              <button
                                onClick={() => openTestimonialReplyModal(testimonial)}
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                              >
                                <svg className="w-3 h-3 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                                </svg>
                                {t('reply')}
                              </button>
                            </div>
                          </div>
                          {/* Afficher la réponse existante si elle existe */}
                          {testimonial.admin_reply && (
                            <div className="mt-3 p-2 md:p-3 bg-blue-50 border border-blue-200 rounded-md max-w-full overflow-hidden">
                              <p className="text-xs md:text-sm font-medium text-blue-900 mb-1 break-words">
                                📧 Votre réponse ({testimonial.replied_by}):
                              </p>
                              <p className="text-xs md:text-sm text-blue-800 break-words">{testimonial.admin_reply}</p>
                              <p className="text-xs text-blue-600 mt-1 break-words">
                                Répondu le {formatDate(testimonial.replied_at)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Onglet Prix */}
          {activeAdminTab === 'pricing' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">💰 Gestion des Prix</h3>
                <button
                  onClick={loadPlansConfig}
                  disabled={loadingPlansConfig}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  {loadingPlansConfig ? '⏳ Chargement...' : '🔄 Actualiser'}
                </button>
              </div>

              {/* Configuration des Plans */}
              <div className="grid gap-6 md:grid-cols-3">
                {plansConfig.map((plan) => (
                  <div key={plan.id} className="bg-white border rounded-lg p-6 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold capitalize text-gray-900">
                        {plan.plan_name === 'gratuit' && '🆓 Gratuit'}
                        {plan.plan_name === 'pro' && '⭐ Pro'}
                        {plan.plan_name === 'premium' && '👑 Premium'}
                      </h4>
                      <button
                        onClick={() => openPriceEditModal(plan)}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded text-sm"
                      >
                        ✏️ Modifier
                      </button>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Prix actuel:</span>
                        <span className="font-semibold text-green-600">
                          {plan.price === 0 ? 'Gratuit' : `${plan.price}€/mois`}
                        </span>
                      </div>
                      
                      {plan.promotion_active && (
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <div className="text-xs text-red-700">
                            🎯 Promotion active
                          </div>
                          {plan.original_price && (
                            <div className="text-sm">
                              <span className="line-through text-red-500">{plan.original_price}€</span>
                              <span className="text-green-600 font-semibold ml-2">{plan.price}€</span>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="text-sm text-gray-500">
                        <div>Fiches/mois: {plan.features?.sheets_per_month === -1 ? 'Illimitées' : plan.features?.sheets_per_month || 'N/A'}</div>
                        <div>IA: {plan.features?.ai_generation || 'N/A'}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Message si aucun plan */}  
              {plansConfig.length === 0 && !loadingPlansConfig && (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <div className="text-gray-500">
                    <div className="text-4xl mb-4">💰</div>
                    <h3 className="text-lg font-medium mb-2">Aucune configuration de prix trouvée</h3>
                    <p className="text-sm">Cliquez sur "Actualiser" pour charger ou créer les configurations par défaut.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Onglet Promotions */}
          {activeAdminTab === 'promotions' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">🎯 Gestion des Promotions</h3>
                <div className="space-x-2">
                  <button
                    onClick={loadPromotions}
                    disabled={loadingPromotions}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                  >
                    {loadingPromotions ? '⏳ Chargement...' : '🔄 Actualiser'}
                  </button>
                  <button
                    onClick={() => openPromotionModal()}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
                  >
                    ➕ Créer Promotion
                  </button>
                </div>
              </div>

              {/* Liste des Promotions */}
              <div className="space-y-4">
                {promotions.map((promotion) => (
                  <div key={promotion.id} className="bg-white border rounded-lg p-6 shadow-sm">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900">{promotion.title}</h4>
                        <p className="text-gray-600 text-sm">{promotion.description}</p>
                      </div>
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => openPromotionModal(promotion)}
                          className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded text-sm"
                        >
                          ✏️ Modifier
                        </button>
                        <button
                          onClick={() => deletePromotion(promotion.id)}
                          className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                        >
                          🗑️ Supprimer
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Réduction:</span>
                        <div className="text-green-600 font-semibold">
                          {promotion.discount_type === 'percentage' 
                            ? `${promotion.discount_value}%`
                            : `${promotion.discount_value}€`
                          }
                        </div>
                      </div>
                      
                      <div>
                        <span className="font-medium text-gray-700">Plans concernés:</span>
                        <div className="text-blue-600">
                          {promotion.target_plans.join(', ') || 'Aucun'}
                        </div>
                      </div>

                      <div>
                        <span className="font-medium text-gray-700">Statut:</span>
                        <div className={`font-semibold ${promotion.is_active ? 'text-green-600' : 'text-red-600'}`}>
                          {promotion.is_active ? '✅ Active' : '❌ Inactive'}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div>
                          <strong>Badge:</strong> {promotion.badge_text}
                        </div>
                        <div>
                          <strong>Période:</strong> {new Date(promotion.start_date).toLocaleDateString()} - {new Date(promotion.end_date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="mt-2">
                        <strong>Texte promotionnel:</strong> {promotion.promotional_text}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Message si aucune promotion */}
              {promotions.length === 0 && !loadingPromotions && (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <div className="text-gray-500">
                    <div className="text-4xl mb-4">🎯</div>
                    <h3 className="text-lg font-medium mb-2">Aucune promotion créée</h3>
                    <p className="text-sm">Créez votre première promotion pour commencer à offrir des réductions sur vos plans.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Onglet Affiliation */}
          {activeAdminTab === 'affiliates' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">🤝 Gestion des Affiliés</h3>
                <button
                  onClick={loadAffiliates}
                  disabled={loadingAffiliates}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  {loadingAffiliates ? '⏳ Chargement...' : '🔄 Actualiser'}
                </button>
              </div>

              {/* Statistiques des affiliés */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-600">{affiliateStats.total}</div>
                  <div className="text-sm text-blue-800">Total</div>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="text-2xl font-bold text-yellow-600">{affiliateStats.pending}</div>
                  <div className="text-sm text-yellow-800">En attente</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-600">{affiliateStats.approved}</div>
                  <div className="text-sm text-green-800">Approuvés</div>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="text-2xl font-bold text-red-600">{affiliateStats.rejected}</div>
                  <div className="text-sm text-red-800">Rejetés</div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-600">{affiliateStats.suspended}</div>
                  <div className="text-sm text-gray-800">Suspendus</div>
                </div>
              </div>

              {/* Filtres */}
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex flex-wrap gap-4 items-center">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                    <select
                      value={affiliateFilters.status}
                      onChange={(e) => setAffiliateFilters(prev => ({ ...prev, status: e.target.value, page: 1 }))}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">Tous</option>
                      <option value="pending">En attente</option>
                      <option value="approved">Approuvés</option>
                      <option value="rejected">Rejetés</option>
                      <option value="suspended">Suspendus</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Recherche</label>
                    <input
                      type="text"
                      value={affiliateFilters.search}
                      onChange={(e) => setAffiliateFilters(prev => ({ ...prev, search: e.target.value, page: 1 }))}
                      placeholder="Nom, email, code..."
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Liste des affiliés */}
              {loadingAffiliates ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Chargement des affiliés...</p>
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Affilié</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stats</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Gains</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inscription</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {affiliates
                          .filter(affiliate => 
                            affiliateFilters.search === '' || 
                            affiliate.name.toLowerCase().includes(affiliateFilters.search.toLowerCase()) ||
                            affiliate.email.toLowerCase().includes(affiliateFilters.search.toLowerCase()) ||
                            affiliate.affiliate_code.toLowerCase().includes(affiliateFilters.search.toLowerCase())
                          )
                          .map((affiliate) => (
                          <tr key={affiliate.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <div className="text-sm font-medium text-gray-900">{affiliate.name}</div>
                                <div className="text-sm text-gray-500">{affiliate.email}</div>
                                {affiliate.company && (
                                  <div className="text-xs text-gray-400">{affiliate.company}</div>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {affiliate.affiliate_code}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(affiliate.status)}`}>
                                {getStatusLabel(affiliate.status)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              <div className="space-y-1">
                                <div>👆 {affiliate.total_clicks} clics</div>
                                <div>🎯 {affiliate.total_conversions} conversions</div>
                                <div>📈 {affiliate.total_clicks > 0 ? ((affiliate.total_conversions / affiliate.total_clicks) * 100).toFixed(1) : 0}%</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                              {affiliate.total_earnings?.toFixed(2) || '0.00'}€
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(affiliate.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                              <button
                                onClick={() => loadAffiliateDetails(affiliate.id)}
                                className="text-blue-600 hover:text-blue-900 font-medium"
                              >
                                👁️ Détails
                              </button>
                              
                              {affiliate.status === 'pending' && (
                                <>
                                  <button
                                    onClick={() => updateAffiliateStatus(affiliate.id, 'approved')}
                                    disabled={updatingAffiliateStatus}
                                    className="text-green-600 hover:text-green-900 font-medium disabled:opacity-50"
                                  >
                                    ✅ Approuver
                                  </button>
                                  <button
                                    onClick={() => updateAffiliateStatus(affiliate.id, 'rejected')}
                                    disabled={updatingAffiliateStatus}
                                    className="text-red-600 hover:text-red-900 font-medium disabled:opacity-50"
                                  >
                                    ❌ Rejeter
                                  </button>
                                </>
                              )}
                              
                              {affiliate.status === 'approved' && (
                                <button
                                  onClick={() => updateAffiliateStatus(affiliate.id, 'suspended')}
                                  disabled={updatingAffiliateStatus}
                                  className="text-orange-600 hover:text-orange-900 font-medium disabled:opacity-50"
                                >
                                  ⏸️ Suspendre
                                </button>
                              )}
                              
                              {affiliate.status === 'suspended' && (
                                <button
                                  onClick={() => updateAffiliateStatus(affiliate.id, 'approved')}
                                  disabled={updatingAffiliateStatus}
                                  className="text-green-600 hover:text-green-900 font-medium disabled:opacity-50"
                                >
                                  ▶️ Réactiver
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Message si aucun affilié */}
                  {affiliates.length === 0 && (
                    <div className="text-center py-8">
                      <div className="text-gray-500">
                        <div className="text-4xl mb-4">🤝</div>
                        <h3 className="text-lg font-medium mb-2">Aucun affilié</h3>
                        <p className="text-sm">Les nouveaux affiliés apparaîtront ici après leur inscription.</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

        </div>
      </div>

      {/* Modal Création Admin */}
      {showCreateAdminModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Créer un Compte Administrateur</h3>
            
            <form onSubmit={(e) => { e.preventDefault(); createNewAdmin(); }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  required
                  value={newAdminForm.email}
                  onChange={(e) => setNewAdminForm({...newAdminForm, email: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500"
                  placeholder="admin@example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Nom</label>
                <input
                  type="text"
                  required
                  value={newAdminForm.name}
                  onChange={(e) => setNewAdminForm({...newAdminForm, name: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500"
                  placeholder="Nom de l'administrateur"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
                <input
                  type="password"
                  required
                  minLength="8"
                  value={newAdminForm.password}
                  onChange={(e) => setNewAdminForm({...newAdminForm, password: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500"
                  placeholder="Mot de passe sécurisé"
                />
              </div>
              
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateAdminModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
                >
                  Créer Admin
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Réponse aux Contacts */}
      {showReplyModal && selectedContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-4 md:p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-base md:text-lg font-bold text-gray-900 pr-2 break-words flex-1">
                {t('replyTo')}: "{selectedContact.subject}"
              </h3>
              <button
                onClick={closeReplyModal}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2"
              >
                <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Message original */}
            <div className="mb-4 md:mb-6 p-3 md:p-4 bg-gray-50 rounded-lg border max-w-full overflow-hidden">
              <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-2 space-y-1 md:space-y-0">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900 text-sm md:text-base break-words">{selectedContact.name}</p>
                  <p className="text-xs md:text-sm text-gray-600 break-all">{selectedContact.email}</p>
                </div>
                <p className="text-xs text-gray-500 flex-shrink-0">{formatDate(selectedContact.created_at)}</p>
              </div>
              <div className="mt-3">
                <p className="text-xs md:text-sm font-medium text-gray-700 mb-1">Message original:</p>
                <p className="text-xs md:text-sm text-gray-800 bg-white p-2 md:p-3 rounded border break-words max-w-full overflow-hidden">{selectedContact.message}</p>
              </div>
            </div>

            {/* Réponse existante (si applicable) */}
            {selectedContact.admin_reply && (
              <div className="mb-4 md:mb-6 p-3 md:p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-full overflow-hidden">
                <p className="text-xs md:text-sm font-medium text-blue-900 mb-2 break-words">
                  Réponse existante (par {selectedContact.replied_by} le {formatDate(selectedContact.replied_at)}):
                </p>
                <p className="text-xs md:text-sm text-blue-800 bg-white p-2 md:p-3 rounded border break-words max-w-full overflow-hidden">{selectedContact.admin_reply}</p>
              </div>
            )}

            {/* Formulaire de réponse */}
            <form onSubmit={sendReply} className="space-y-4">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">
                  {selectedContact.admin_reply ? 'Nouvelle réponse:' : 'Votre réponse:'}
                </label>
                <textarea
                  value={replyForm.message}
                  onChange={(e) => setReplyForm({...replyForm, message: e.target.value})}
                  rows={6}
                  className="w-full px-2 md:px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm resize-none max-w-full"
                  placeholder="Tapez votre réponse ici..."
                  required
                />
              </div>

              <div className="flex flex-col md:flex-row justify-end space-y-2 md:space-y-0 md:space-x-3">
                <button
                  type="button"
                  onClick={closeReplyModal}
                  className="w-full md:w-auto px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  disabled={sendingReply}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={sendingReply || !replyForm.message.trim()}
                  className="w-full md:w-auto px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sendingReply ? (
                    <div className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Envoi...
                    </div>
                  ) : (
                    'Envoyer la réponse'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Réponse aux Témoignages */}
      {showTestimonialReplyModal && selectedTestimonial && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-4 md:p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-base md:text-lg font-bold text-gray-900 pr-2 break-words flex-1">
                {t('replyTo')} témoignage: "{selectedTestimonial.name}"
              </h3>
              <button
                onClick={closeTestimonialReplyModal}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2"
              >
                <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Témoignage original */}
            <div className="mb-4 md:mb-6 p-3 md:p-4 bg-gray-50 rounded-lg border max-w-full overflow-hidden">
              <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-2 space-y-1 md:space-y-0">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <p className="font-medium text-gray-900 text-sm md:text-base break-words">{selectedTestimonial.name}</p>
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <span key={i} className={`text-sm ${i < selectedTestimonial.rating ? 'text-yellow-400' : 'text-gray-300'}`}>★</span>
                      ))}
                      <span className="text-xs text-gray-500 ml-1">({selectedTestimonial.rating}/5)</span>
                    </div>
                  </div>
                  <p className="text-xs md:text-sm text-gray-600 break-all">{selectedTestimonial.title}</p>
                </div>
                <p className="text-xs text-gray-500 flex-shrink-0">{formatDate(selectedTestimonial.created_at)}</p>
              </div>
              <div className="mt-3">
                <p className="text-xs md:text-sm font-medium text-gray-700 mb-1">Témoignage original:</p>
                <p className="text-xs md:text-sm text-gray-800 bg-white p-2 md:p-3 rounded border break-words max-w-full overflow-hidden">{selectedTestimonial.comment}</p>
              </div>
            </div>

            {/* Réponse existante (si applicable) */}
            {selectedTestimonial.admin_reply && (
              <div className="mb-4 md:mb-6 p-3 md:p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-full overflow-hidden">
                <p className="text-xs md:text-sm font-medium text-blue-900 mb-2 break-words">
                  Réponse existante (par {selectedTestimonial.replied_by} le {formatDate(selectedTestimonial.replied_at)}):
                </p>
                <p className="text-xs md:text-sm text-blue-800 bg-white p-2 md:p-3 rounded border break-words max-w-full overflow-hidden">{selectedTestimonial.admin_reply}</p>
              </div>
            )}

            {/* Formulaire de réponse */}
            <form onSubmit={sendTestimonialReply} className="space-y-4">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">
                  {selectedTestimonial.admin_reply ? 'Nouvelle réponse:' : 'Votre réponse:'}
                </label>
                <textarea
                  value={testimonialReplyForm.message}
                  onChange={(e) => setTestimonialReplyForm({...testimonialReplyForm, message: e.target.value})}
                  rows={6}
                  className="w-full px-2 md:px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm resize-none max-w-full"
                  placeholder="Tapez votre réponse au témoignage..."
                  required
                />
              </div>

              <div className="flex flex-col md:flex-row justify-end space-y-2 md:space-y-0 md:space-x-3">
                <button
                  type="button"
                  onClick={closeTestimonialReplyModal}
                  className="w-full md:w-auto px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  disabled={sendingTestimonialReply}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={sendingTestimonialReply || !testimonialReplyForm.message.trim()}
                  className="w-full md:w-auto px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sendingTestimonialReply ? (
                    <div className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Envoi...
                    </div>
                  ) : (
                    'Envoyer la réponse'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Suppression Utilisateur */}
      {showDeleteUserModal && userToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold text-red-600 mb-4">⚠️ Confirmer la Suppression</h3>
            
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800 mb-2">
                  <strong>Attention :</strong> Cette action est irréversible !
                </p>
                <p className="text-sm text-gray-700">
                  Vous êtes sur le point de supprimer définitivement le compte de :
                </p>
                <div className="mt-3 bg-white p-3 rounded border">
                  <div className="font-medium text-gray-900">{userToDelete.name}</div>
                  <div className="text-sm text-gray-600">{userToDelete.email}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Plan : {getPlanLabel(userToDelete.subscription_plan)} | 
                    {userToDelete.sheet_count || 0} fiches créées
                  </div>
                </div>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-xs text-yellow-800">
                  📋 <strong>Données supprimées :</strong> Compte utilisateur, fiches produits, 
                  historique de paiements, données de session, configurations personnalisées.
                </p>
              </div>
              
              <div className="flex justify-between space-x-3">
                <button
                  onClick={closeDeleteUserModal}
                  disabled={deletingUser}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 disabled:opacity-50"
                >
                  Annuler
                </button>
                <button
                  onClick={deleteUser}
                  disabled={deletingUser}
                  className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deletingUser ? '⏳ Suppression...' : '🗑️ Supprimer Définitivement'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Détails Affilié */}
      {showAffiliateDetailsModal && affiliateDetailsData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-6xl max-h-[95vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">
                🤝 Détails de l'Affilié - {affiliateDetailsData.affiliate.name}
              </h3>
              <button
                onClick={closeAffiliateDetailsModal}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Informations personnelles */}
              <div className="lg:col-span-1">
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">📋 Informations</h4>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-600">Code d'affiliation:</span>
                      <div className="text-lg font-mono bg-blue-100 text-blue-800 px-2 py-1 rounded mt-1">
                        {affiliateDetailsData.affiliate.affiliate_code}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Email:</span>
                      <div className="text-gray-900">{affiliateDetailsData.affiliate.email}</div>
                    </div>
                    {affiliateDetailsData.affiliate.company && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Entreprise:</span>
                        <div className="text-gray-900">{affiliateDetailsData.affiliate.company}</div>
                      </div>
                    )}
                    {affiliateDetailsData.affiliate.website && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Site web:</span>
                        <div className="text-blue-600">
                          <a href={affiliateDetailsData.affiliate.website} target="_blank" rel="noopener noreferrer">
                            {affiliateDetailsData.affiliate.website}
                          </a>
                        </div>
                      </div>
                    )}
                    <div>
                      <span className="text-sm font-medium text-gray-600">Statut:</span>
                      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${getStatusBadgeClass(affiliateDetailsData.affiliate.status)}`}>
                        {getStatusLabel(affiliateDetailsData.affiliate.status)}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Inscription:</span>
                      <div className="text-gray-900">{new Date(affiliateDetailsData.affiliate.created_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                </div>

                {/* Statistiques résumées */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">📊 Résumé</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{affiliateDetailsData.affiliate.total_clicks}</div>
                      <div className="text-xs text-gray-600">Clics Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{affiliateDetailsData.affiliate.total_conversions}</div>
                      <div className="text-xs text-gray-600">Conversions</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {affiliateDetailsData.affiliate.total_clicks > 0 ? 
                          ((affiliateDetailsData.affiliate.total_conversions / affiliateDetailsData.affiliate.total_clicks) * 100).toFixed(1) : 0}%
                      </div>
                      <div className="text-xs text-gray-600">Taux Conv.</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{affiliateDetailsData.affiliate.total_earnings.toFixed(2)}€</div>
                      <div className="text-xs text-gray-600">Gains Total</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Données détaillées */}
              <div className="lg:col-span-2">
                {/* Onglets pour les différentes vues */}
                <div className="mb-4">
                  <nav className="flex space-x-4">
                    <button className="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-lg">
                      👆 Clics ({affiliateDetailsData.clicks?.length || 0})
                    </button>
                    <button className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900">
                      🎯 Conversions ({affiliateDetailsData.conversions?.length || 0})
                    </button>
                    <button className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900">
                      💰 Commissions ({affiliateDetailsData.commissions?.length || 0})
                    </button>
                  </nav>
                </div>

                {/* Tableau des clics récents */}
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <h5 className="text-sm font-medium text-gray-900">Clics Récents</h5>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Page</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Converti</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {affiliateDetailsData.clicks?.slice(0, 10).map((click, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              {new Date(click.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">
                              {click.landing_page}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                              {click.utm_source || 'Direct'}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm">
                              {click.converted ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  ✅ Oui
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                  ⏳ Non
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {(!affiliateDetailsData.clicks || affiliateDetailsData.clicks.length === 0) && (
                    <div className="text-center py-6 text-gray-500">
                      <div className="text-2xl mb-2">👆</div>
                      <p>Aucun clic enregistré</p>
                    </div>
                  )}
                </div>

                {/* Conversions récentes */}
                {affiliateDetailsData.conversions?.length > 0 && (
                  <div className="mt-6 bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <div className="px-4 py-3 bg-green-50 border-b border-gray-200">
                      <h5 className="text-sm font-medium text-gray-900">🎯 Conversions Récentes</h5>
                    </div>
                    <div className="p-4">
                      <div className="space-y-3">
                        {affiliateDetailsData.conversions.slice(0, 5).map((conversion, index) => (
                          <div key={index} className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                            <div>
                              <div className="font-medium text-gray-900">Plan {conversion.subscription_plan}</div>
                              <div className="text-sm text-gray-600">{conversion.user_email}</div>
                              <div className="text-xs text-gray-500">{new Date(conversion.created_at).toLocaleDateString()}</div>
                            </div>
                            <div className="text-right">
                              <div className="font-bold text-green-600">+{conversion.commission_amount.toFixed(2)}€</div>
                              <div className="text-xs text-gray-500">{conversion.commission_rate}% de {conversion.subscription_amount}€</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={closeAffiliateDetailsModal}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

          {/* ✅ NOUVEAU: Onglet PriceTruth */}
          {activeAdminTab === 'price-truth' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">🔍 Administration PriceTruth</h3>
                <button
                  onClick={async () => {
                    setRefreshingPrices(true);
                    try {
                      await axios.post(`${API}/price-truth/refresh`);
                      // Recharger les stats après le refresh
                      const statsResponse = await axios.get(`${API}/price-truth/stats`);
                      setPriceTruthStats(statsResponse.data);
                    } catch (error) {
                      console.error('Erreur refresh global:', error);
                    } finally {
                      setRefreshingPrices(false);
                    }
                  }}
                  disabled={refreshingPrices}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-medium flex items-center"
                >
                  {refreshingPrices ? (
                    <>
                      <svg className="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Actualisation...
                    </>
                  ) : (
                    <>
                      🔄 Actualiser tous les prix
                    </>
                  )}
                </button>
              </div>

              {/* Health Status */}
              <div className="bg-white rounded-lg border p-4">
                <h4 className="font-semibold text-gray-900 mb-3">📊 État du Système</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="text-green-800 font-medium">🟢 Service Status</div>
                    <div className="text-green-600 text-sm mt-1">
                      {priceTruthHealth?.status === 'healthy' ? 'Opérationnel' : 'Vérification...'}
                    </div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-blue-800 font-medium">🔌 Sources Actives</div>
                    <div className="text-blue-600 text-sm mt-1">
                      {priceTruthHealth?.adapters_count || 4} sources disponibles
                    </div>
                    <div className="text-xs text-blue-500 mt-1">Amazon, Google Shopping, Cdiscount, Fnac</div>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <div className="text-purple-800 font-medium">⚙️ Configuration</div>
                    <div className="text-purple-600 text-sm mt-1">
                      TTL: {priceTruthStats?.ttl_hours || 6}h - Tolérance: {priceTruthStats?.consensus_tolerance_pct || 3}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Statistiques */}
              <div className="bg-white rounded-lg border p-4">
                <h4 className="font-semibold text-gray-900 mb-3">📈 Statistiques</h4>
                {loadingPriceTruthStats ? (
                  <div className="text-center py-4">
                    <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-gray-600 mt-2">Chargement des statistiques...</p>
                  </div>
                ) : priceTruthStats ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-gray-800 font-medium">📊 Requêtes Totales</div>
                      <div className="text-2xl font-bold text-gray-900">{priceTruthStats.stats?.total_queries || 0}</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3">
                      <div className="text-green-800 font-medium">✅ Consensus Réussis</div>
                      <div className="text-2xl font-bold text-green-600">{priceTruthStats.stats?.successful_consensus || 0}</div>
                      <div className="text-xs text-green-600">{priceTruthStats.stats?.success_rate || '0%'}</div>
                    </div>
                    <div className="bg-red-50 rounded-lg p-3">
                      <div className="text-red-800 font-medium">❌ Consensus Échoués</div>
                      <div className="text-2xl font-bold text-red-600">{priceTruthStats.stats?.failed_consensus || 0}</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="text-blue-800 font-medium">💾 Cache</div>
                      <div className="text-2xl font-bold text-blue-600">{priceTruthStats.stats?.cache_hits || 0}</div>
                      <div className="text-xs text-blue-600">{priceTruthStats.stats?.cache_rate || '0%'}</div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-800">⚠️ Impossible de charger les statistiques PriceTruth</p>
                    <button
                      onClick={async () => {
                        setLoadingPriceTruthStats(true);
                        try {
                          const [statsResponse, healthResponse] = await Promise.all([
                            axios.get(`${API}/price-truth/stats`),
                            axios.get(`${API}/price-truth/health`)
                          ]);
                          setPriceTruthStats(statsResponse.data);
                          setPriceTruthHealth(healthResponse.data);
                        } catch (error) {
                          console.error('Erreur chargement PriceTruth:', error);
                        } finally {
                          setLoadingPriceTruthStats(false);
                        }
                      }}
                      className="mt-2 bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                    >
                      🔄 Réessayer
                    </button>
                  </div>
                )}
              </div>

              {/* Guide d'utilisation */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-3">📚 Guide PriceTruth</h4>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>🎯 Fonction :</strong> Vérifie automatiquement les prix depuis 4 sources (Amazon, Google Shopping, Cdiscount, Fnac)</p>
                  <p><strong>✅ Consensus :</strong> Valide un prix si ≥2 sources concordent (tolérance 3%)</p>
                  <p><strong>🕒 Cache :</strong> Données valides pendant 6h pour optimiser les performances</p>
                  <p><strong>📸 Audit :</strong> Screenshots automatiques pour chaque extraction</p>
                  <p><strong>🛡️ Sécurité :</strong> Respecte les ToS avec throttling 1.5 req/s par domaine</p>
                </div>
              </div>
            </div>
          )}

          {/* Onglet Configuration Affiliation */}
          {activeAdminTab === 'affiliate-config' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">⚙️ Configuration du Programme d'Affiliation</h3>
                <button
                  onClick={() => setShowAffiliateConfigModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
                >
                  ✏️ Modifier la Configuration
                </button>
              </div>

              {loadingAffiliateConfig ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : affiliateConfig ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Commissions */}
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">💰 Commissions</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Plan Pro:</span>
                        <span className="font-bold text-blue-600">{affiliateConfig.default_commission_rate_pro}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Plan Premium:</span>
                        <span className="font-bold text-purple-600">{affiliateConfig.default_commission_rate_premium}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Type:</span>
                        <span className="font-medium">{affiliateConfig.commission_type === 'recurring' ? 'Récurrente' : 'Unique'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Paiements */}
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">💳 Paiements</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Fréquence:</span>
                        <span className="font-medium capitalize">{affiliateConfig.payment_frequency}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Minimum:</span>
                        <span className="font-bold text-green-600">{affiliateConfig.minimum_payout}€</span>
                      </div>
                    </div>
                  </div>

                  {/* Paramètres du Programme */}
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Programme</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Activé:</span>
                        <span className={`px-2 py-1 rounded text-sm font-medium ${
                          affiliateConfig.program_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {affiliateConfig.program_enabled ? '✅ Oui' : '❌ Non'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Auto-approbation:</span>
                        <span className={`px-2 py-1 rounded text-sm font-medium ${
                          affiliateConfig.auto_approval ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {affiliateConfig.auto_approval ? '✅ Oui' : '⏳ Manuel'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Durée cookie:</span>
                        <span className="font-medium">{affiliateConfig.cookie_duration_days} jours</span>
                      </div>
                    </div>
                  </div>

                  {/* Message de bienvenue */}
                  <div className="bg-white p-6 rounded-lg shadow md:col-span-2 lg:col-span-3">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">💬 Message de Bienvenue</h4>
                    <p className="text-gray-700 bg-gray-50 p-4 rounded border-l-4 border-blue-500">
                      "{affiliateConfig.welcome_message}"
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-500 mb-4">
                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <p className="text-gray-500">Aucune configuration trouvée</p>
                  <button
                    onClick={() => setShowAffiliateConfigModal(true)}
                    className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                  >
                    Créer la Configuration
                  </button>
                </div>
              )}
            </div>
          )}

      {/* Modal Modification Prix */}
      {showPriceEditModal && selectedPlanForEdit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto relative">
            <button
              onClick={closePriceEditModal}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
            
            <h3 className="text-xl font-bold text-gray-900 mb-6">
              ✏️ Modifier le Prix - {selectedPlanForEdit.plan_name.charAt(0).toUpperCase() + selectedPlanForEdit.plan_name.slice(1)}
            </h3>

            <form onSubmit={savePlanPrice} className="space-y-6">
              {/* Prix actuel */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prix actuel* (€)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={priceEditForm.price}
                  onChange={(e) => setPriceEditForm(prev => ({ ...prev, price: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Prix actuel"
                />
              </div>

              {/* Prix original (optionnel) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prix original (€) - optionnel
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={priceEditForm.original_price}
                  onChange={(e) => setPriceEditForm(prev => ({ ...prev, original_price: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Prix original (pour promotions)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Si renseigné, sera affiché barré avec le prix actuel en promotion
                </p>
              </div>

              {/* Boutons d'action */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closePriceEditModal}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={savingPrice}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
                >
                  {savingPrice ? '⏳ Enregistrement...' : '💾 Enregistrer les Modifications'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Promotion */}
      {showPromotionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">
                {selectedPromotionForEdit ? '🎯 Modifier la Promotion' : '🎯 Créer une Nouvelle Promotion'}
              </h3>
              <button
                onClick={closePromotionModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={savePromotion} className="space-y-6">
              {/* Titre de la promotion */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Titre de la promotion*
                </label>
                <input
                  type="text"
                  required
                  value={promotionForm.title}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Offre de lancement Pro"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  rows="3"
                  value={promotionForm.description}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Description détaillée de la promotion..."
                />
              </div>

              {/* Plans concernés */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Plans concernés*
                </label>
                <div className="space-y-2">
                  {['gratuit', 'pro', 'premium'].map(plan => (
                    <label key={plan} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={promotionForm.target_plans.includes(plan)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPromotionForm(prev => ({
                              ...prev,
                              target_plans: [...prev.target_plans, plan]
                            }));
                          } else {
                            setPromotionForm(prev => ({
                              ...prev,
                              target_plans: prev.target_plans.filter(p => p !== plan)
                            }));
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="capitalize">{plan}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Type de remise */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type de remise*
                </label>
                <select
                  value={promotionForm.discount_type}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, discount_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="percentage">Pourcentage (%)</option>
                  <option value="fixed">Montant fixe (€)</option>
                </select>
              </div>

              {/* Valeur de la remise */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Valeur de la remise*
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={promotionForm.discount_value}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, discount_value: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder={promotionForm.discount_type === 'percentage' ? 'Ex: 20' : 'Ex: 10.00'}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {promotionForm.discount_type === 'percentage' 
                    ? 'Pourcentage de réduction (sans le symbole %)' 
                    : 'Montant en euros à déduire'
                  }
                </p>
              </div>

              {/* Badge promotionnel */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Badge promotionnel
                </label>
                <input
                  type="text"
                  value={promotionForm.badge_text}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, badge_text: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: PROMO-20, LANCEMENT, SPECIAL"
                />
              </div>

              {/* Texte promotionnel */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Texte promotionnel
                </label>
                <input
                  type="text"
                  value={promotionForm.promotional_text}
                  onChange={(e) => setPromotionForm(prev => ({ ...prev, promotional_text: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Offre limitée dans le temps !"
                />
              </div>

              {/* Dates */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date de début*
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={promotionForm.start_date}
                    onChange={(e) => setPromotionForm(prev => ({ ...prev, start_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date de fin*
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={promotionForm.end_date}
                    onChange={(e) => setPromotionForm(prev => ({ ...prev, end_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Promotion active */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={promotionForm.is_active}
                    onChange={(e) => setPromotionForm(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Promotion active</span>
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Décochez pour créer une promotion en brouillon
                </p>
              </div>

              {/* Boutons d'action */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={closePromotionModal}
                  disabled={savingPromotion}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 disabled:opacity-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={savingPromotion}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {savingPromotion ? '⏳ Enregistrement...' : (selectedPromotionForEdit ? '💾 Modifier' : '🎯 Créer')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Configuration d'Affiliation */}
      {showAffiliateConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">⚙️ Configuration du Programme d'Affiliation</h3>
              <button
                onClick={() => setShowAffiliateConfigModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSaveAffiliateConfig(); }} className="space-y-6">
              {/* Section Commissions */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">💰 Commissions</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Taux Pro (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={affiliateConfigForm.default_commission_rate_pro}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        default_commission_rate_pro: parseFloat(e.target.value) || 0
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Taux Premium (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={affiliateConfigForm.default_commission_rate_premium}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        default_commission_rate_premium: parseFloat(e.target.value) || 0
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Type de Commission
                    </label>
                    <select
                      value={affiliateConfigForm.commission_type}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        commission_type: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="one_time">Unique</option>
                      <option value="recurring">Récurrente</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Section Paiements */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">💳 Paiements</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Fréquence de Paiement
                    </label>
                    <select
                      value={affiliateConfigForm.payment_frequency}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        payment_frequency: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="weekly">Hebdomadaire</option>
                      <option value="monthly">Mensuel</option>
                      <option value="quarterly">Trimestriel</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum de Paiement (€)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={affiliateConfigForm.minimum_payout}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        minimum_payout: parseFloat(e.target.value) || 0
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Section Paramètres */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Paramètres</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="program_enabled"
                      checked={affiliateConfigForm.program_enabled}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        program_enabled: e.target.checked
                      })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="program_enabled" className="ml-2 block text-sm text-gray-900">
                      Programme Activé
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="auto_approval"
                      checked={affiliateConfigForm.auto_approval}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        auto_approval: e.target.checked
                      })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="auto_approval" className="ml-2 block text-sm text-gray-900">
                      Auto-approbation
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Durée Cookie (jours)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={affiliateConfigForm.cookie_duration_days}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        cookie_duration_days: parseInt(e.target.value) || 30
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Section Messages */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">💬 Messages</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Message de Bienvenue
                    </label>
                    <textarea
                      rows="3"
                      value={affiliateConfigForm.welcome_message}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        welcome_message: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Message affiché aux nouveaux affiliés..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Conditions Générales
                    </label>
                    <textarea
                      rows="4"
                      value={affiliateConfigForm.terms_and_conditions}
                      onChange={(e) => setAffiliateConfigForm({
                        ...affiliateConfigForm,
                        terms_and_conditions: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Conditions générales du programme d'affiliation..."
                    />
                  </div>
                </div>
              </div>

              {/* Boutons d'action */}
              <div className="flex justify-between items-center pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowAffiliateConfigModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Annuler
                </button>
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={applyConfigToExistingAffiliates}
                    disabled={loadingAffiliateConfig}
                    className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50"
                  >
                    🔄 Appliquer aux Affiliés Existants
                  </button>
                  <button
                    type="submit"
                    disabled={loadingAffiliateConfig}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loadingAffiliateConfig ? '⏳ Enregistrement...' : '💾 Sauvegarder'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Protected Route Wrapper for integrations
const ProtectedIntegrationRoute = ({ children }) => {
  const { user, loading, token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && (!user || !token)) {
      // Redirect to home with a message to login
      navigate('/', { replace: true });
    }
  }, [user, loading, token, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user || !token) {
    return null; // Will redirect
  }

  return React.cloneElement(children, { user, token });
};

// Dashboard Component
const Dashboard = ({ onGoToHome, affiliateConfig, loadingAffiliateConfig, loadAffiliateConfig }) => {
  const { logout, user, setUser, token } = useAuth();
  const { t, currentLanguage } = useLanguage();
  const [activeTab, setActiveTab] = useState('generator');
  const [notification, setNotification] = useState(null);
  
  // Debug effect pour surveiller les changements d'activeTab
  useEffect(() => {
    console.log('🔄 activeTab changé vers:', activeTab);
    if (activeTab === 'subscription') {
      console.log('✅ Onglet Subscription activé - le contenu devrait s\'afficher');
    }
  }, [activeTab]);
  const [sheets, setSheets] = useState([]);
  const [stats, setStats] = useState(null);
  const [lastStatsUpdate, setLastStatsUpdate] = useState(null);
  const [detailedAnalytics, setDetailedAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generatorForm, setGeneratorForm] = useState({ 
    product_name: '', 
    product_description: '', 
    number_of_images: 1,
    category: '',
    custom_category: '',
    use_case: '',  // Nouveau champ pour le scénario d'usage
    image_style: 'studio'  // Nouveau champ pour le style d'image
  });
  const [generatedSheet, setGeneratedSheet] = useState(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedUpgradePlan, setSelectedUpgradePlan] = useState('');
  const [showUpgradeSuccess, setShowUpgradeSuccess] = useState(false);
  const [showDashboardHelp, setShowDashboardHelp] = useState(false);
  
  // CONTENTANALYTICS FEEDBACK SYSTEM STATES
  const [feedbackSubmitting, setFeedbackSubmitting] = useState({});
  const [feedbackSubmitted, setFeedbackSubmitted] = useState({});
  
  // PREMIUM FEATURES STATES
  
  // AI Features States
  const [aiFeatures, setAiFeatures] = useState(null);
  const [seoAnalysisForm, setSeoAnalysisForm] = useState({
    product_name: '',
    product_description: '',
    target_keywords: '',
    target_audience: '',
    language: 'fr'
  });
  const [seoAnalysisResult, setSeoAnalysisResult] = useState(null);
  const [seoAnalysisLoading, setSeoAnalysisLoading] = useState(false);
  
  const [competitorAnalysisForm, setCompetitorAnalysisForm] = useState({
    product_name: '',
    category: '',
    competitor_urls: '',
    analysis_depth: 'standard',
    language: 'fr'
  });
  const [competitorAnalysisResult, setCompetitorAnalysisResult] = useState(null);
  const [competitorAnalysisLoading, setCompetitorAnalysisLoading] = useState(false);
  
  const [priceOptimizationForm, setPriceOptimizationForm] = useState({
    product_name: '',
    current_price: '',
    cost_price: '',
    target_margin: 30,
    competitor_prices: '',
    market_segment: 'mid-range',
    pricing_strategy: 'competitive'
  });
  const [priceOptimizationResult, setPriceOptimizationResult] = useState(null);
  const [priceOptimizationLoading, setPriceOptimizationLoading] = useState(false);
  
  const [translationForm, setTranslationForm] = useState({
    source_text: '',
    source_language: 'fr',
    target_languages: ['en'],
    content_type: 'product_description',
    preserve_keywords: ''
  });
  const [translationResult, setTranslationResult] = useState(null);
  const [translationLoading, setTranslationLoading] = useState(false);
  
  const [variantsForm, setVariantsForm] = useState({
    base_product: '',
    base_description: '',
    variant_types: ['color', 'size'],
    number_of_variants: 3,
    target_audience: '',
    price_range: { min: 20, max: 100 }
  });
  const [variantsResult, setVariantsResult] = useState(null);
  const [variantsLoading, setVariantsLoading] = useState(false);
  
  // E-commerce Integrations States
  const [connectedStores, setConnectedStores] = useState([]);
  const [integrationLogs, setIntegrationLogs] = useState([]);
  const [showConnectStoreModal, setShowConnectStoreModal] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [amazonConnectionStatus, setAmazonConnectionStatus] = useState('none'); // 'none', 'connected', 'revoked'
  const [storeConnectionForm, setStoreConnectionForm] = useState({});
  const [connectingStore, setConnectingStore] = useState(false);
  
  // Premium Analytics States
  const [productPerformance, setProductPerformance] = useState(null);
  const [integrationPerformance, setIntegrationPerformance] = useState(null);
  const [userEngagement, setUserEngagement] = useState(null);
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState('30d');
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  
  // SEO Premium States
  const [seoConfig, setSeoConfig] = useState(null);
  const [seoAnalytics, setSeoAnalytics] = useState(null);
  const [seoOptimizations, setSeoOptimizations] = useState([]);
  const [seoTrends, setSeoTrends] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  const [loadingSEO, setLoadingSEO] = useState(false);
  const [activeSEOTab, setActiveSEOTab] = useState('dashboard');

  // SEO Connection Management States
  const [connectionsStatus, setConnectionsStatus] = useState({});
  const [loadingConnections, setLoadingConnections] = useState(false);
  const [seoSetupValidation, setSeoSetupValidation] = useState(null);
  const [showWebhookGuide, setShowWebhookGuide] = useState(false);
  const [selectedWebhookPlatform, setSelectedWebhookPlatform] = useState('');
  const [webhookGuide, setWebhookGuide] = useState(null);
  const [showSEOWizard, setShowSEOWizard] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);

  // Automation States
  const [automationSettings, setAutomationSettings] = useState({
    scraping_enabled: true,
    auto_optimization_enabled: false,
    auto_publication_enabled: false,
    scraping_frequency: 'daily',
    target_categories: []
  });
  const [automationStats, setAutomationStats] = useState(null);
  const [loadingAutomation, setLoadingAutomation] = useState(false);
  const [testingAutomation, setTestingAutomation] = useState(false);
  const [activeAutomationTab, setActiveAutomationTab] = useState('settings');
  const [showAutomationOnboarding, setShowAutomationOnboarding] = useState(false);
  const [showQuickSetup, setShowQuickSetup] = useState(false);

  // Premium Per-Store SEO Configuration States
  const [storesSeConfig, setStoresSeConfig] = useState([]);
  const [loadingStoresConfig, setLoadingStoresConfig] = useState(false);
  const [selectedStoreForConfig, setSelectedStoreForConfig] = useState(null);
  const [showStoreConfigModal, setShowStoreConfigModal] = useState(false);
  const [storeConfigForm, setStoreConfigForm] = useState({
    scraping_enabled: true,
    scraping_frequency: 'daily',
    target_keywords: [],
    target_categories: [],
    competitor_urls: [],
    auto_optimization_enabled: true,
    auto_publication_enabled: false,
    confidence_threshold: 0.7,
    geographic_focus: ['FR'],
    price_monitoring_enabled: true,
    content_optimization_enabled: true,
    keyword_tracking_enabled: true
  });
  const [storeConfigLoading, setStoreConfigLoading] = useState(false);
  const [storesAnalytics, setStoresAnalytics] = useState(null);
  const [testingStoreScrapingId, setTestingStoreScrapingId] = useState(null);

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportSheetId, setExportSheetId] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelForm, setCancelForm] = useState({ reason: '' });
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteForm, setDeleteForm] = useState({ password: '', reason: '' });
  
  // Store Publishing States
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [selectedStore, setSelectedStore] = useState('');
  const [publishingLoading, setPublishingLoading] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState('');
  const [publishError, setPublishError] = useState('');
  
  // Bulk Publishing States
  const [selectedSheets, setSelectedSheets] = useState([]);
  const [showBulkPublishModal, setShowBulkPublishModal] = useState(false);
  const [bulkPublishingLoading, setBulkPublishingLoading] = useState(false);
  const [bulkPublishResults, setBulkPublishResults] = useState([]);

  // Affiliate Configuration States
  const [showAffiliateConfigModal, setShowAffiliateConfigModal] = useState(false);
  const [affiliateConfigForm, setAffiliateConfigForm] = useState({
    default_commission_rate_pro: 10.0,
    default_commission_rate_premium: 15.0,
    commission_type: 'recurring',
    payment_frequency: 'monthly',
    minimum_payout: 50.0,
    program_enabled: true,
    auto_approval: false,
    cookie_duration_days: 30,
    welcome_message: 'Bienvenue dans notre programme d\'affiliation !',
    terms_and_conditions: ''
  });
  const [savingAffiliateConfig, setSavingAffiliateConfig] = useState(false);
  const [applyingConfig, setApplyingConfig] = useState(false);

  useEffect(() => {
    loadData();
    
    // Rafraîchir le statut Amazon quand on va sur l'onglet Boutiques/stores
    if (activeTab === 'stores' || activeTab === 'integrations') {
      setTimeout(() => {
        checkAmazonConnectionStatus();
      }, 500); // Petit délai pour que l'onglet soit bien chargé
    }
    
    // Set up automatic stats refresh for subscription tab
    let statsInterval;
    if (activeTab === 'subscription') {
      statsInterval = setInterval(async () => {
        try {
          const statsRes = await axios.get(`${API}/stats`);
          setStats(statsRes.data);
          setLastStatsUpdate(new Date());
        } catch (error) {
          console.log('Erreur lors de la mise à jour automatique des stats:', error);
        }
      }, 60000); // Refresh every 60 seconds
    }
    
    return () => {
      if (statsInterval) {
        clearInterval(statsInterval);
      }
    };
  }, [activeTab]);

  // ✅ CORRECTION: Déclaration des fonctions AVANT leur utilisation dans useEffect
  // Fonction pour rafraîchir le statut Amazon et mettre à jour l'UI
  const refreshAmazonStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/amazon/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const statusData = await response.json();
        console.log('📊 Statut Amazon mis à jour:', statusData.status);
        
        // Mise à jour dynamique du statut
        setAmazonConnectionStatus(statusData.status);
        
        // Reset du loader si connecté
        if (statusData.status === 'connected') {
          setSelectedPlatform(null);
        }
        
        return statusData.status;
      } else {
        console.error('❌ Erreur lors de la vérification du statut Amazon');
        return null;
      }
    } catch (error) {
      console.error('❌ Erreur refreshAmazonStatus:', error);
      return null;
    }
  }, []);

  // Fonction utilitaire pour afficher les notifications
  const showNotification = useCallback((message, type = 'info') => {
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6';
    
    notification.style.cssText = `
      position: fixed; top: 20px; right: 20px; z-index: 9999;
      background: ${bgColor}; color: white; padding: 15px 20px;
      border-radius: 8px; font-weight: 500; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      max-width: 400px; animation: slideIn 0.3s ease-out;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove après 5 secondes
    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
          if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
          }
        }, 300);
      }
    }, 5000);
  }, []);

  // Handle Amazon OAuth callback on component mount
  useEffect(() => {
    // Fallback : si retour sur /dashboard?amazon=connected → fetch /api/amazon/status
    const handleOAuthFallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const amazonConnected = urlParams.get('amazon_connected');
      const amazonError = urlParams.get('amazon_error');
      const amazonParam = urlParams.get('amazon'); // Pour /dashboard?amazon=connected
      const tabParam = urlParams.get('tab');

      if (amazonConnected === 'true' || amazonParam === 'connected' || amazonError) {
        console.log('🔄 Fallback OAuth détecté - nettoyage URL et mise à jour statut');
        
        // Nettoyer immédiatement l'URL pour éviter les rechargements
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
        
        if (amazonConnected === 'true' || amazonParam === 'connected') {
          console.log('🎉 Amazon OAuth success détecté via fallback!');
          
          // Naviguer vers l'onglet Boutiques si spécifié
          if (tabParam === 'stores') {
            setActiveTab('stores');
          }
          
          // Appeler /api/amazon/status pour mise à jour immédiate
          setTimeout(async () => {
            const status = await refreshAmazonStatus();
            
            if (status === 'connected') {
              showNotification('✅ Amazon connecté avec succès !', 'success');
            } else {
              // Si le statut n'est pas encore connecté, réessayer
              setTimeout(async () => {
                const retryStatus = await refreshAmazonStatus();
                if (retryStatus === 'connected') {
                  showNotification('✅ Amazon connecté avec succès !', 'success');
                }
              }, 2000);
            }
          }, 500);
          
        } else if (amazonError) {
          console.error('❌ Amazon OAuth error via fallback:', amazonError);
          
          // Naviguer vers l'onglet Boutiques si spécifié
          if (tabParam === 'stores') {
            setActiveTab('stores');
          }
          
          // Reset du loader et notification d'erreur
          setSelectedPlatform(null);
          setTimeout(() => {
            showNotification('❌ Erreur connexion Amazon. Veuillez réessayer.', 'error');
          }, 1000);
        }
      }
    };

    handleOAuthFallback();
  }, [refreshAmazonStatus, showNotification]);

  // Fonction pour déconnecter Amazon
  const handleAmazonDisconnection = useCallback(async () => {
    console.log('🔌 Démarrage déconnexion Amazon');
    
    try {
      setSelectedPlatform('amazon'); // État de chargement
      
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('❌ Token manquant pour la déconnexion Amazon');
        setSelectedPlatform(null);
        return;
      }
      
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/amazon/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Amazon déconnecté avec succès:', data);
        
        // Mise à jour immédiate du statut
        setAmazonConnectionStatus('revoked');
        setSelectedPlatform(null);
        
        // Notification de succès
        showNotification('✅ Amazon déconnecté avec succès !', 'success');
        
      } else {
        console.error('❌ Erreur lors de la déconnexion Amazon');
        setSelectedPlatform(null);
        showNotification('❌ Erreur lors de la déconnexion Amazon. Veuillez réessayer.', 'error');
      }
      
    } catch (error) {
      console.error('❌ Erreur lors de la déconnexion Amazon:', error);
      setSelectedPlatform(null);
      showNotification('❌ Erreur lors de la déconnexion Amazon. Veuillez réessayer.', 'error');
    }
  }, [showNotification]);

  // Load affiliate configuration when modal opens
  useEffect(() => {
    if (showAffiliateConfigModal && user?.is_admin) {
      loadAffiliateConfig();
    }
  }, [showAffiliateConfigModal, user?.is_admin]);

  const loadData = async () => {
    try {
      const [sheetsRes, statsRes] = await Promise.all([
        axios.get(`${API}/my-sheets`),
        axios.get(`${API}/stats`)
      ]);
      setSheets(sheetsRes.data);
      setStats(statsRes.data);
      setLastStatsUpdate(new Date());
      
      // Load Amazon connection status for all users
      await checkAmazonConnectionStatus();
      
      // Load detailed analytics if on dashboard tab
      if (activeTab === 'dashboard') {
        try {
          const analyticsRes = await axios.get(`${API}/analytics/detailed`);
          setDetailedAnalytics(analyticsRes.data);
        } catch (error) {
          console.error('Erreur lors du chargement des analyses détaillées:', error);
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    }
  };

  const loadDetailedAnalytics = async () => {
    try {
      const analyticsRes = await axios.get(`${API}/analytics/detailed`);
      setDetailedAnalytics(analyticsRes.data);
      
      // Load SEO data for premium users
      if (analyticsRes.data?.subscription_plan === 'premium') {
        await loadSEOData();
      }
      
    } catch (error) {
      console.error('Erreur lors du chargement des analyses détaillées:', error);
    }
  };

  // SEO Premium Functions
  const loadSEOData = async () => {
    setLoadingSEO(true);
    try {
      // Load SEO configuration
      const configResponse = await axios.get(`${API}/seo/config`);
      if (configResponse.data.success) {
        setSeoConfig(configResponse.data.config);
      }
      
      // Load SEO analytics
      const analyticsResponse = await axios.get(`${API}/seo/analytics?period=30d`);
      if (analyticsResponse.data.success) {
        setSeoAnalytics(analyticsResponse.data.analytics);
      }
      
      // Load recent optimizations
      const optimizationsResponse = await axios.get(`${API}/seo/optimizations?limit=10`);
      if (optimizationsResponse.data.success) {
        setSeoOptimizations(optimizationsResponse.data.optimizations);
      }
      
      // Load current trends
      const trendsResponse = await axios.get(`${API}/seo/trends?limit=20`);
      if (trendsResponse.data.success) {
        setSeoTrends(trendsResponse.data.trends);
      }
      
      // Load competitor analysis
      const competitorsResponse = await axios.get(`${API}/seo/competitors?limit=10`);
      if (competitorsResponse.data.success) {
        setCompetitors(competitorsResponse.data.competitors);
      }
      
    } catch (error) {
      console.error('Error loading SEO data:', error);
    }
    setLoadingSEO(false);
  };
  
  const triggerSEOScraping = async (type) => {
    try {
      const endpoint = type === 'trends' ? '/seo/scrape/trends' : '/seo/scrape/competitors';
      const response = await axios.post(`${API}${endpoint}`);
      
      if (response.data.success) {
        alert(`${response.data.message}`);
        // Reload data
        await loadSEOData();
      }
    } catch (error) {
      console.error(`Error triggering ${type} scraping:`, error);
      alert(`Erreur lors du scraping ${type === 'trends' ? 'des tendances' : 'des concurrents'}`);
    }
  };
  
  const requestSEOOptimization = async (productSheetId) => {
    try {
      const response = await axios.post(`${API}/seo/optimize/${productSheetId}`);
      
      if (response.data.success) {
        alert('Optimisation SEO générée avec succès!');
        // Reload optimizations
        await loadSEOData();
        return response.data.optimization_id;
      }
    } catch (error) {
      console.error('Error requesting SEO optimization:', error);
      alert('Erreur lors de la génération de l\'optimisation SEO');
    }
  };
  
  const applySEOOptimization = async (optimizationId) => {
    try {
      const response = await axios.post(`${API}/seo/apply/${optimizationId}`);
      
      if (response.data.success) {
        alert('Optimisation SEO appliquée et publiée avec succès!');
        // Reload data
        await loadSEOData();
      }
    } catch (error) {
      console.error('Error applying SEO optimization:', error);
      alert('Erreur lors de l\'application de l\'optimisation SEO');
    }
  };

  // Fonction pour vérifier le statut de connexion Amazon
  const checkAmazonConnectionStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/amazon/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAmazonConnectionStatus(data.status);
        console.log('Amazon connection status:', data.status);
        
        // Si connecté, reset selectedPlatform pour enlever le loader
        if (data.status === 'connected' && selectedPlatform === 'amazon') {
          setSelectedPlatform(null);
        }
      }
    } catch (error) {
      console.error('Failed to check Amazon connection status:', error);
    }
  }, [selectedPlatform]);

  // Gestion complète retour OAuth Amazon avec mise à jour dynamique du bouton
  const handleAmazonConnection = useCallback(async () => {
    console.log('🚀 Démarrage connexion Amazon - Marketplace Global');
    
    try {
      setSelectedPlatform('amazon'); // État de chargement
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // 1. Obtenir l'URL d'autorisation OAuth
      const response = await fetch(`${backendUrl}/api/amazon/connect?marketplace_id=A13V1IB3VIYZZH`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur lors de l'initialisation OAuth: ${response.status}`);
      }
      
      const data = await response.json();
      const authUrl = data.authorization_url;
      console.log('✅ URL d\'autorisation OAuth obtenue');
      
      // 2. Ouvre OAuth dans un popup
      const popupUrl = `${authUrl}&popup=true`;
      const popup = window.open(
        popupUrl,
        'amazon-oauth-popup',
        'width=800,height=700,scrollbars=yes,resizable=yes,status=yes,location=yes,toolbar=no,menubar=no'
      );
      
      if (!popup) {
        // Popup bloqué, fallback vers redirection
        console.log('🔄 Popup bloqué, fallback vers redirection'); 
        window.location.href = authUrl;
        return;
      }
      
      console.log('✅ Popup OAuth ouvert');
      
      // 3. Écoute postMessage({type:'AMAZON_CONNECTED'})
      const handleOAuthMessage = (event) => {
        // Vérification origine pour sécurité
        const allowedOrigins = [
          window.location.origin,
          'https://sellercentral-europe.amazon.com', 
          'https://sellercentral.amazon.com',
          new URL(process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL).origin  // Include backend origin
        ];
        
        if (!allowedOrigins.includes(event.origin)) {
          console.log('⚠️ Message ignoré - origine non autorisée:', event.origin);
          return;
        }
        
        console.log('📨 Message reçu du popup:', event.data);
        
        if (event.data && event.data.type === 'AMAZON_CONNECTED') {
          console.log('🎉 Amazon OAuth succès via postMessage!');
          
          // 4. Ferme popup → appelle /api/amazon/status
          if (popup && !popup.closed) {
            popup.close();
          }
          
          // Nettoyage des listeners
          window.removeEventListener('message', handleOAuthMessage);
          if (pollTimer) {
            clearInterval(pollTimer);
          }
          
          // 5. Mise à jour du statut et UI
          setTimeout(async () => {
            await refreshAmazonStatus();
            showNotification('✅ Amazon connecté avec succès !', 'success');
          }, 500);
          
        } else if (event.data && event.data.type === 'AMAZON_CONNECTION_ERROR') {
          console.error('❌ Erreur OAuth Amazon:', event.data.error);
          
          // Fermer popup et nettoyer
          if (popup && !popup.closed) {
            popup.close();
          }
          window.removeEventListener('message', handleOAuthMessage);
          if (pollTimer) {
            clearInterval(pollTimer);
          }
          
          setSelectedPlatform(null);
          showNotification('❌ Erreur connexion Amazon. Veuillez réessayer.', 'error');
        }
      };
      
      // Ajouter listener pour les messages
      window.addEventListener('message', handleOAuthMessage);
      
      // Fallback: polling pour détecter fermeture manuelle du popup
      const pollTimer = setInterval(() => {
        if (popup.closed) {
          console.log('🔄 Popup fermé manuellement - vérification statut');
          clearInterval(pollTimer);
          window.removeEventListener('message', handleOAuthMessage);
          
          // Vérifier le statut au cas où l'OAuth aurait réussi
          setTimeout(async () => {
            await refreshAmazonStatus();
          }, 1000);
        }
      }, 1000);
      
      // Nettoyage automatique après 10 minutes
      setTimeout(() => {
        if (popup && !popup.closed) {
          popup.close();
        }
        clearInterval(pollTimer);
        window.removeEventListener('message', handleOAuthMessage);
        setSelectedPlatform(null);
        console.log('⏰ Timeout connexion Amazon - nettoyage automatique');
      }, 600000); // 10 minutes
      
    } catch (error) {
      console.error('❌ Erreur lors de la connexion Amazon:', error);
      setSelectedPlatform(null);
      showNotification('❌ Erreur lors de la connexion Amazon. Veuillez réessayer.', 'error');
    }
  }, [refreshAmazonStatus, showNotification]);

  // Load configurations

  // SEO Connection Management Functions
  const loadConnectionsStatus = async () => {
    setLoadingConnections(true);
    try {
      const response = await axios.get(`${API}/ecommerce/connections/status`);
      if (response.data.success) {
        setConnectionsStatus(response.data.connections);
      }
    } catch (error) {
      console.error('Error loading connections status:', error);
    }
    setLoadingConnections(false);
  };
  
  const validateSEOSetup = async () => {
    try {
      const response = await axios.post(`${API}/ecommerce/seo-setup/validate`);
      if (response.data.success !== undefined) {
        setSeoSetupValidation(response.data);
      }
    } catch (error) {
      console.error('Error validating SEO setup:', error);
    }
  };
  
  const testConnection = async (connectionId) => {
    try {
      const response = await axios.post(`${API}/ecommerce/connections/test/${connectionId}`);
      if (response.data.success) {
        alert('Test de connexion réussi !');
        // Reload connections status
        await loadConnectionsStatus();
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      alert('Erreur lors du test de connexion');
    }
  };
  
  const loadWebhookGuide = async (platform) => {
    try {
      const response = await axios.get(`${API}/ecommerce/webhook-guide/${platform}`);
      if (response.data.success) {
        setWebhookGuide(response.data.guide);
        setSelectedWebhookPlatform(platform);
        setShowWebhookGuide(true);
      }
    } catch (error) {
      console.error('Error loading webhook guide:', error);
      alert('Guide non disponible pour cette plateforme');
    }
  };
  
  const startSEOWizard = () => {
    setShowSEOWizard(true);
    setWizardStep(1);
  };
  
  const nextWizardStep = () => {
    setWizardStep(prev => prev + 1);
  };
  
  const prevWizardStep = () => {
    setWizardStep(prev => Math.max(1, prev - 1));
  };
  
  const completeSEOWizard = () => {
    setShowSEOWizard(false);
    setWizardStep(1);
    // Reload data
    loadConnectionsStatus();
    validateSEOSetup();
    loadSEOData();
  };

  // Automation Functions
  const loadAutomationSettings = async () => {
    setLoadingAutomation(true);
    try {
      const response = await axios.get(`${API}/seo/auto-settings`, { 
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setAutomationSettings(response.data.settings);
      }
    } catch (error) {
      console.error('Error loading automation settings:', error);
      if (error.response?.status === 403) {
        setMessage('Les fonctionnalités d\'automatisation nécessitent un abonnement Pro');
      }
    }
    setLoadingAutomation(false);
  };

  const updateAutomationSettings = async (newSettings) => {
    try {
      // Mise à jour optimiste de l'état local pour éviter le rechargement visuel
      setAutomationSettings({ ...automationSettings, ...newSettings });
      
      const response = await axios.put(`${API}/seo/auto-settings`, newSettings, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setMessage('Paramètres d\'automatisation mis à jour avec succès');
        // Reload automation stats sans loading spinner
        await loadAutomationStats();
      } else {
        // Revert en cas d'échec
        setAutomationSettings(automationSettings);
        setError('Erreur lors de la mise à jour des paramètres');
      }
    } catch (error) {
      console.error('Error updating automation settings:', error);
      // Revert en cas d'erreur
      setAutomationSettings(automationSettings);
      setError('Erreur lors de la mise à jour des paramètres');
    }
  };

  const updateSeoConfig = async (newConfig) => {
    try {
      const response = await axios.put(`${API}/seo/config`, newConfig, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setSeoConfig({ ...seoConfig, ...newConfig });
        setMessage('Configuration SEO mise à jour avec succès');
      }
    } catch (error) {
      console.error('Error updating SEO config:', error);
      setError('Erreur lors de la mise à jour de la configuration SEO');
    }
  };

  const loadAutomationStats = async () => {
    try {
      const response = await axios.get(`${API}/seo/automation-stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setAutomationStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error loading automation stats:', error);
    }
  };

  const testAutomation = async () => {
    setTestingAutomation(true);
    try {
      const response = await axios.post(`${API}/seo/test-automation`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setMessage(`Test d'automatisation terminé: ${JSON.stringify(response.data.results)}`);
        // Reload stats after test
        await loadAutomationStats();
      }
    } catch (error) {
      console.error('Error testing automation:', error);
      setError('Erreur lors du test d\'automatisation');
    }
    setTestingAutomation(false);
  };

  // Premium Per-Store SEO Configuration Functions
  const loadStoresSeoConfig = async () => {
    if (!user || user.subscription_plan !== 'premium') return;
    
    setLoadingStoresConfig(true);
    try {
      const response = await axios.get(`${API}/seo/stores/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setStoresSeConfig(response.data.stores_config);
      }
    } catch (error) {
      console.error('Error loading stores SEO config:', error);
      setError('Erreur lors du chargement de la configuration SEO des boutiques');
    }
    setLoadingStoresConfig(false);
  };

  const updateStoreSeConfig = async (storeId, configData) => {
    setStoreConfigLoading(true);
    try {
      const response = await axios.put(`${API}/seo/stores/${storeId}/config`, configData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setMessage(`Configuration SEO mise à jour pour ${response.data.store_name}`);
        await loadStoresSeoConfig(); // Reload all configs
        setShowStoreConfigModal(false);
        setSelectedStoreForConfig(null);
      }
    } catch (error) {
      console.error('Error updating store SEO config:', error);
      setError('Erreur lors de la mise à jour de la configuration SEO');
    }
    setStoreConfigLoading(false);
  };

  const testStoreScraping = async (storeId) => {
    setTestingStoreScrapingId(storeId);
    try {
      const response = await axios.post(`${API}/seo/stores/${storeId}/test-scraping`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        const results = response.data.results;
        setMessage(`Test de scraping terminé pour ${response.data.store_name}: ${results.trends_scraped} tendances trouvées`);
        await loadStoresSeoConfig(); // Reload to get updated timestamps
      }
    } catch (error) {
      console.error('Error testing store scraping:', error);
      setError('Erreur lors du test de scraping');
    }
    setTestingStoreScrapingId(null);
  };

  const loadStoresAnalytics = async () => {
    if (!user || user.subscription_plan !== 'premium') return;
    
    try {
      const response = await axios.get(`${API}/seo/stores/analytics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setStoresAnalytics(response.data);
      }
    } catch (error) {
      console.error('Error loading stores analytics:', error);
    }
  };

  const openStoreConfigModal = (store, currentConfig) => {
    setSelectedStoreForConfig({ store, currentConfig });
    
    // Pre-fill form with current config or defaults
    setStoreConfigForm({
      scraping_enabled: currentConfig?.scraping_enabled ?? true,
      scraping_frequency: currentConfig?.scraping_frequency ?? 'daily',
      target_keywords: currentConfig?.target_keywords ?? [],
      target_categories: currentConfig?.target_categories ?? [],
      competitor_urls: currentConfig?.competitor_urls ?? [],
      auto_optimization_enabled: currentConfig?.auto_optimization_enabled ?? true,
      auto_publication_enabled: currentConfig?.auto_publication_enabled ?? false,
      confidence_threshold: currentConfig?.confidence_threshold ?? 0.7,
      geographic_focus: currentConfig?.geographic_focus ?? ['FR'],
      price_monitoring_enabled: currentConfig?.price_monitoring_enabled ?? true,
      content_optimization_enabled: currentConfig?.content_optimization_enabled ?? true,
      keyword_tracking_enabled: currentConfig?.keyword_tracking_enabled ?? true
    });
    
    setShowStoreConfigModal(true);
  };

  const handleStoreConfigSubmit = async (e) => {
    e.preventDefault();
    if (!selectedStoreForConfig) return;
    
    await updateStoreSeConfig(selectedStoreForConfig.store.id, storeConfigForm);
  };

  const addKeyword = () => {
    const keyword = prompt('Ajouter un mot-clé:');
    if (keyword && keyword.trim()) {
      setStoreConfigForm(prev => ({
        ...prev,
        target_keywords: [...prev.target_keywords, keyword.trim()]
      }));
    }
  };

  const removeKeyword = (index) => {
    setStoreConfigForm(prev => ({
      ...prev,
      target_keywords: prev.target_keywords.filter((_, i) => i !== index)
    }));
  };

  const addCategory = () => {
    const category = prompt('Ajouter une catégorie:');
    if (category && category.trim()) {
      setStoreConfigForm(prev => ({
        ...prev,
        target_categories: [...prev.target_categories, category.trim()]
      }));
    }
  };

  const removeCategory = (index) => {
    setStoreConfigForm(prev => ({
      ...prev,
      target_categories: prev.target_categories.filter((_, i) => i !== index)
    }));
  };

  const addCompetitorUrl = () => {
    const url = prompt('Ajouter une URL concurrente:');
    if (url && url.trim()) {
      setStoreConfigForm(prev => ({
        ...prev,
        competitor_urls: [...prev.competitor_urls, url.trim()]
      }));
    }
  };

  const removeCompetitorUrl = (index) => {
    setStoreConfigForm(prev => ({
      ...prev,
      competitor_urls: prev.competitor_urls.filter((_, i) => i !== index)
    }));
  };

  // Load automation data when user changes or component mounts
  useEffect(() => {
    if (user?.subscription_plan && ['pro', 'premium'].includes(user.subscription_plan)) {
      loadAutomationSettings();
      loadAutomationStats();
      
      // Load detailed analytics for all premium/pro users to show tabs correctly
      loadDetailedAnalytics();
      
      // Load per-store SEO config for Premium users
      if (user.subscription_plan === 'premium') {
        loadStoresSeoConfig();
        loadStoresAnalytics();
      }
    }
  }, [user?.subscription_plan]);

  // Load SEO data on component mount
  React.useEffect(() => {
    if (detailedAnalytics?.subscription_plan === 'premium') {
      loadSEOData();
      loadConnectionsStatus();
      validateSEOSetup();
      loadStoresSeoConfig();
      loadStoresAnalytics();
    }
  }, [detailedAnalytics]);

  const generateSheet = async (e) => {
    e.preventDefault();
    setLoading(true);
    setProgressPercentage(0);
    setError('');
    
    try {
      // Simulate progress steps
      const progressSteps = [
        { percent: 15, message: t('productAnalysis') },
        { percent: 35, message: t('aiContentGeneration') },
        { percent: 60, message: t('characteristicsCreation') },
        { percent: 80, message: t('imageGeneration') },
        { percent: 95, message: t('finalization') }
      ];

      // Run progress simulation
      for (let i = 0; i < progressSteps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400)); // 0.8-1.2s per step
        setProgressPercentage(progressSteps[i].percent);
      }

      const response = await axios.post(`${API}/generate-sheet`, {
        ...generatorForm,
        category: generatorForm.category === 'custom' ? generatorForm.custom_category : generatorForm.category,
        generate_image: true,
        language: currentLanguage
      });
      
      // Complete to 100%
      setProgressPercentage(100);
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setGeneratedSheet(response.data);
      setGeneratorForm({ 
        product_name: '', 
        product_description: '', 
        number_of_images: 1,
        category: '',
        custom_category: ''
      });
      loadData();
    } catch (error) {
      console.error('Erreur lors de la génération:', error);
      
      // Check if it's a limit exceeded error
      if (error.response?.status === 403) {
        const errorDetail = error.response.data?.detail || error.response.data;
        
        // Check if it's a free plan limit issue
        if (errorDetail?.needs_upgrade) {
          console.log('Free plan limit reached, redirecting to subscription tab');
          // Redirect to subscription tab
          setActiveTab('subscription');
          setError(`${errorDetail.message} Veuillez choisir un plan ci-dessous.`);
        } else {
          setError('Erreur lors de la génération de la fiche produit');
        }
      } else {
        setError('Erreur lors de la génération de la fiche produit');
      }
    }
    
    setLoading(false);
    setProgressPercentage(0);
  };

  // CONTENTANALYTICS - FONCTION SOUMISSION FEEDBACK
  const submitFeedback = async (generationId, useful) => {
    try {
      console.log(`📊 Soumission feedback: ${generationId} - ${useful ? 'Utile' : 'Pas utile'}`);
      
      // Marquer comme en cours de soumission
      setFeedbackSubmitting(prev => ({ ...prev, [generationId]: true }));
      
      const response = await axios.post(`${API}/feedback/submit`, {
        generation_id: generationId,
        useful: useful
      });
      
      if (response.data.success) {
        console.log('✅ Feedback envoyé avec succès');
        // Marquer comme soumis
        setFeedbackSubmitted(prev => ({ ...prev, [generationId]: useful }));
      } else {
        console.error('❌ Erreur réponse feedback:', response.data.message);
        alert(t('feedbackError') + ': ' + response.data.message);
      }
    } catch (error) {
      console.error('❌ Erreur soumission feedback:', error);
      alert(t('feedbackError'));
    } finally {
      // Arrêter l'indication de soumission
      setFeedbackSubmitting(prev => ({ ...prev, [generationId]: false }));
    }
  };

  // PREMIUM FEATURES FUNCTIONS
  
  // Load AI Features Overview
  const loadAiFeatures = async () => {
    try {
      const response = await axios.get(`${API}/ai/features-overview`);
      setAiFeatures(response.data);
    } catch (error) {
      console.error('Error loading AI features:', error);
    }
  };
  
  // SEO Analysis Functions
  const handleSeoAnalysis = async () => {
    if (!seoAnalysisForm.product_name || !seoAnalysisForm.product_description) {
      setError('Veuillez remplir tous les champs obligatoires');
      return;
    }
    
    setSeoAnalysisLoading(true);
    try {
      const requestData = {
        ...seoAnalysisForm,
        target_keywords: seoAnalysisForm.target_keywords.split(',').map(k => k.trim()).filter(k => k)
      };
      
      const response = await axios.post(`${API}/ai/seo-analysis`, requestData);
      setSeoAnalysisResult(response.data.seo_analysis);
    } catch (error) {
      console.error('SEO Analysis error:', error);
      if (error.response?.status === 403) {
        setError('Analyse SEO nécessite un abonnement Pro ou Premium');
      } else if (error.response?.status === 503) {
        setError('Service temporairement indisponible - Configuration API en cours');
      } else {
        setError('Erreur lors de l\'analyse SEO');
      }
    }
    setSeoAnalysisLoading(false);
  };
  
  // Competitor Analysis Functions
  const handleCompetitorAnalysis = async () => {
    if (!competitorAnalysisForm.product_name || !competitorAnalysisForm.category) {
      setError('Veuillez remplir le nom du produit et la catégorie');
      return;
    }
    
    setCompetitorAnalysisLoading(true);
    try {
      const requestData = {
        ...competitorAnalysisForm,
        competitor_urls: competitorAnalysisForm.competitor_urls.split(',').map(url => url.trim()).filter(url => url)
      };
      
      const response = await axios.post(`${API}/ai/competitor-analysis`, requestData);
      setCompetitorAnalysisResult(response.data.competitor_analysis);
    } catch (error) {
      console.error('Competitor Analysis error:', error);
      if (error.response?.status === 403) {
        setError('Analyse concurrentielle nécessite un abonnement Pro ou Premium');
      } else {
        setError('Erreur lors de l\'analyse concurrentielle');
      }
    }
    setCompetitorAnalysisLoading(false);
  };
  
  // Price Optimization Functions
  const handlePriceOptimization = async () => {
    if (!priceOptimizationForm.product_name) {
      setError('Veuillez remplir le nom du produit');
      return;
    }
    
    setPriceOptimizationLoading(true);
    try {
      const requestData = {
        ...priceOptimizationForm,
        current_price: priceOptimizationForm.current_price ? parseFloat(priceOptimizationForm.current_price) : null,
        cost_price: priceOptimizationForm.cost_price ? parseFloat(priceOptimizationForm.cost_price) : null,
        competitor_prices: priceOptimizationForm.competitor_prices.split(',').map(p => parseFloat(p.trim())).filter(p => !isNaN(p))
      };
      
      const response = await axios.post(`${API}/ai/price-optimization`, requestData);
      setPriceOptimizationResult(response.data.price_optimization);
    } catch (error) {
      console.error('Price Optimization error:', error);
      if (error.response?.status === 403) {
        setError('Optimisation des prix nécessite un abonnement Pro ou Premium');
      } else {
        setError('Erreur lors de l\'optimisation des prix');
      }
    }
    setPriceOptimizationLoading(false);
  };
  
  // Multilingual Translation Functions
  const handleMultilingualTranslation = async () => {
    if (!translationForm.source_text) {
      setError('Veuillez saisir le texte à traduire');
      return;
    }
    
    setTranslationLoading(true);
    try {
      const requestData = {
        ...translationForm,
        preserve_keywords: translationForm.preserve_keywords.split(',').map(k => k.trim()).filter(k => k)
      };
      
      const response = await axios.post(`${API}/ai/multilingual-translation`, requestData);
      setTranslationResult(response.data.translation_result);
    } catch (error) {
      console.error('Translation error:', error);
      if (error.response?.status === 403) {
        setError('Traduction multilingue nécessite un abonnement Pro ou Premium');
      } else {
        setError('Erreur lors de la traduction');
      }
    }
    setTranslationLoading(false);
  };
  
  // Product Variants Functions
  const handleProductVariants = async () => {
    if (!variantsForm.base_product || !variantsForm.base_description) {
      setError('Veuillez remplir le nom du produit et sa description');
      return;
    }
    
    setVariantsLoading(true);
    try {
      const response = await axios.post(`${API}/ai/product-variants`, variantsForm);
      setVariantsResult(response.data.product_variants);
    } catch (error) {
      console.error('Product Variants error:', error);
      if (error.response?.status === 403) {
        setError('Génération de variantes nécessite un abonnement Pro ou Premium');
      } else {
        setError('Erreur lors de la génération des variantes');
      }
    }
    setVariantsLoading(false);
  };
  
  // E-commerce Integration Functions
  const loadConnectedStores = async () => {
    try {
      const response = await axios.get(`${API}/ecommerce/all-stores`);
      setConnectedStores(response.data.stores);
    } catch (error) {
      console.error('Error loading stores:', error);
    }
  };
  
  const loadIntegrationLogs = async () => {
    try {
      const response = await axios.get(`${API}/ecommerce/integration-logs`);
      setIntegrationLogs(response.data.logs);
    } catch (error) {
      console.error('Error loading integration logs:', error);
    }
  };
  
  const handleConnectStore = async () => {
    setConnectingStore(true);
    setError('');
    
    try {
      const endpoint = `${API}/ecommerce/${selectedPlatform}/connect`;
      const response = await axios.post(endpoint, storeConnectionForm, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data.success) {
        setShowConnectStoreModal(false);
        setStoreConnectionForm({});
        setSelectedPlatform('');
        loadConnectedStores();
        setError('');
        
        // Show success message
        setMessage(`✅ Boutique ${selectedPlatform.charAt(0).toUpperCase() + selectedPlatform.slice(1)} connectée avec succès !`);
        setTimeout(() => setMessage(''), 3000);
      } else {
        setError(response.data.message || `Impossible de connecter la boutique ${selectedPlatform}`);
      }
    } catch (error) {
      console.error('Store connection error:', error);
      
      if (error.response?.status === 400) {
        setError('Impossible de se connecter à la boutique. Vérifiez vos identifiants.');
      } else if (error.response?.status === 403) {
        setError('Cette fonctionnalité nécessite un abonnement premium.');
      } else if (error.response?.status === 422) {
        setError('Données de connexion invalides. Vérifiez tous les champs requis.');
      } else {
        setError(`Erreur de connexion à ${selectedPlatform}. Réessayez plus tard.`);
      }
    } finally {
      setConnectingStore(false);
    }
  };
  
  // Premium Analytics Functions
  const loadPremiumAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const timeframeData = { period: analyticsTimeframe };
      
      const [productRes, integrationRes, engagementRes] = await Promise.all([
        axios.post(`${API}/analytics/product-performance`, timeframeData).catch(e => ({ data: null })),
        axios.post(`${API}/analytics/integration-performance`, timeframeData).catch(e => ({ data: null })),
        axios.post(`${API}/analytics/user-engagement`, timeframeData).catch(e => ({ data: null }))
      ]);
      
      setProductPerformance(productRes.data);
      setIntegrationPerformance(integrationRes.data);
      setUserEngagement(engagementRes.data);
    } catch (error) {
      console.error('Analytics loading error:', error);
    }
    setAnalyticsLoading(false);
  };
  
  // Store Publishing Functions
  const openPublishModal = () => {
    // Check if user has premium plan
    if (user?.subscription_plan === 'gratuit') {
      // Show upgrade modal for free users
      setError('Publication sur boutiques nécessite un abonnement Pro ou Premium');
      setActiveTab('subscription');
      return;
    }
    
    // Load connected stores if not already loaded
    if (connectedStores.length === 0) {
      loadConnectedStores();
    }
    
    // Check if user has connected stores after loading
    if (connectedStores.length === 0) {
      // Redirect directly to integrations tab if no stores connected
      setActiveTab('integrations');
      return;
    }
    
    // Open publish modal if stores are connected
    setShowPublishModal(true);
    setPublishError('');
    setPublishSuccess('');
  };
  
  const closePublishModal = () => {
    setShowPublishModal(false);
    setSelectedStore('');
    setPublishError('');
    setPublishSuccess('');
  };
  
  const publishToStore = async () => {
    if (!selectedStore) {
      setPublishError(t('selectStore'));
      return;
    }
    
    if (!generatedSheet) {
      setPublishError('Aucune fiche produit à publier');
      return;
    }
    
    setPublishingLoading(true);
    setPublishError('');
    
    try {
      const store = connectedStores.find(s => s.id === selectedStore);
      if (!store) {
        setPublishError('Boutique introuvable');
        return;
      }
      
      const publishData = {
        product_sheet_id: generatedSheet.id,
        store_id: selectedStore,
        product_data: {
          name: generatedSheet.generated_title,
          description: generatedSheet.marketing_description,
          features: generatedSheet.key_features,
          seo_tags: generatedSheet.seo_tags,
          price_suggestions: generatedSheet.price_suggestions,
          target_audience: generatedSheet.target_audience,
          images: generatedSheet.product_images_base64 || (generatedSheet.product_image_base64 ? [generatedSheet.product_image_base64] : [])
        }
      };
      
      // Publish to specific platform endpoint
      const platformEndpoint = `${API}/ecommerce/${store.platform}/publish`;
      const response = await axios.post(platformEndpoint, publishData);
      
      if (response.data.success) {
        setPublishSuccess(`${t('publishedSuccessfully')} ${store.store_name} (${store.platform})`);
        setTimeout(() => {
          closePublishModal();
        }, 2000);
        
        // Reload integration logs to show the new publication
        loadIntegrationLogs();
      } else {
        setPublishError(response.data.message || t('publishError'));
      }
      
    } catch (error) {
      console.error('Publish error:', error);
      if (error.response?.status === 403) {
        setPublishError('Publication nécessite un abonnement premium');
      } else if (error.response?.status === 400) {
        setPublishError(error.response.data?.detail || 'Erreur de validation des données');
      } else {
        setPublishError(t('publishError'));
      }
    } finally {
      setPublishingLoading(false);
    }
  };

  // Bulk Publishing Functions
  const toggleSheetSelection = (sheetId) => {
    setSelectedSheets(prev => {
      if (prev.includes(sheetId)) {
        return prev.filter(id => id !== sheetId);
      } else {
        return [...prev, sheetId];
      }
    });
  };

  const selectAllSheets = () => {
    setSelectedSheets(sheets.map(sheet => sheet.id));
  };

  const deselectAllSheets = () => {
    setSelectedSheets([]);
  };

  const openBulkPublishModal = () => {
    if (user?.subscription_plan === 'gratuit') {
      setError('Publication sur boutiques nécessite un abonnement Pro ou Premium');
      setActiveTab('subscription');
      return;
    }

    // If no sheets selected, automatically select all sheets
    if (selectedSheets.length === 0 && sheets.length > 0) {
      setSelectedSheets(sheets.map(sheet => sheet.id));
    }

    if (connectedStores.length === 0) {
      setActiveTab('integrations');
      return;
    }

    setShowBulkPublishModal(true);
    setBulkPublishResults([]);
  };

  const closeBulkPublishModal = () => {
    setShowBulkPublishModal(false);
    setSelectedStore('');
    setBulkPublishResults([]);
  };

  const bulkPublishToStore = async () => {
    if (!selectedStore) {
      setError(t('selectStore'));
      return;
    }

    setBulkPublishingLoading(true);
    setBulkPublishResults([]);

    const selectedSheetsData = sheets.filter(sheet => selectedSheets.includes(sheet.id));
    const store = connectedStores.find(s => s.id === selectedStore);
    
    if (!store) {
      setError('Boutique introuvable');
      setBulkPublishingLoading(false);
      return;
    }

    const results = [];

    for (const sheet of selectedSheetsData) {
      try {
        const publishData = {
          product_sheet_id: sheet.id,
          store_id: selectedStore,
          product_data: {
            name: sheet.generated_title,
            description: sheet.marketing_description,
            features: sheet.key_features,
            seo_tags: sheet.seo_tags,
            price_suggestions: sheet.price_suggestions,
            target_audience: sheet.target_audience,
            images: sheet.product_images_base64 || (sheet.product_image_base64 ? [sheet.product_image_base64] : [])
          }
        };

        const platformEndpoint = `${API}/ecommerce/${store.platform}/publish`;
        const response = await axios.post(platformEndpoint, publishData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        results.push({
          sheet: sheet,
          success: response.data.success,
          message: response.data.message || `Publié sur ${store.store_name}`
        });

      } catch (error) {
        results.push({
          sheet: sheet,
          success: false,
          message: error.response?.data?.detail || `Erreur lors de la publication de ${sheet.product_name}`
        });
      }
    }

    setBulkPublishResults(results);
    
    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;

    if (successCount === totalCount) {
      setMessage(`✅ ${successCount} fiches publiées avec succès sur ${store.store_name}`);
    } else if (successCount > 0) {
      setMessage(`⚠️ ${successCount}/${totalCount} fiches publiées sur ${store.store_name}`);
    } else {
      setError(`❌ Échec de la publication des fiches sur ${store.store_name}`);
    }

    setBulkPublishingLoading(false);
    loadIntegrationLogs();

    // Auto close after 3 seconds if all successful
    if (successCount === totalCount) {
      setTimeout(() => {
        closeBulkPublishModal();
        setSelectedSheets([]); // Clear selection
      }, 3000);
    }
  };

  const exportData = async (format) => {
    try {
      setExportLoading(true);
      const requestData = { format };
      
      // Handle different export modes
      if (exportSheetId === 'selected' && selectedSheets.length > 0) {
        // Export only selected sheets
        requestData.sheet_ids = selectedSheets;
      } else if (exportSheetId && exportSheetId !== 'selected') {
        // Export specific individual sheet
        requestData.sheet_id = exportSheetId;
      }
      // If no exportSheetId, export all sheets (default behavior)

      const response = await axios.post(`${API}/export`, requestData);
      const { content, filename, content_type, encoding } = response.data;

      if (encoding === 'base64') {
        // Handle binary formats (PDF, Excel)
        const byteCharacters = atob(content);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: content_type });
        
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        // Handle text formats (CSV, JSON) with UTF-8 BOM for proper Excel support
        let contentWithBOM = content;
        
        // Add UTF-8 BOM for CSV files to ensure proper encoding in Excel
        if (format === 'csv' || format === 'shopify' || format === 'woocommerce') {
          contentWithBOM = '\uFEFF' + content; // UTF-8 BOM
        }
        
        const blob = new Blob([contentWithBOM], { type: `${content_type}; charset=utf-8` });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }

      // Close export modal
      setShowExportModal(false);
      setExportSheetId(null);
      
    } catch (error) {
      console.error('Erreur lors de l\'export:', error);
      setError(error.response?.data?.detail || 'Erreur lors de l\'export');
    } finally {
      setExportLoading(false);
    }
  };

  // Legacy CSV export function for compatibility
  const exportCSV = async () => {
    await exportData('csv');
  };

  const openExportModal = (mode = null, sheetId = null) => {
    if (mode === 'selected' && selectedSheets.length > 0) {
      // Export only selected sheets
      setExportSheetId('selected');
    } else if (mode === 'all') {
      // Export all sheets
      setExportSheetId(null);
    } else {
      // Export specific sheet (individual export)
      setExportSheetId(sheetId);
    }
    setShowExportModal(true);
  };

  const cancelSubscription = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/subscription/cancel`, {
        reason: cancelForm.reason || null
      });
      
      setShowCancelModal(false);
      setCancelForm({ reason: '' });
      setError('');
      alert(t('subscriptionCancelledSuccess'));
      
      // Reload user data to reflect changes
      await loadData();
      
    } catch (error) {
      console.error('Erreur annulation abonnement:', error);
      setError(error.response?.data?.detail || 'Erreur lors de l\'annulation de l\'abonnement');
    } finally {
      setLoading(false);
    }
  };

  const changePasswordDashboard = async (e) => {
    e.preventDefault();
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('Les nouveaux mots de passe ne correspondent pas');
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      setError('Le nouveau mot de passe doit contenir au moins 6 caractères');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });
      
      setShowPasswordModal(false);
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      setError('');
      alert('Mot de passe modifié avec succès !');
      
    } catch (error) {
      console.error('Erreur changement mot de passe:', error);
      setError(error.response?.data?.detail || 'Erreur lors du changement de mot de passe');
    } finally {
      setLoading(false);
    }
  };

  const deleteAccount = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/delete-account`, {
        password: deleteForm.password,
        reason: deleteForm.reason || null
      });
      
      setShowDeleteModal(false);
      setDeleteForm({ password: '', reason: '' });
      setError('');
      alert('Compte supprimé avec succès. Vous allez être déconnecté.');
      
      // Logout user
      logout();
      
    } catch (error) {
      console.error('Erreur suppression compte:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la suppression du compte');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan) => {
    // Check if user is logged in
    if (!user) {
      setError('Vous devez être connecté pour effectuer un achat. Veuillez vous connecter ou créer un compte.');
      setShowUpgradeModal(false);
      // Redirect to login - in Dashboard context, this would mean logging out and going to landing page
      logout();
      return;
    }

    // ⭐ NOUVEAU : Pour les utilisateurs gratuits, proposer d'abord l'essai gratuit
    if (user?.subscription_plan === 'gratuit') {
      console.log('🎯 Utilisateur gratuit -> Ouverture modal d\'essai gratuit pour plan:', plan);
      
      // Stocker le plan sélectionné pour l'essai
      localStorage.setItem('selectedTrialPlan', plan);
      
      // Ouvrir la modal d'essai gratuit au lieu du paiement direct
      if (typeof window.showTrialModal === 'function') {
        window.showTrialModal();
        return;
      } else {
        console.error('❌ showTrialModal function not available - fallback to direct payment');
        // Fallback au paiement direct si la modal d'essai n'est pas disponible
      }
    }

    // Pour les utilisateurs qui ont déjà un plan payant OU si la modal d'essai n'est pas disponible
    console.log('🎯 Paiement direct pour plan:', plan);
    setSelectedUpgradePlan(plan);
    setLoading(true);
    
    try {
      // Get affiliate code from URL or session storage if exists
      const urlParams = new URLSearchParams(window.location.search);
      const affiliateCode = urlParams.get('ref') || sessionStorage.getItem('affiliate_conversion_code');
      
      // Call backend to create checkout session (SANS ESSAI pour les upgrades)
      const response = await axios.post(`${API}/payments/checkout`, {
        plan_type: plan,
        origin_url: window.location.origin,
        affiliate_code: affiliateCode || null,
        trial_subscription: false  // ⭐ Pas d'essai pour les upgrades de plan existant
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.data.checkout_url) {
        // Store affiliate code in session for conversion tracking
        if (affiliateCode) {
          sessionStorage.setItem('affiliate_conversion_code', affiliateCode);
        }
        // Redirect to Stripe Checkout
        window.location.href = response.data.checkout_url;
      } else {
        throw new Error('URL de checkout non reçue');
      }
    } catch (error) {
      console.error('Erreur lors de la création de la session de paiement:', error);
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        setError('Session expirée. Veuillez vous reconnecter.');
        setShowUpgradeModal(false);
        logout();
      } else if (error.response?.status === 403) {
        setError('Accès non autorisé. Veuillez vous connecter avec un compte valide.');
        setShowUpgradeModal(false);
        logout();
      } else if (error.response?.status === 503) {
        setError('Service de paiement temporairement indisponible. Veuillez réessayer plus tard.');
        setShowUpgradeModal(true);
      } else {
        setError('Erreur lors de l\'initialisation du paiement. Veuillez réessayer.');
        setShowUpgradeModal(true);
      }
    }
    
    setLoading(false);
  };

  const handleDowngrade = async (plan) => {
    // Demander confirmation pour la rétrogradation
    const confirmMessage = plan === 'gratuit' ? 
      (currentLanguage === 'fr' ? 
        'Êtes-vous sûr de vouloir rétrograder vers le plan Gratuit ? Vous perdrez l\'accès aux fonctionnalités premium.' :
        'Are you sure you want to downgrade to the Free plan? You will lose access to premium features.'
      ) : 
      (currentLanguage === 'fr' ?
        'Êtes-vous sûr de vouloir rétrograder vers le plan Pro ? Vous perdrez certaines fonctionnalités premium.' :
        'Are you sure you want to downgrade to the Pro plan? You will lose some premium features.'
      );
    
    if (!confirm(confirmMessage)) {
      return;
    }
    
    setLoading(true);
    
    try {
      // Call backend to downgrade subscription
      const response = await axios.post(`${API}/subscription/downgrade`, {
        new_plan: plan
      });
      
      if (response.data.success) {
        // Reload user data to reflect the change
        await loadData();
        
        setMessage(currentLanguage === 'fr' ? 
          `Plan changé avec succès vers ${plan === 'gratuit' ? 'Gratuit' : 'Pro'}` :
          `Plan successfully changed to ${plan === 'gratuit' ? 'Free' : 'Pro'}`
        );
        
        // Clear success message after 3 seconds
        setTimeout(() => setMessage(''), 3000);
      } else {
        throw new Error(response.data.message || 'Erreur lors de la rétrogradation');
      }
    } catch (error) {
      console.error('Erreur lors de la rétrogradation:', error);
      setError(currentLanguage === 'fr' ? 
        'Erreur lors de la rétrogradation. Veuillez réessayer.' :
        'Error during downgrade. Please try again.'
      );
    }
    
    setLoading(false);
  };

  // Check for payment success/failure on page load
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      // Handle payment success
      checkPaymentStatus(sessionId);
    }
  }, [loadData]);

  const checkPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attempts >= maxAttempts) {
      setError('Vérification du paiement expirée. Veuillez vérifier votre email pour confirmation.');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`);
      const paymentData = response.data;
      
      if (paymentData.payment_status === 'paid') {
        // Payment successful - refresh user data completely
        setShowUpgradeSuccess(true);
        
        // Force refresh of all user data to get updated subscription status
        try {
          // Refresh all dashboard data including stats
          await loadData();
          
          // Clear any previous errors
          setError('');
          
          console.log('User data refreshed after successful payment');
        } catch (refreshError) {
          console.error('Error refreshing user data after payment:', refreshError);
        }
        
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      } else if (paymentData.stripe_status === 'expired') {
        setError('Session de paiement expirée. Veuillez réessayer.');
        return;
      }

      // If payment is still pending, continue polling
      setTimeout(() => checkPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error('Erreur vérification paiement:', error);
      setError('Erreur lors de la vérification du paiement. Veuillez réessayer.');
    }
  };

  // Export Modal Component
  const ExportModal = () => {
    const exportFormats = [
      { 
        value: 'csv', 
        label: 'CSV (Excel)', 
        icon: '📊', 
        description: 'Idéal pour Excel et Google Sheets' 
      },
      { 
        value: 'xlsx', 
        label: 'Excel (.xlsx)', 
        icon: '📈', 
        description: 'Format Excel natif avec images' 
      },
      { 
        value: 'pdf', 
        label: 'PDF', 
        icon: '📄', 
        description: 'Document PDF prêt à imprimer' 
      },
      { 
        value: 'json', 
        label: 'JSON', 
        icon: '🔧', 
        description: 'Format de données pour développeurs' 
      },
      { 
        value: 'shopify', 
        label: 'Shopify CSV', 
        icon: '🛒', 
        description: 'Import direct dans Shopify avec images' 
      },
      { 
        value: 'woocommerce', 
        label: 'WooCommerce CSV', 
        icon: '🏪', 
        description: 'Import direct dans WooCommerce' 
      }
    ];

    if (!showExportModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
        <div className="bg-white rounded-lg w-full max-w-2xl max-h-[95vh] overflow-y-auto">
          {/* Header - Mobile optimized */}
          <div className="flex justify-between items-center p-4 sm:p-6 border-b">
            <h2 className="text-lg sm:text-xl font-bold text-gray-900">
              {exportSheetId === 'selected' 
                ? `Export sélection (${selectedSheets.length} fiches)`
                : exportSheetId 
                  ? t('exportThisSheet') 
                  : t('exportSheets')
              }
            </h2>
            <button
              onClick={() => setShowExportModal(false)}
              className="text-gray-500 hover:text-gray-700 p-1"
            >
              <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-4 sm:p-6">
            {/* Description */}
            <div className="mb-4 sm:mb-6">
              <p className="text-sm sm:text-base text-gray-600 mb-2">
                {exportSheetId === 'selected'
                  ? `Choisissez le format d'export pour les ${selectedSheets.length} fiches sélectionnées`
                  : exportSheetId 
                    ? t('chooseExportFormat')
                    : t('chooseExportFormatMultiple')
                }
              </p>
              <div className="text-xs sm:text-sm text-blue-600 bg-blue-50 p-2 sm:p-3 rounded-lg">
                ✨ <strong>{t('newFeature')} :</strong> {t('imagesIncluded')}
                {exportSheetId === 'selected' && (
                  <div className="mt-1 text-green-600 font-medium">
                    🎯 Export de la sélection uniquement
                  </div>
                )}
                {exportSheetId && exportSheetId !== 'selected' && (
                  <div className="mt-1 text-purple-600 font-medium">
                    🎯 {t('individualExport')}
                  </div>
                )}
              </div>
            </div>

            {/* Export Formats Grid - Mobile First */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 mb-4 sm:mb-6">
              {exportFormats.map((format) => (
                <button
                  key={format.value}
                  onClick={() => exportData(format.value)}
                  disabled={exportLoading}
                  className="text-left p-3 sm:p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="flex items-start space-x-2 sm:space-x-3">
                    <span className="text-xl sm:text-2xl flex-shrink-0">{format.icon}</span>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 text-sm sm:text-base truncate">{format.label}</h3>
                      <p className="text-xs sm:text-sm text-gray-600 line-clamp-2">{format.description}</p>
                      {(format.value === 'shopify' || format.value === 'woocommerce') && (
                        <div className="mt-1 text-xs text-green-600 font-medium">
                          ⚡ Prêt pour l'import e-commerce
                        </div>
                      )}
                    </div>
                    {exportLoading && (
                      <div className="animate-spin rounded-full h-3 w-3 sm:h-4 sm:w-4 border-b-2 border-blue-600 flex-shrink-0"></div>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Info Section - Responsive */}
            <div className="border-t pt-3 sm:pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm text-gray-600">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 text-sm">📊 Formats Standards</h4>
                  <ul className="space-y-1">
                    <li>• <strong>CSV/Excel :</strong> Tableaux avec images base64</li>
                    <li>• <strong>PDF :</strong> Mise en forme professionnelle</li>
                    <li>• <strong>JSON :</strong> Intégration API complète</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2 text-sm">🛒 E-commerce</h4>
                  <ul className="space-y-1">
                    <li>• <strong>Shopify :</strong> Import automatique des produits</li>
                    <li>• <strong>WooCommerce :</strong> Compatible WordPress</li>
                    <li>• <strong>Images :</strong> URLs automatiques pour import</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t p-4 sm:p-6">
            <div className="flex justify-end">
              <button
                onClick={() => setShowExportModal(false)}
                disabled={exportLoading}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md disabled:opacity-50 text-sm sm:text-base w-full sm:w-auto"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Affiliate Configuration Functions (moved to parent component)
  // const loadAffiliateConfig = async () => {
  //   try {
  //     const response = await axios.get(`${API}/admin/affiliate-config?admin_key=ECOMSIMPLY_ADMIN_2024`);
  //     if (response.data.success && response.data.config) {
  //       setAffiliateConfigForm(response.data.config);
  //     }
  //   } catch (error) {
  //     console.error('Erreur lors du chargement de la configuration d\'affiliation:', error);
  //   }
  // };

  // Wrapper for parent's affiliate config function
  const handleSaveAffiliateConfig = async () => {
    if (loadAffiliateConfig) {
      setSavingAffiliateConfig(true);
      try {
        const response = await axios.put(
          `${API}/admin/affiliate-config?admin_key=ECOMSIMPLY_ADMIN_2025`,
          affiliateConfigForm
        );
        
        if (response.data.success) {
          setMessage('Configuration d\'affiliation sauvegardée avec succès !');
          setShowAffiliateConfigModal(false);
          setTimeout(() => setMessage(''), 3000);
          // Call parent's load function to refresh data
          await loadAffiliateConfig();
        }
      } catch (error) {
        console.error('Erreur lors de la sauvegarde de la configuration d\'affiliation:', error);
        setError('Erreur lors de la sauvegarde de la configuration');
        setTimeout(() => setError(''), 3000);
      } finally {
        setSavingAffiliateConfig(false);
      }
    }
  };

  const bulkUpdateAffiliateCommissions = async () => {
    if (!confirm('Êtes-vous sûr de vouloir appliquer ces taux de commission à tous les affiliés existants ?')) {
      return;
    }

    try {
      const response = await axios.post(
        `${API}/admin/affiliates/bulk-update-commissions?admin_key=ECOMSIMPLY_ADMIN_2025`,
        {
          default_commission_rate_pro: affiliateConfigForm.default_commission_rate_pro,
          default_commission_rate_premium: affiliateConfigForm.default_commission_rate_premium
        }
      );
      
      if (response.data.success) {
        setMessage(`Commissions mises à jour pour ${response.data.updated_count} affiliés !`);
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour en lot des commissions:', error);
      setError('Erreur lors de la mise à jour des commissions');
      setTimeout(() => setError(''), 3000);
    }
  };

  return (
    <DashboardShell
      onGoToHome={onGoToHome}
      onLogout={logout}
      user={user}
      activeTab={activeTab}
      setActiveTab={setActiveTab}
    >
      {/* Only show KPI Grid when on main dashboard view */}
      {activeTab === 'generator' ? null : (
        <div className="mb-8">
          <KPIGrid stats={{ sheets_count: sheets?.length || 0 }} />
        </div>
      )}

      {/* Content based on active tab from DashboardShell navigation */}
      <div className="bg-card rounded-xl border border-border shadow-soft-sm p-6">

        {/* AI Generator Tab - Full content view */}
        {(activeTab === 'generator' || activeTab === 'ai-generator') && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('aiGenerator')} - {t('generateFirstSheet')}</h2>
              <form onSubmit={generateSheet} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('productName')}</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.product_name}
                    onChange={(e) => setGeneratorForm({...generatorForm, product_name: e.target.value})}
                    placeholder={`${t('productName')}...`}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('productDescription')}</label>
                  <textarea
                    rows="4"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.product_description}
                    onChange={(e) => setGeneratorForm({...generatorForm, product_description: e.target.value})}
                    placeholder={`${t('productDescription')}...`}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('productCategory')}</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.category}
                    onChange={(e) => setGeneratorForm({...generatorForm, category: e.target.value, custom_category: e.target.value === 'custom' ? generatorForm.custom_category : ''})}
                  >
                    <option value="">{t('selectCategory')}</option>
                    {PRODUCT_CATEGORIES[currentLanguage].map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {t('categoryHelpsTargetSeo')}
                  </p>
                </div>
                {generatorForm.category === 'custom' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">{t('customCategory')}</label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      value={generatorForm.custom_category}
                      onChange={(e) => setGeneratorForm({...generatorForm, custom_category: e.target.value})}
                      placeholder={t('enterCustomCategory')}
                      required
                    />
                  </div>
                )}
                
                {/* Nouveau champ Use Case */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('productUseCase')}</label>
                  <textarea
                    rows="2"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.use_case}
                    onChange={(e) => setGeneratorForm({...generatorForm, use_case: e.target.value})}
                    placeholder={t('enterUseCase')}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {t('useCaseHelpsContext')}
                  </p>
                </div>
                
                {/* Sélecteur de style d'image */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('imageStyle')}</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.image_style}
                    onChange={(e) => setGeneratorForm({...generatorForm, image_style: e.target.value})}
                  >
                    <option value="studio">{t('imageStyleStudio')}</option>
                    <option value="lifestyle">{t('imageStyleLifestyle')}</option>
                    <option value="detailed">{t('imageStyleDetailed')}</option>
                    <option value="technical">{t('imageStyleTechnical')}</option>
                    <option value="emotional">{t('imageStyleEmotional')}</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {t('imageStyleHelps')}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('numberOfImages')}</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={generatorForm.number_of_images}
                    onChange={(e) => setGeneratorForm({...generatorForm, number_of_images: parseInt(e.target.value)})}
                  >
                    <option value={1}>1 image</option>
                    <option value={2}>2 images</option>
                    <option value={3}>3 images</option>
                    <option value={4}>4 images</option>
                    <option value={5}>5 images</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {t('aiGenerateImages')}
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-md disabled:opacity-50 flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {t('processing')} {progressPercentage}%
                    </>
                  ) : t('generateSheet')}
                </button>

                {/* Progress Bar */}
                {loading && (
                  <div className="mt-4 space-y-2">
                    <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${progressPercentage}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between items-center text-sm text-gray-600">
                      <span>
                        {progressPercentage < 15 && `🔍 ${t('productAnalysis')}`}
                        {progressPercentage >= 15 && progressPercentage < 35 && `🤖 ${t('aiContentGeneration')}`}
                        {progressPercentage >= 35 && progressPercentage < 60 && `⚙️ ${t('characteristicsCreation')}`}
                        {progressPercentage >= 60 && progressPercentage < 80 && `🎨 ${t('imageGeneration')}`}
                        {progressPercentage >= 80 && progressPercentage < 100 && `✨ ${t('finalization')}`}
                        {progressPercentage >= 100 && `✅ ${t('completed')}!`}
                      </span>
                      <span className="font-semibold text-purple-600">{progressPercentage}%</span>
                    </div>
                  </div>
                )}
              </form>
            </div>

            {/* Generated Sheet Display */}
            {generatedSheet && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900 flex-1 mr-2">{t('sheetGenerated')}</h3>
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 flex-shrink-0">
                    <button
                      onClick={() => openExportModal(generatedSheet.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium flex items-center justify-center"
                    >
                      <svg className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      EXPORT
                    </button>
                    <button
                      onClick={openPublishModal}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium flex items-center justify-center"
                    >
                      <svg className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
                      </svg>
                      <span className="hidden sm:inline">{t('publishToStore')}</span>
                      <span className="sm:hidden">{t('publish')}</span>
                    </button>
                  </div>
                </div>
                
                {/* Product Images - Always show section */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">
                    🖼️ {t('productImages')} ({generatedSheet.number_of_images_generated || 0}) :
                  </h4>
                  
                  {generatedSheet.generated_images && generatedSheet.generated_images.length > 0 ? (
                    <div className="border-2 border-purple-200 rounded-xl p-4 bg-gradient-to-br from-purple-50 to-blue-50">
                      <div className={`grid gap-4 ${generatedSheet.generated_images?.length === 1 ? 'grid-cols-1' : 'grid-cols-2 md:grid-cols-3'}`}>
                        {generatedSheet.generated_images?.map((imageBase64, index) => (
                          <div key={index} className="relative">
                            <img 
                              src={`data:image/png;base64,${imageBase64}`}
                              alt={`${generatedSheet.product_name} - Image ${index + 1}`}
                              className="w-full h-48 object-cover rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300"
                              onError={(e) => {
                                console.log('Image loading error, trying as JPEG');
                                e.target.src = `data:image/jpeg;base64,${imageBase64}`;
                              }}
                            />
                            <div className="absolute top-2 right-2 bg-white bg-opacity-75 text-gray-800 text-xs px-2 py-1 rounded">
                              {index + 1}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="text-center mt-4">
                        <p className="text-sm text-green-700 font-medium">
                          📸 {t('professionalProductImages')}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {generatedSheet.generated_images?.length || 0} {t('optimizedImagesForEcommerce')}
                        </p>
                      </div>
                    </div>
                  ) : generatedSheet.product_image_base64 ? (
                    // Fallback pour l'ancienne structure (single image)
                    <div className="border-2 border-purple-200 rounded-xl p-4 bg-gradient-to-br from-purple-50 to-blue-50">
                      <img 
                        src={`data:image/png;base64,${generatedSheet.product_image_base64}`}
                        alt={generatedSheet.product_name}
                        className="w-full max-w-md mx-auto rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300"
                        onError={(e) => {
                          console.log('Image loading error, trying as JPEG');
                          e.target.src = `data:image/jpeg;base64,${generatedSheet.product_image_base64}`;
                        }}
                      />
                      <div className="text-center mt-3">
                        <p className="text-sm text-green-700 font-medium">
                          📸 Image professionnelle du produit
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Image optimisée pour l'e-commerce
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="border-2 border-gray-200 rounded-xl p-8 bg-gray-50 text-center">
                      <div className="text-6xl mb-4">🖼️</div>
                      <p className="text-gray-600 font-medium mb-2">Images en cours de génération...</p>
                      <p className="text-sm text-gray-500">
                        Génération d'images professionnelles pour votre produit
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900">{t('optimizedTitle')} :</h4>
                    <p className="text-gray-700">{generatedSheet.generated_title}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('marketingDescription')} :</h4>
                    <p className="text-gray-700">{generatedSheet.marketing_description}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('keyFeatures')} :</h4>
                    <ul className="list-disc list-inside text-gray-700">
                      {generatedSheet.key_features.map((feature, index) => (
                        <li key={index}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('seoTags')} :</h4>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {generatedSheet.seo_tags.map((tag, index) => (
                        <span key={index} className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('priceSuggestions')} :</h4>
                    <p className="text-gray-700 mb-3">{generatedSheet.price_suggestions}</p>
                    
                    {/* ✅ NOUVEAU: Système PriceTruth - Prix vérifiés multi-sources */}
                    <PriceTruthDisplay 
                      productName={generatedSheet.product_name || generatedSheet.generated_title}
                      className="mt-4"
                    />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('targetAudience')} :</h4>
                    <p className="text-gray-700">{generatedSheet.target_audience}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{t('callToAction')} :</h4>
                    <p className="text-gray-700">{generatedSheet.call_to_action}</p>
                  </div>
                </div>
                
                {/* ContentAnalytics Feedback System - Main Sheet */}
                {generatedSheet.generation_id && (
                  <div className="mt-6 pt-6 border-t">
                    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-gray-900 mb-2">{t('feedbackTitle')}</h4>
                      <p className="text-gray-600 text-sm mb-4">{t('feedbackQuestion')}</p>
                      
                      {feedbackSubmitted[generatedSheet.generation_id] !== undefined ? (
                        // Feedback déjà soumis
                        <div className="flex items-center justify-center bg-green-100 rounded-lg p-3">
                          <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span className="text-green-700 font-medium">{t('feedbackThanks')}</span>
                        </div>
                      ) : (
                        // Boutons de feedback
                        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                          <button
                            onClick={() => submitFeedback(generatedSheet.generation_id, true)}
                            disabled={feedbackSubmitting[generatedSheet.generation_id]}
                            className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium transition duration-200"
                          >
                            {feedbackSubmitting[generatedSheet.generation_id] ? (
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-4a2 2 0 012-2h2.5" />
                              </svg>
                            )}
                            {feedbackSubmitting[generatedSheet.generation_id] ? t('feedbackSubmitting') : t('feedbackUseful')}
                          </button>
                          
                          <button
                            onClick={() => submitFeedback(generatedSheet.generation_id, false)}
                            disabled={feedbackSubmitting[generatedSheet.generation_id]}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium transition duration-200"
                          >
                            {feedbackSubmitting[generatedSheet.generation_id] ? (
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-.999 4.125m.023-8.25c-.076-.365-.183-.718-.31-1.056a13.265 13.265 0 00-1.299-2.497m1.609 3.553v.943a6.01 6.01 0 01-1.619 4.1c-.835 1.09-2.237 1.47-3.581.822a4.73 4.73 0 01-2.66-2.94c-.24-.852-.240-1.793.017-2.654M6.75 15a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 0v-3.675A55.378 55.378 0 003.75 9.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                            )}
                            {feedbackSubmitting[generatedSheet.generation_id] ? t('feedbackSubmitting') : t('feedbackNotUseful')}
                          </button>
                        </div>
                      )}
                      
                      <p className="text-xs text-gray-500 mt-3 text-center">{t('feedbackHelp')}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Subscription Tab - NOUVEAU: Version complète avec SubscriptionManager */}
        {activeTab === 'subscription' && (
          <div className="space-y-6" data-tab="subscription">
            {/* Error message display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <div className="flex items-center">
                  <div className="text-red-600 mr-3">⚠️</div>
                  <div className="text-red-800 font-medium">{error}</div>
                </div>
              </div>
            )}
            
            {/* ✅ NOUVEAU: Remplacement par le SubscriptionManager complet */}
            <SubscriptionManager user={user} />
          </div>
        )}
        
        {/* Account Management Tab */}
        {activeTab === 'account' && (
          <div className="space-y-6" data-tab="account">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">👤 Gestion de compte</h2>
            
            {/* Account Info Section */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations personnelles</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Adresse email</label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                  <p className="text-xs text-gray-500 mt-1">L'email ne peut pas être modifié</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Plan d'abonnement</label>
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      user?.subscription_plan === 'premium' ? 'bg-purple-100 text-purple-800' :
                      user?.subscription_plan === 'pro' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {user?.subscription_plan === 'premium' ? '🏆 Premium' :
                       user?.subscription_plan === 'pro' ? '⭐ Pro' :
                       '🆓 Gratuit'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Usage Statistics */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistiques d'utilisation</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{user?.sheets_generated || 0}</div>
                  <div className="text-sm text-gray-600">Fiches générées</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {user?.sheets_limit === Infinity ? '∞' : (user?.sheets_limit || 0)}
                  </div>
                  <div className="text-sm text-gray-600">Limite mensuelle</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    {user?.subscription_plan === 'premium' ? '100%' :
                     user?.subscription_plan === 'pro' ? '80%' : '20%'}
                  </div>
                  <div className="text-sm text-gray-600">Fonctionnalités</div>
                </div>
              </div>
            </div>
            
            {/* Security Section */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sécurité</h3>
              
              <div className="space-y-4">
                <button className="w-full md:w-auto px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
                  🔒 Changer le mot de passe
                </button>
                
                <button className="w-full md:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  📧 Vérifier l'email
                </button>
              </div>
            </div>
            
            {/* Danger Zone */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-4">⚠️ Zone dangereuse</h3>
              
              <div className="space-y-4">
                <p className="text-sm text-red-700">
                  Les actions suivantes sont irréversibles. Procédez avec prudence.
                </p>
                
                <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                  🗑️ Supprimer le compte
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* AI FEATURES TAB - Premium Only */}
        {activeTab === 'ai-features' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">🤖 {t('aiFeatures')} - Fonctionnalités IA Avancées</h2>
              
              {(user?.subscription_plan === 'gratuit') && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">{t('premiumRequired')}</h3>
                  <p className="text-yellow-700 mb-4">{t('premiumRequiredDesc')}</p>
                  <button 
                    onClick={() => setActiveTab('subscription')}
                    className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700"
                  >
                    {t('upgradeToPro')}
                  </button>
                </div>
              )}
              
              {(user?.subscription_plan === 'pro' || user?.subscription_plan === 'premium') && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* SEO Analysis */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 {t('seoAnalysis')}</h3>
                    <div className="space-y-4">
                      <input
                        type="text"
                        placeholder="Nom du produit"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={seoAnalysisForm.product_name}
                        onChange={(e) => setSeoAnalysisForm({...seoAnalysisForm, product_name: e.target.value})}
                      />
                      <textarea
                        placeholder="Description du produit"
                        rows="3"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={seoAnalysisForm.product_description}
                        onChange={(e) => setSeoAnalysisForm({...seoAnalysisForm, product_description: e.target.value})}
                      />
                      <input
                        type="text"
                        placeholder="Mots-clés cibles (séparés par virgules)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={seoAnalysisForm.target_keywords}
                        onChange={(e) => setSeoAnalysisForm({...seoAnalysisForm, target_keywords: e.target.value})}
                      />
                      <button
                        onClick={handleSeoAnalysis}
                        disabled={seoAnalysisLoading}
                        className="w-full bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
                      >
                        {seoAnalysisLoading ? 'Analyse en cours...' : 'Analyser SEO'}
                      </button>
                    </div>
                    
                    {seoAnalysisResult && (
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <h4 className="font-semibold text-green-800 mb-2">Résultats de l'analyse SEO:</h4>
                        <div className="text-sm text-green-700 space-y-2">
                          <p><strong>Titre optimisé:</strong> {seoAnalysisResult.optimized_title}</p>
                          <p><strong>Score contenu:</strong> {seoAnalysisResult.content_score}/10</p>
                          <p><strong>Mots-clés:</strong> {seoAnalysisResult.seo_keywords?.join(', ')}</p>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Competitor Analysis */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🏢 {t('competitorAnalysis')}</h3>
                    <div className="space-y-4">
                      <input
                        type="text"
                        placeholder="Nom du produit"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={competitorAnalysisForm.product_name}
                        onChange={(e) => setCompetitorAnalysisForm({...competitorAnalysisForm, product_name: e.target.value})}
                      />
                      <input
                        type="text"
                        placeholder="Catégorie (ex: électronique, mode)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={competitorAnalysisForm.category}
                        onChange={(e) => setCompetitorAnalysisForm({...competitorAnalysisForm, category: e.target.value})}
                      />
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={competitorAnalysisForm.analysis_depth}
                        onChange={(e) => setCompetitorAnalysisForm({...competitorAnalysisForm, analysis_depth: e.target.value})}
                      >
                        <option value="standard">Analyse Standard</option>
                        <option value="deep">Analyse Approfondie</option>
                        <option value="premium">Analyse Premium</option>
                      </select>
                      <button
                        onClick={handleCompetitorAnalysis}
                        disabled={competitorAnalysisLoading}
                        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        {competitorAnalysisLoading ? 'Analyse en cours...' : 'Analyser Concurrence'}
                      </button>
                    </div>
                    
                    {competitorAnalysisResult && (
                      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h4 className="font-semibold text-blue-800 mb-2">Analyse Concurrentielle:</h4>
                        <div className="text-sm text-blue-700 space-y-2">
                          <p><strong>Concurrents analysés:</strong> {competitorAnalysisResult.competitors_found}</p>
                          <p><strong>Position marché:</strong> {competitorAnalysisResult.market_position}</p>
                          <p><strong>Prix moyen:</strong> {competitorAnalysisResult.avg_price_range?.average}€</p>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Price Optimization */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">💰 {t('priceOptimization')}</h3>
                    <div className="space-y-4">
                      <input
                        type="text"
                        placeholder="Nom du produit"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={priceOptimizationForm.product_name}
                        onChange={(e) => setPriceOptimizationForm({...priceOptimizationForm, product_name: e.target.value})}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="number"
                          placeholder="Prix actuel (€)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={priceOptimizationForm.current_price}
                          onChange={(e) => setPriceOptimizationForm({...priceOptimizationForm, current_price: e.target.value})}
                        />
                        <input
                          type="number"
                          placeholder="Coût produit (€)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={priceOptimizationForm.cost_price}
                          onChange={(e) => setPriceOptimizationForm({...priceOptimizationForm, cost_price: e.target.value})}
                        />
                      </div>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={priceOptimizationForm.pricing_strategy}
                        onChange={(e) => setPriceOptimizationForm({...priceOptimizationForm, pricing_strategy: e.target.value})}
                      >
                        <option value="competitive">Stratégie Concurrentielle</option>
                        <option value="penetration">Pénétration Marché</option>
                        <option value="skimming">Écrémage</option>
                        <option value="value">Basée sur la Valeur</option>
                      </select>
                      <button
                        onClick={handlePriceOptimization}
                        disabled={priceOptimizationLoading}
                        className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                      >
                        {priceOptimizationLoading ? 'Optimisation en cours...' : 'Optimiser Prix'}
                      </button>
                    </div>
                    
                    {priceOptimizationResult && (
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <h4 className="font-semibold text-green-800 mb-2">Prix Optimisé:</h4>
                        <div className="text-sm text-green-700 space-y-2">
                          <p><strong>Prix recommandé:</strong> {priceOptimizationResult.recommended_price}€</p>
                          <p><strong>Marge brute:</strong> {priceOptimizationResult.margin_analysis?.gross_margin}%</p>
                          <p><strong>Position:</strong> {priceOptimizationResult.market_positioning}</p>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Multilingual Translation */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🌍 {t('multilingualTranslation')}</h3>
                    <div className="space-y-4">
                      <textarea
                        placeholder="Texte à traduire"
                        rows="3"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={translationForm.source_text}
                        onChange={(e) => setTranslationForm({...translationForm, source_text: e.target.value})}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={translationForm.source_language}
                          onChange={(e) => setTranslationForm({...translationForm, source_language: e.target.value})}
                        >
                          <option value="fr">Français</option>
                          <option value="en">Anglais</option>
                          <option value="es">Espagnol</option>
                        </select>
                        <select
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={translationForm.target_languages[0]}
                          onChange={(e) => setTranslationForm({...translationForm, target_languages: [e.target.value]})}
                        >
                          <option value="en">Vers Anglais</option>
                          <option value="es">Vers Espagnol</option>
                          <option value="de">Vers Allemand</option>
                          <option value="it">Vers Italien</option>
                        </select>
                      </div>
                      <button
                        onClick={handleMultilingualTranslation}
                        disabled={translationLoading}
                        className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {translationLoading ? 'Traduction en cours...' : 'Traduire'}
                      </button>
                    </div>
                    
                    {translationResult && (
                      <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                        <h4 className="font-semibold text-indigo-800 mb-2">Traductions:</h4>
                        <div className="text-sm text-indigo-700 space-y-2">
                          {Object.entries(translationResult.translations || {}).map(([lang, text]) => (
                            <div key={lang} className="border-b border-indigo-200 pb-2">
                              <p><strong>{lang.toUpperCase()}:</strong> {text}</p>
                              <p className="text-xs">Qualité: {translationResult.quality_scores?.[lang]}/10</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Product Variants */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🔄 {t('productVariants')}</h3>
                    <div className="space-y-4">
                      <input
                        type="text"
                        placeholder="Produit de base"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={variantsForm.base_product}
                        onChange={(e) => setVariantsForm({...variantsForm, base_product: e.target.value})}
                      />
                      <textarea
                        placeholder="Description du produit de base"
                        rows="2"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={variantsForm.base_description}
                        onChange={(e) => setVariantsForm({...variantsForm, base_description: e.target.value})}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={variantsForm.number_of_variants}
                          onChange={(e) => setVariantsForm({...variantsForm, number_of_variants: parseInt(e.target.value)})}
                        >
                          <option value="3">3 Variantes</option>
                          <option value="5">5 Variantes</option>
                          <option value="7">7 Variantes</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Types (couleur, taille)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={variantsForm.variant_types.join(', ')}
                          onChange={(e) => setVariantsForm({...variantsForm, variant_types: e.target.value.split(',').map(t => t.trim())})}
                        />
                      </div>
                      <button
                        onClick={handleProductVariants}
                        disabled={variantsLoading}
                        className="w-full bg-pink-600 text-white py-2 rounded-lg hover:bg-pink-700 disabled:opacity-50"
                      >
                        {variantsLoading ? 'Génération en cours...' : 'Générer Variantes'}
                      </button>
                    </div>
                    
                    {variantsResult && (
                      <div className="mt-4 p-4 bg-pink-50 border border-pink-200 rounded-lg">
                        <h4 className="font-semibold text-pink-800 mb-2">Variantes Générées:</h4>
                        <div className="text-sm text-pink-700 space-y-2">
                          {variantsResult.variants?.map((variant, index) => (
                            <div key={index} className="border-b border-pink-200 pb-2">
                              <p><strong>{variant.variant_name}</strong></p>
                              <p className="text-xs">{variant.marketing_angle} - {variant.suggested_price}€</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Boutiques Tab */}
        {(activeTab === 'integrations' || activeTab === 'stores') && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-4 sm:p-6">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">🛒 {t('ecommerceIntegrations')} - Connexions Marketplace</h2>
              
              {/* Preview of Available Platforms - Always Visible */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🌟 Plateformes Disponibles</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3 sm:gap-4">
                  {[
                    { name: 'Shopify', icon: '🛍️', platform: 'shopify', desc: 'E-commerce leader' },
                    { name: 'WooCommerce', icon: '🏪', platform: 'woocommerce', desc: 'WordPress store' },
                    { name: 'Amazon', icon: '📦', platform: 'amazon', desc: 'Marketplace global' },
                    { name: 'eBay', icon: '🔨', platform: 'ebay', desc: 'Ventes aux enchères' },
                    { name: 'Etsy', icon: '🎨', platform: 'etsy', desc: 'Produits créatifs' },
                    { name: 'Facebook', icon: '👥', platform: 'facebook', desc: 'Social commerce' },
                    { name: 'Google Shopping', icon: '🔍', platform: 'google-shopping', desc: 'Recherche Google' }
                  ].map((store) => (
                    <button
                      key={store.platform}
                      onClick={async () => {
                        console.log('DEBUG - Button clicked for platform:', store.platform, 'User plan:', user?.subscription_plan);
                        if (user?.subscription_plan === 'gratuit') {
                          // For free users, show upgrade message
                          setActiveTab('subscription');
                        } else if (store.platform === 'amazon') {
                          // Amazon est géré dans la section dédiée ci-dessous
                          // Scroll vers la section Amazon
                          document.getElementById('amazon-integration-section')?.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'start' 
                          });
                        } else {
                          // For other platforms, open connection modal
                          setSelectedPlatform(store.platform);
                          setShowConnectStoreModal(true);
                        }
                      }}
                      className={`p-3 sm:p-4 border-2 rounded-lg text-center transition-colors cursor-pointer ${
                        (store.platform === 'amazon' && (selectedPlatform === 'amazon' || selectedPlatform === 'amazon-integration')) || 
                        (store.platform !== 'amazon' && selectedPlatform === store.platform)
                          ? 'border-purple-500 bg-purple-50' 
                          : 'border-gray-200 bg-gray-50 hover:border-purple-500 hover:bg-purple-50'
                      }`}
                    >
                      <div className="text-2xl sm:text-3xl mb-1 sm:mb-2">
                        {store.platform === 'amazon' && selectedPlatform === 'amazon' ? '⏳' : store.icon}
                      </div>
                      <div className="text-xs sm:text-sm font-medium text-gray-700 mb-1">{store.name}</div>
                      <div className="text-xs text-gray-500">
                        {store.platform === 'amazon' ? (
                          selectedPlatform === 'amazon' ? 'Connexion...' :
                          amazonConnectionStatus === 'connected' ? 'Connecté ✅' :
                          amazonConnectionStatus === 'revoked' ? 'Déconnecté ❌' :
                          amazonConnectionStatus === 'error' ? 'Erreur ⚠️' :
                          'Marketplace global'
                        ) : store.desc}
                      </div>
                      {user?.subscription_plan === 'gratuit' && (
                        <div className="mt-2 text-xs text-purple-600 font-medium">
                          Cliquez pour connecter
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
              
              {(user?.subscription_plan === 'gratuit') && (
                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4 sm:p-6 mb-6">
                  <div className="flex items-start">
                    <div className="text-2xl mr-3">🚀</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-yellow-800 mb-2">{t('premiumRequired')}</h3>
                      <p className="text-yellow-700 mb-4">
                        Connectez vos boutiques en ligne et publiez automatiquement vos fiches produits sur toutes les plateformes e-commerce.
                      </p>
                      <div className="text-sm text-yellow-600 mb-4">
                        ✨ <strong>Fonctionnalités Premium :</strong>
                        <ul className="mt-2 space-y-1 ml-4">
                          <li>• Connexion illimitée aux boutiques</li>
                          <li>• Publication automatique des produits</li>
                          <li>• Synchronisation des stocks et prix</li>
                          <li>• Analytics des ventes par plateforme</li>
                        </ul>
                      </div>
                      <button 
                        onClick={() => setActiveTab('subscription')}
                        className="bg-gradient-to-r from-yellow-600 to-orange-600 text-white px-6 py-3 rounded-lg hover:from-yellow-700 hover:to-orange-700 font-medium text-sm sm:text-base"
                      >
                        {t('upgradeToPro')} 🎯
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Section Amazon Integration - Gestion complète */}
              <div id="amazon-integration-section" className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🛒 Gestion Amazon SP-API</h3>
                <AmazonIntegrationCard
                  amazonConnectionStatus={amazonConnectionStatus}
                  selectedPlatform={selectedPlatform}
                  onConnect={handleAmazonConnection}
                  onDisconnect={handleAmazonDisconnection}
                  showConfirmDialog={true}
                  size="normal"
                />
              </div>

              {(user?.subscription_plan === 'pro' || user?.subscription_plan === 'premium') && (
                <>
                  {/* Connect New Store */}
                  <div className="mb-6">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 space-y-2 sm:space-y-0">
                      <h3 className="text-lg font-semibold text-gray-900">{t('connectStore')}</h3>
                      <button
                        onClick={() => setShowConnectStoreModal(true)}
                        className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center justify-center text-sm sm:text-base"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        Nouvelle Connexion
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3 sm:gap-4">
                      {[
                        { name: 'Shopify', icon: '🛍️', platform: 'shopify' },
                        { name: 'WooCommerce', icon: '🏪', platform: 'woocommerce' },
                        { name: 'eBay', icon: '🔨', platform: 'ebay' },
                        { name: 'Etsy', icon: '🎨', platform: 'etsy' },
                        { name: 'Facebook', icon: '👥', platform: 'facebook' },
                        { name: 'Google Shopping', icon: '🔍', platform: 'google-shopping' }
                      ].map((store) => (
                        <button
                          key={store.platform}
                          onClick={() => {
                            setSelectedPlatform(store.platform);
                            setShowConnectStoreModal(true);
                          }}
                          className="p-3 sm:p-4 border-2 border-gray-200 rounded-lg text-center hover:border-purple-500 hover:bg-purple-50 transition-colors"
                        >
                          <div className="text-2xl sm:text-3xl mb-1 sm:mb-2">{store.icon}</div>
                          <div className="text-xs sm:text-sm font-medium text-gray-700">{store.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Connected Stores */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('manageStores')}</h3>
                    {connectedStores.length > 0 ? (
                      <div className="space-y-3">
                        {connectedStores.map((store) => (
                          <div key={store.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border border-gray-200 rounded-lg space-y-3 sm:space-y-0">
                            <div className="flex items-center space-x-3">
                              <div className="text-2xl">
                                {store.platform === 'shopify' && '🛍️'}
                                {store.platform === 'woocommerce' && '🏪'}
                                {store.platform === 'amazon' && '📦'}
                                {store.platform === 'ebay' && '🔨'}
                                {store.platform === 'etsy' && '🎨'}
                                {store.platform === 'facebook' && '👥'}
                                {store.platform === 'google_shopping' && '🔍'}
                              </div>
                              <div>
                                <h4 className="font-medium text-gray-900">{store.store_name}</h4>
                                <p className="text-sm text-gray-500">{store.platform.charAt(0).toUpperCase() + store.platform.slice(1)}</p>
                              </div>
                            </div>
                            <div className="flex items-center justify-between sm:justify-end space-x-3">
                              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                                store.is_active 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {store.is_active ? 'Actif' : 'Inactif'}
                              </div>
                              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                Gérer
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <div className="text-4xl mb-4">🏪</div>
                        <p>Aucune boutique connectée</p>
                        <p className="text-sm">Connectez votre première boutique pour commencer</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Integration Logs */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('integrationLogs')}</h3>
                    {integrationLogs.length > 0 ? (
                      <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                        {integrationLogs.map((log) => (
                          <div key={log.id} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
                            <div className="flex items-center space-x-3">
                              <div className={`w-2 h-2 rounded-full ${
                                log.status === 'success' ? 'bg-green-500' : 
                                log.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                              }`}></div>
                              <span className="text-sm text-gray-700">{log.action}</span>
                              <span className="text-xs text-gray-500">{log.platform}</span>
                            </div>
                            <span className="text-xs text-gray-400">
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <div className="text-2xl mb-2">📋</div>
                        <p>Aucun log d'intégration</p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
        
        {/* Analytics Pro Tab */}
        {(activeTab === 'premium-analytics' || activeTab === 'analytics') && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 {t('premiumAnalytics')} - Analytics Avancées</h2>
              
              {(user?.subscription_plan === 'gratuit') && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">{t('premiumRequired')}</h3>
                  <p className="text-yellow-700 mb-4">{t('premiumRequiredDesc')}</p>
                  <button 
                    onClick={() => setActiveTab('subscription')}
                    className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700"
                  >
                    {t('upgradeToPro')}
                  </button>
                </div>
              )}
              
              {(user?.subscription_plan === 'pro' || user?.subscription_plan === 'premium') && (
                <>
                  {/* Timeframe Selector */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Période d'Analyse</h3>
                      <select
                        value={analyticsTimeframe}
                        onChange={(e) => setAnalyticsTimeframe(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="7d">7 derniers jours</option>
                        <option value="30d">30 derniers jours</option>
                        <option value="90d">90 derniers jours</option>
                        <option value="1y">12 derniers mois</option>
                      </select>
                    </div>
                  </div>
                  
                  {analyticsLoading ? (
                    <div className="text-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                      <p className="mt-4 text-gray-600">Chargement des analytics...</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      
                      {/* Product Performance Analytics */}
                      <div className="border border-gray-200 rounded-lg p-6">
                        <h4 className="text-lg font-semibold text-gray-900 mb-4">{t('productPerformance')}</h4>
                        {productPerformance && productPerformance.success ? (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{productPerformance.summary?.total_views || 0}</div>
                                <div className="text-sm text-gray-600">Vues Total</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">{productPerformance.summary?.total_exports || 0}</div>
                                <div className="text-sm text-gray-600">Exports</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{productPerformance.summary?.total_publishes || 0}</div>
                                <div className="text-sm text-gray-600">Publications</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">{productPerformance.summary?.avg_engagement_score || 0}</div>
                                <div className="text-sm text-gray-600">Score Engagement</div>
                              </div>
                            </div>
                            
                            {productPerformance.metrics && productPerformance.metrics.length > 0 ? (
                              <div className="mt-4">
                                <h5 className="font-medium text-gray-900 mb-2">Top Produits:</h5>
                                <div className="space-y-2">
                                  {productPerformance.metrics.slice(0, 5).map((product, index) => (
                                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                      <span className="text-sm text-gray-700">{product.product_name}</span>
                                      <span className="text-sm font-medium text-purple-600">{product.engagement_score}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <p className="text-gray-500 text-center py-4">Aucune donnée de performance disponible</p>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-center py-4">Erreur de chargement des données de performance</p>
                        )}
                      </div>
                      
                      {/* Integration Performance Analytics */}
                      <div className="border border-gray-200 rounded-lg p-6">
                        <h4 className="text-lg font-semibold text-gray-900 mb-4">{t('integrationPerformance')}</h4>
                        {integrationPerformance && integrationPerformance.success ? (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{integrationPerformance.summary?.total_platforms || 0}</div>
                                <div className="text-sm text-gray-600">Plateformes</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">{integrationPerformance.summary?.total_publishes || 0}</div>
                                <div className="text-sm text-gray-600">Publications</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{integrationPerformance.summary?.overall_success_rate || 0}%</div>
                                <div className="text-sm text-gray-600">Taux de Réussite</div>
                              </div>
                            </div>
                            
                            {integrationPerformance.platforms && integrationPerformance.platforms.length > 0 ? (
                              <div className="mt-4">
                                <h5 className="font-medium text-gray-900 mb-2">Performance par Plateforme:</h5>
                                <div className="space-y-2">
                                  {integrationPerformance.platforms.map((platform, index) => (
                                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                      <span className="text-sm text-gray-700 capitalize">{platform.platform}</span>
                                      <span className="text-sm font-medium text-green-600">{platform.success_rate}%</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <p className="text-gray-500 text-center py-4">Aucune donnée d'intégration disponible</p>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-center py-4">Erreur de chargement des données d'intégration</p>
                        )}
                      </div>
                      
                      {/* User Engagement Analytics */}
                      <div className="border border-gray-200 rounded-lg p-6">
                        <h4 className="text-lg font-semibold text-gray-900 mb-4">{t('userEngagement')}</h4>
                        {userEngagement && userEngagement.success ? (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{userEngagement.engagement_metrics?.total_sheets_generated || 0}</div>
                                <div className="text-sm text-gray-600">Fiches Générées</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{userEngagement.engagement_metrics?.total_images_generated || 0}</div>
                                <div className="text-sm text-gray-600">Images IA</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">{Object.keys(userEngagement.engagement_metrics?.platform_usage || {}).length}</div>
                                <div className="text-sm text-gray-600">Plateformes</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">{userEngagement.engagement_metrics?.favorite_styles?.length || 0}</div>
                                <div className="text-sm text-gray-600">Styles Favoris</div>
                              </div>
                            </div>
                            
                            {userEngagement.engagement_metrics?.favorite_styles && userEngagement.engagement_metrics.favorite_styles.length > 0 && (
                              <div className="mt-4">
                                <h5 className="font-medium text-gray-900 mb-2">Styles d'Images Préférés:</h5>
                                <div className="flex flex-wrap gap-2">
                                  {userEngagement.engagement_metrics.favorite_styles.map((style, index) => (
                                    <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                                      {style}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-center py-4">Erreur de chargement des données d'engagement</p>
                        )}
                      </div>
                      
                      {/* Load Analytics Button */}
                      <div className="text-center">
                        <button
                          onClick={loadPremiumAnalytics}
                          className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700"
                        >
                          🔄 Actualiser les Analytics
                        </button>
                      </div>
                      
                    </div>
                  )}
                </>
              )}
            </div>
            {/* Amazon SP-API Integration Component */}
            {selectedPlatform === 'amazon-integration' && (user?.subscription_plan === 'pro' || user?.subscription_plan === 'premium') && (
              <div className="mt-6">
                <div className="mb-4">
                  <button
                    onClick={() => setSelectedPlatform(null)}
                    className="text-purple-600 hover:text-purple-800 flex items-center"
                  >
                    ← Retour aux intégrations
                  </button>
                </div>
                <AmazonIntegration />
              </div>
            )}
          </div>
        )}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && stats && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{t('totalSheets')}</h3>
                <p className="text-3xl font-bold text-purple-600">{detailedAnalytics?.total_sheets || stats.total_sheets}</p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{t('thisMonth')}</h3>
                <p className="text-3xl font-bold text-green-600">{detailedAnalytics?.sheets_this_month || stats.sheets_this_month}</p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{t('thisWeek')}</h3>
                <p className="text-3xl font-bold text-blue-600">{detailedAnalytics?.sheets_this_week || 0}</p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{t('currentPlan')}</h3>
                <p className="text-lg font-semibold text-gray-900 capitalize">{detailedAnalytics?.subscription_plan || stats.subscription_plan}</p>
              </div>
            </div>
            
            {/* Sales Metrics Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{currentLanguage === 'fr' ? 'Ventes Totales' : 'Total Sales'}</h3>
                <p className="text-3xl font-bold text-green-600">
                  {detailedAnalytics?.total_sales || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {currentLanguage === 'fr' ? 'Produits vendus' : 'Products sold'}
                </p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{currentLanguage === 'fr' ? 'Revenu Total' : 'Total Revenue'}</h3>
                <p className="text-3xl font-bold text-purple-600">
                  €{(detailedAnalytics?.total_revenue || 0).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {currentLanguage === 'fr' ? 'Revenu généré' : 'Revenue generated'}
                </p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">{currentLanguage === 'fr' ? 'Taux de Conversion' : 'Conversion Rate'}</h3>
                <p className="text-3xl font-bold text-orange-600">
                  {((detailedAnalytics?.conversion_rate || 0)).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {currentLanguage === 'fr' ? 'Ventes par fiche' : 'Sales per sheet'}
                </p>
              </div>
            </div>
            
            {detailedAnalytics && (
              <>
                {/* Monthly & Weekly Sales */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">📈 {currentLanguage === 'fr' ? 'Ventes ce Mois' : 'Sales This Month'}</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{currentLanguage === 'fr' ? 'Nombre de ventes' : 'Number of sales'}</span>
                        <span className="text-2xl font-bold text-green-600">{detailedAnalytics?.sales_this_month || 0}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{currentLanguage === 'fr' ? 'Revenu ce mois' : 'Revenue this month'}</span>
                        <span className="text-2xl font-bold text-purple-600">€{(detailedAnalytics?.revenue_this_month || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">⚡ {currentLanguage === 'fr' ? 'Ventes cette Semaine' : 'Sales This Week'}</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{currentLanguage === 'fr' ? 'Nombre de ventes' : 'Number of sales'}</span>
                        <span className="text-2xl font-bold text-blue-600">{detailedAnalytics?.sales_this_week || 0}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{currentLanguage === 'fr' ? 'Revenu cette semaine' : 'Revenue this week'}</span>
                        <span className="text-2xl font-bold text-orange-600">€{(detailedAnalytics?.revenue_this_week || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Platform Sales Breakdown */}
                {detailedAnalytics?.platform_sales_breakdown && Object.keys(detailedAnalytics.platform_sales_breakdown).length > 0 && (
                  <div className="bg-white shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">🛒 {currentLanguage === 'fr' ? 'Ventes par Plateforme' : 'Sales by Platform'}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {Object.entries(detailedAnalytics?.platform_sales_breakdown || {}).map(([platform, data]) => (
                        <div key={platform} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900 capitalize">{platform}</span>
                            <span className="text-sm text-gray-500">{data.sales} ventes</span>
                          </div>
                          <div className="text-lg font-bold text-purple-600">€{(data.revenue || 0).toLocaleString()}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Analytics Sections */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Category Breakdown */}
                  <div className="bg-white shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">📊 {t('categoryBreakdown')}</h3>
                    {Object.keys(detailedAnalytics.category_breakdown).length > 0 ? (
                      <div className="space-y-3">
                        {Object.entries(detailedAnalytics.category_breakdown).map(([category, count]) => (
                          <div key={category} className="flex items-center justify-between">
                            <span className="text-gray-700">{category}</span>
                            <div className="flex items-center">
                              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                                <div 
                                  className="bg-purple-600 h-2 rounded-full" 
                                  style={{ width: `${(count / detailedAnalytics.total_sheets) * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-gray-900">{count}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">Aucune donnée disponible</p>
                    )}
                  </div>

                  {/* AI vs Simulated */}
                  <div className="bg-white shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">🤖 {t('generationType')}</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{t('artificialIntelligence')}</span>
                        <span className="text-xl font-bold text-green-600">{detailedAnalytics.ai_vs_simulated.IA}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">{t('simulatedGeneration')}</span>
                        <span className="text-xl font-bold text-blue-600">{detailedAnalytics.ai_vs_simulated.Simulé}</span>
                      </div>
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">{t('averageCharacteristics')}</span>
                          <span className="text-sm font-medium text-gray-900">{detailedAnalytics.average_features_per_sheet}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

                {/* Popular Keywords */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">🔥 {t('popularKeywords')}</h3>
                  {detailedAnalytics.popular_keywords.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {detailedAnalytics.popular_keywords.slice(0, 15).map((keyword, index) => (
                        <span 
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                        >
                          {keyword.word} <span className="ml-1 text-xs bg-purple-200 rounded-full px-2 py-0.5">{keyword.count}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500">Aucun mot-clé disponible</p>
                  )}
                </div>

                {/* Generation Trends */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">📈 {t('generationTrends')}</h3>
                  <div className="grid grid-cols-7 gap-2">
                    {detailedAnalytics.generation_trends.map((trend, index) => (
                      <div key={index} className="text-center">
                        <div className="text-xs text-gray-500 mb-2">
                          {new Date(trend.date).toLocaleDateString('fr-FR', { weekday: 'short' })}
                        </div>
                        <div className="bg-gray-100 rounded p-2 h-16 flex items-end justify-center">
                          <div 
                            className="bg-purple-500 rounded w-full transition-all duration-300"
                            style={{ height: `${trend.count > 0 ? Math.max((trend.count / Math.max(...detailedAnalytics.generation_trends.map(t => t.count))) * 100, 10) : 0}%` }}
                          ></div>
                        </div>
                        <div className="text-sm font-medium text-gray-900 mt-1">{trend.count}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t text-center">
                    <p className="text-sm text-gray-600">
                      {t('mostProductiveDay')} : <span className="font-medium text-purple-600">{detailedAnalytics.most_productive_day}</span>
                    </p>
                  </div>
                </div>
              </>
            )}

            {!detailedAnalytics && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-300 rounded w-1/4 mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-300 rounded"></div>
                    <div className="h-4 bg-gray-300 rounded w-5/6"></div>
                    <div className="h-4 bg-gray-300 rounded w-4/6"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* SEO Premium Tab */}
        {(activeTab === 'seo-premium' || activeTab === 'seo') && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">🚀 SEO Premium - Optimisation Automatique</h2>
              
              {/* Navigation des sous-onglets SEO */}
              <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex flex-wrap gap-2 md:flex-nowrap md:space-x-8 md:gap-0">
                  {['dashboard', 'setup', 'optimizations', 'trends', 'competitors', 'automation', 'stores', 'config', 'images', 'markets', 'amazon-seo'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveSEOTab(tab)}
                      className={`py-2 px-2 md:px-1 border-b-2 font-medium text-xs md:text-sm whitespace-nowrap flex-shrink-0 ${
                        activeSEOTab === tab
                          ? 'border-purple-500 text-purple-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab === 'dashboard' && '📊 Dashboard'}
                      {tab === 'setup' && '🚀 Configuration'}
                      {tab === 'optimizations' && '⚡ Optimisations'}
                      {tab === 'trends' && '📈 Tendances'}
                      {tab === 'competitors' && '🥊 Concurrents'}
                      {tab === 'automation' && '🤖 Automatisation'}
                      {tab === 'stores' && '🏪 Boutiques'}
                      {tab === 'config' && '⚙️ Paramètres'}
                      {tab === 'images' && '🖼️ Images'}
                      {tab === 'markets' && '🌍 Marchés'}
                      {tab === 'amazon-seo' && '🚀 SEO Amazon'}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Setup and Configuration Tab */}
              {activeSEOTab === 'setup' && (
                <div className="space-y-6">
                  {/* SEO Setup Validation */}
                  <div className="bg-white shadow rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">🚀 Configuration SEO Premium</h3>
                      <button
                        onClick={validateSEOSetup}
                        className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                      >
                        Vérifier Configuration
                      </button>
                    </div>
                    
                    {seoSetupValidation && (
                      <div className="space-y-4">
                        {/* Setup Status */}
                        <div className={`p-4 rounded-lg ${
                          seoSetupValidation.setup_complete 
                            ? 'bg-green-50 border border-green-200' 
                            : 'bg-yellow-50 border border-yellow-200'
                        }`}>
                          <div className="flex items-center">
                            <div className={`text-2xl mr-3 ${
                              seoSetupValidation.setup_complete ? 'text-green-600' : 'text-yellow-600'
                            }`}>
                              {seoSetupValidation.setup_complete ? '✅' : '⚠️'}
                            </div>
                            <div>
                              <h4 className="font-medium">
                                {seoSetupValidation.setup_complete 
                                  ? 'Configuration Complète' 
                                  : 'Configuration Incomplète'}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {seoSetupValidation.setup_complete 
                                  ? 'Votre SEO Premium est prêt à fonctionner' 
                                  : 'Quelques étapes sont encore nécessaires'}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Setup Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-blue-50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-blue-600">
                              {seoSetupValidation.connections_count}
                            </div>
                            <div className="text-sm text-gray-600">Boutiques Connectées</div>
                          </div>
                          <div className="bg-green-50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-green-600">
                              {seoSetupValidation.webhook_ready_count}
                            </div>
                            <div className="text-sm text-gray-600">Webhooks Configurés</div>
                          </div>
                          <div className="bg-purple-50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-purple-600">
                              {seoSetupValidation.product_sheets_count}
                            </div>
                            <div className="text-sm text-gray-600">Fiches Produits</div>
                          </div>
                          <div className="bg-orange-50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-orange-600">
                              {seoSetupValidation.seo_config_exists ? '✓' : '✗'}
                            </div>
                            <div className="text-sm text-gray-600">Config SEO</div>
                          </div>
                        </div>
                        
                        {/* Issues and Recommendations */}
                        {seoSetupValidation.issues && seoSetupValidation.issues.length > 0 && (
                          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <h4 className="font-medium text-red-800 mb-2">⚠️ Problèmes Détectés</h4>
                            <ul className="text-sm text-red-700 space-y-1">
                              {seoSetupValidation.issues.map((issue, idx) => (
                                <li key={idx}>• {issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {seoSetupValidation.recommendations && seoSetupValidation.recommendations.length > 0 && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-medium text-blue-800 mb-2">💡 Recommandations</h4>
                            <ul className="text-sm text-blue-700 space-y-1">
                              {seoSetupValidation.recommendations.map((rec, idx) => (
                                <li key={idx}>• {rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {/* Next Steps */}
                        {seoSetupValidation.next_steps && seoSetupValidation.next_steps.length > 0 && (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <h4 className="font-medium text-green-800 mb-2">🎯 Prochaines Étapes</h4>
                            <ul className="text-sm text-green-700 space-y-1">
                              {seoSetupValidation.next_steps.map((step, idx) => (
                                <li key={idx}>• {step}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Connection Status Dashboard */}
                  <div className="bg-white shadow rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">🔗 État des Connexions</h3>
                      <button
                        onClick={loadConnectionsStatus}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                        disabled={loadingConnections}
                      >
                        {loadingConnections ? 'Chargement...' : 'Actualiser'}
                      </button>
                    </div>
                    
                    {Object.keys(connectionsStatus).length > 0 ? (
                      <div className="space-y-4">
                        {Object.entries(connectionsStatus).map(([connectionId, connection]) => (
                          <div key={connectionId} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center">
                                <div className="text-2xl mr-3">
                                  {connection.platform === 'shopify' && '🛍️'}
                                  {connection.platform === 'woocommerce' && '🏪'}
                                  {connection.platform === 'amazon' && '📦'}
                                  {connection.platform === 'ebay' && '🔨'}
                                  {connection.platform === 'etsy' && '🎨'}
                                  {connection.platform === 'facebook' && '👥'}
                                  {connection.platform === 'google-shopping' && '🔍'}
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-900">{connection.store_name}</h4>
                                  <p className="text-sm text-gray-600 capitalize">{connection.platform}</p>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  connection.connection_health === 'healthy' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {connection.connection_health === 'healthy' ? '✓ Saine' : '✗ Problème'}
                                </span>
                                <button
                                  onClick={() => testConnection(connectionId)}
                                  className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700"
                                >
                                  Tester
                                </button>
                              </div>
                            </div>
                            
                            {/* Webhook Status */}
                            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                              <div className="flex items-center">
                                <span className={`w-3 h-3 rounded-full mr-2 ${
                                  connection.webhook_configured ? 'bg-green-500' : 'bg-yellow-500'
                                }`}></span>
                                <span className="text-sm text-gray-600">
                                  Webhook {connection.webhook_configured ? 'Configuré' : 'Non Configuré'}
                                </span>
                              </div>
                              {connection.webhook_url && (
                                <button
                                  onClick={() => loadWebhookGuide(connection.platform)}
                                  className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                                >
                                  Guide Setup
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">🔗</div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune connexion</h3>
                        <p className="text-gray-600 mb-4">Connectez vos boutiques e-commerce pour commencer</p>
                        <button
                          onClick={() => setActiveTab('integrations')}
                          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                        >
                          Connecter une Boutique
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* SEO Setup Wizard */}
                  <div className="bg-white shadow rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">🧙‍♂️ Assistant Configuration SEO</h3>
                      <button
                        onClick={startSEOWizard}
                        className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-pink-700"
                      >
                        Lancer l'Assistant
                      </button>
                    </div>
                    
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">🎯 Assistant de Configuration Guidée</h4>
                      <p className="text-sm text-gray-600 mb-3">
                        Suivez notre assistant étape par étape pour configurer votre SEO Premium automatique.
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="flex items-center">
                          <span className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs mr-2">1</span>
                          <span>Vérification des connexions</span>
                        </div>
                        <div className="flex items-center">
                          <span className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs mr-2">2</span>
                          <span>Configuration webhooks</span>
                        </div>
                        <div className="flex items-center">
                          <span className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs mr-2">3</span>
                          <span>Test complet du système</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Dashboard SEO */}
              {activeSEOTab === 'dashboard' && (
                <div className="space-y-6">
                  {loadingSEO ? (
                    <div className="animate-pulse">
                      <div className="h-4 bg-gray-300 rounded w-1/4 mb-4"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-300 rounded"></div>
                        <div className="h-4 bg-gray-300 rounded w-5/6"></div>
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* SEO Analytics Overview */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg p-6">
                          <h3 className="text-sm font-medium opacity-90">Optimisations Totales</h3>
                          <p className="text-3xl font-bold">{seoAnalytics?.total_optimizations || 0}</p>
                        </div>
                        <div className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg p-6">
                          <h3 className="text-sm font-medium opacity-90">Auto-Appliquées</h3>
                          <p className="text-3xl font-bold">{seoAnalytics?.auto_applied_optimizations || 0}</p>
                        </div>
                        <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg p-6">
                          <h3 className="text-sm font-medium opacity-90">Score de Confiance</h3>
                          <p className="text-3xl font-bold">{((seoAnalytics?.average_confidence_score || 0) * 100).toFixed(0)}%</p>
                        </div>
                        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg p-6">
                          <h3 className="text-sm font-medium opacity-90">Amélioration Performance</h3>
                          <p className="text-3xl font-bold">+{(seoAnalytics?.total_performance_improvement || 0).toFixed(1)}%</p>
                        </div>
                      </div>

                      {/* Quick Actions */}
                      <div className="bg-gray-50 rounded-lg p-6">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">🎯 Actions Rapides</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <button
                            onClick={() => triggerSEOScraping('trends')}
                            className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center"
                          >
                            📈 Scraper les Tendances
                          </button>
                          <button
                            onClick={() => triggerSEOScraping('competitors')}
                            className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center"
                          >
                            🥊 Analyser Concurrents
                          </button>
                        </div>
                      </div>

                      {/* Recent Optimizations */}
                      <div className="bg-white shadow rounded-lg p-6">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">⚡ Optimisations Récentes</h3>
                        {seoOptimizations && seoOptimizations.length > 0 ? (
                          <div className="space-y-4">
                            {seoOptimizations.slice(0, 5).map((opt, index) => (
                              <div key={index} className="border-l-4 border-purple-500 pl-4 py-3 bg-gray-50 rounded-r-lg">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <h4 className="font-medium text-gray-900">{opt.request?.suggested_title || 'Optimisation SEO'}</h4>
                                    <p className="text-sm text-gray-600">
                                      Confiance: {((opt.request?.confidence_score || 0) * 100).toFixed(0)}% | 
                                      Status: {opt.request?.status || 'pending'}
                                    </p>
                                  </div>
                                  <div className="flex space-x-2">
                                    {opt.request?.status === 'pending' && (
                                      <button
                                        onClick={() => applySEOOptimization(opt.request.id)}
                                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                                      >
                                        Appliquer
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500">Aucune optimisation récente</p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Optimizations Tab */}
              {activeSEOTab === 'optimizations' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium text-gray-900">⚡ Toutes les Optimisations</h3>
                    <button
                      onClick={() => {
                        if (sheets && sheets.length > 0) {
                          requestSEOOptimization(sheets[0].id);
                        }
                      }}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                    >
                      Nouvelle Optimisation
                    </button>
                  </div>
                  
                  {seoOptimizations && seoOptimizations.length > 0 ? (
                    <div className="space-y-4">
                      {seoOptimizations.map((opt, index) => (
                        <div key={index} className="bg-white border border-gray-200 rounded-lg p-6">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold text-gray-900">
                              {opt.request?.suggested_title || 'Optimisation SEO'}
                            </h4>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              opt.request?.status === 'completed' ? 'bg-green-100 text-green-800' :
                              opt.request?.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {opt.request?.status || 'pending'}
                            </span>
                          </div>
                          
                          {opt.request && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h5 className="font-medium text-gray-700 mb-2">Titre Suggéré:</h5>
                                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                                  {opt.request.suggested_title}
                                </p>
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-700 mb-2">Description Suggérée:</h5>
                                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                                  {opt.request.suggested_description}
                                </p>
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-700 mb-2">Mots-clés:</h5>
                                <div className="flex flex-wrap gap-2">
                                  {opt.request.suggested_keywords?.map((keyword, idx) => (
                                    <span key={idx} className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                                      {keyword}
                                    </span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-700 mb-2">Score de Confiance:</h5>
                                <div className="bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-purple-600 h-2 rounded-full" 
                                    style={{ width: `${(opt.request.confidence_score || 0) * 100}%` }}
                                  ></div>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">
                                  {((opt.request.confidence_score || 0) * 100).toFixed(0)}%
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {opt.request?.status === 'pending' && (
                            <div className="mt-4 flex space-x-3">
                              <button
                                onClick={() => applySEOOptimization(opt.request.id)}
                                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                              >
                                Appliquer
                              </button>
                              <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">
                                Rejeter
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">⚡</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune optimisation</h3>
                      <p className="text-gray-600">Commencez par générer des optimisations SEO pour vos produits</p>
                    </div>
                  )}
                </div>
              )}

              {/* Trends Tab */}
              {activeSEOTab === 'trends' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium text-gray-900">📈 Tendances SEO</h3>
                    <button
                      onClick={() => triggerSEOScraping('trends')}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                    >
                      Actualiser Tendances
                    </button>
                  </div>
                  
                  {seoTrends && seoTrends.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {seoTrends.map((trend, index) => (
                        <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-gray-900">{trend.keyword}</h4>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              trend.trend_direction === 'rising' ? 'bg-green-100 text-green-800' :
                              trend.trend_direction === 'falling' ? 'bg-red-100 text-red-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {trend.trend_direction === 'rising' ? '📈' : trend.trend_direction === 'falling' ? '📉' : '➡️'}
                              {trend.trend_direction}
                            </span>
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Volume de recherche:</span>
                              <span className="font-medium">{trend.search_volume?.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Concurrence:</span>
                              <span className={`font-medium ${
                                trend.competition_level === 'high' ? 'text-red-600' :
                                trend.competition_level === 'medium' ? 'text-yellow-600' :
                                'text-green-600'
                              }`}>
                                {trend.competition_level}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Source:</span>
                              <span className="font-medium">{trend.source}</span>
                            </div>
                            <div className="bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-purple-600 h-2 rounded-full" 
                                style={{ width: `${(trend.confidence_score || 0) * 100}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-gray-500">
                              Confiance: {((trend.confidence_score || 0) * 100).toFixed(0)}%
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">📈</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune tendance</h3>
                      <p className="text-gray-600">Cliquez sur "Actualiser Tendances" pour scraper les dernières données</p>
                    </div>
                  )}
                </div>
              )}

              {/* Competitors Tab */}
              {activeSEOTab === 'competitors' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium text-gray-900">🥊 Analyse Concurrentielle</h3>
                    <button
                      onClick={() => triggerSEOScraping('competitors')}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                      Analyser Concurrents
                    </button>
                  </div>
                  
                  {competitors && competitors.length > 0 ? (
                    <div className="space-y-4">
                      {competitors.map((competitor, index) => (
                        <div key={index} className="bg-white border border-gray-200 rounded-lg p-6">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold text-gray-900">{competitor.product_name}</h4>
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                              {competitor.platform}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div>
                              <span className="text-gray-600 text-sm">Prix:</span>
                              <p className="font-semibold text-green-600">€{competitor.price?.toFixed(2) || 0}</p>
                            </div>
                            <div>
                              <span className="text-gray-600 text-sm">Note:</span>
                              <p className="font-semibold text-yellow-600">⭐ {competitor.rating?.toFixed(1) || 0}</p>
                            </div>
                            <div>
                              <span className="text-gray-600 text-sm">Avis:</span>
                              <p className="font-semibold text-blue-600">{competitor.review_count?.toLocaleString() || 0}</p>
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <div>
                              <h5 className="font-medium text-gray-700 mb-1">Titre SEO:</h5>
                              <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                                {competitor.seo_title || 'Non disponible'}
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-700 mb-1">Description:</h5>
                              <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                                {competitor.seo_description || 'Non disponible'}
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium text-gray-700 mb-1">Mots-clés:</h5>
                              <div className="flex flex-wrap gap-2">
                                {competitor.keywords?.map((keyword, idx) => (
                                  <span key={idx} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                                    {keyword}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">🥊</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun concurrent</h3>
                      <p className="text-gray-600">Cliquez sur "Analyser Concurrents" pour scraper les données des concurrents</p>
                    </div>
                  )}
                </div>
              )}

              {/* Automation Tab */}
              {activeSEOTab === 'automation' && (
                <div className="space-y-6" data-automation-tab="true">
                  <h3 className="text-lg font-medium text-gray-900">🤖 Automatisation SEO</h3>
                  
                  {/* Onboarding Welcome for New Premium Users */}
                  {automationSettings && !automationSettings.onboarding_completed && (
                    <div className="bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-lg p-6 mb-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-bold text-lg flex items-center">
                            🎉 Bienvenue dans l'Automatisation SEO Premium !
                          </h4>
                          <p className="mt-2 text-sm">
                            Votre système de scraping automatique est maintenant configuré avec des paramètres optimaux.
                            Découvrez comment maximiser vos ventes avec l'IA.
                          </p>
                        </div>
                        <button
                          onClick={() => setShowAutomationOnboarding(true)}
                          className="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
                        >
                          🚀 Commencer le Tour
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Quick Setup Guide */}
                  {(!automationSettings?.scraping_enabled || automationSettings?.target_categories?.length === 0) && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                      <h4 className="font-bold text-blue-900 mb-3">⚡ Configuration Express (2 minutes)</h4>
                      <div className="space-y-3">
                        <div className="flex items-start">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">1</div>
                          <div>
                            <h5 className="font-medium text-blue-900">Activer le Scraping Automatique</h5>
                            <p className="text-sm text-blue-700">Collecte quotidienne des tendances de vos marchés</p>
                          </div>
                        </div>
                        <div className="flex items-start">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">2</div>
                          <div>
                            <h5 className="font-medium text-blue-900">Choisir vos Catégories Cibles</h5>
                            <p className="text-sm text-blue-700">Sélectionnez les marchés à surveiller (mode, tech, beauté...)</p>
                          </div>
                        </div>
                        <div className="flex items-start">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">3</div>
                          <div>
                            <h5 className="font-medium text-blue-900">Activer l'Optimisation (Optionnel)</h5>
                            <p className="text-sm text-blue-700">Mise à jour automatique de vos fiches selon les tendances</p>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setShowQuickSetup(true)}
                        className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                      >
                        🎯 Configuration Express
                      </button>
                    </div>
                  )}

                  {/* Success Metrics Preview */}
                  {automationSettings?.scraping_enabled && (
                    <div className="bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg p-6">
                      <h4 className="font-bold text-lg mb-4">📈 Votre Impact SEO Automatique</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                          <div className="text-3xl font-bold">{automationStats?.sheets_optimized || 0}</div>
                          <div className="text-sm opacity-90">Fiches Optimisées</div>
                          <div className="text-xs opacity-75">+{Math.floor(Math.random() * 25 + 15)}% ce mois</div>
                        </div>
                        <div className="text-center">
                          <div className="text-3xl font-bold">{automationStats?.trends_available || 0}</div>
                          <div className="text-sm opacity-90">Tendances Actives</div>
                          <div className="text-xs opacity-75">Mises à jour quotidiennes</div>
                        </div>
                        <div className="text-center">
                          <div className="text-3xl font-bold">{automationStats?.sheets_published || 0}</div>
                          <div className="text-sm opacity-90">Publications Auto</div>
                          <div className="text-xs opacity-75">Gain de temps estimé: {Math.floor((automationStats?.sheets_published || 0) * 15)}min</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {loadingAutomation ? (
                    <div className="animate-pulse space-y-4">
                      <div className="h-4 bg-gray-300 rounded w-1/3"></div>
                      <div className="h-20 bg-gray-300 rounded"></div>
                      <div className="h-4 bg-gray-300 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      
                      {/* Automation Settings */}
                      <div className="bg-white border border-gray-200 rounded-lg p-6">
                        <h4 className="font-bold text-gray-900 mb-4">⚙️ Paramètres d'Automatisation</h4>
                        <div className="space-y-6">
                          
                          {/* Scraping Enabled */}
                          <div className="flex items-center justify-between">
                            <div>
                              <h5 className="font-medium text-gray-900">🔍 Scraping Automatique</h5>
                              <p className="text-sm text-gray-600">Collecte automatiquement les données de tendances et concurrents</p>
                              <div className="text-xs text-green-600 mt-1">
                                ✅ Recommandé pour maximiser vos ventes
                              </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={automationSettings.scraping_enabled}
                                onChange={(e) => updateAutomationSettings({ scraping_enabled: e.target.checked })}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                          </div>

                          {/* Auto Optimization */}
                          <div className="flex items-center justify-between">
                            <div>
                              <h5 className="font-medium text-gray-900">⚡ Optimisation Automatique</h5>
                              <p className="text-sm text-gray-600">Applique automatiquement les optimisations SEO basées sur les tendances</p>
                              <div className="text-xs text-blue-600 mt-1">
                                💡 Améliore automatiquement vos titres et descriptions
                              </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={automationSettings.auto_optimization_enabled}
                                onChange={(e) => updateAutomationSettings({ auto_optimization_enabled: e.target.checked })}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                            </label>
                          </div>

                          {/* Auto Publication */}
                          <div className="flex items-center justify-between">
                            <div>
                              <h5 className="font-medium text-gray-900">📤 Publication Automatique</h5>
                              <p className="text-sm text-gray-600">Publie automatiquement les fiches optimisées sur vos boutiques connectées</p>
                              <div className="text-xs text-orange-600 mt-1">
                                ⚠️ Assurez-vous d'avoir des boutiques connectées
                              </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={automationSettings.auto_publication_enabled}
                                onChange={(e) => updateAutomationSettings({ auto_publication_enabled: e.target.checked })}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
                            </label>
                          </div>

                          {/* Scraping Frequency */}
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">⏰ Fréquence de Scraping</h5>
                            <select
                              value={automationSettings.scraping_frequency}
                              onChange={(e) => updateAutomationSettings({ scraping_frequency: e.target.value })}
                              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="daily">Quotidien (recommandé) 🔥</option>
                              <option value="weekly">Hebdomadaire 📅</option>
                            </select>
                            <p className="text-xs text-gray-500 mt-1">
                              Plus la fréquence est élevée, plus vos données sont fraîches
                            </p>
                          </div>

                          {/* Target Categories */}
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">🎯 Catégories Cibles</h5>
                            <p className="text-sm text-gray-600 mb-3">Sélectionnez les marchés à surveiller pour optimiser vos produits</p>
                            
                            {/* Popular Categories Quick Add */}
                            <div className="mb-3">
                              <p className="text-xs text-gray-500 mb-2">🔥 Catégories populaires :</p>
                              <div className="flex flex-wrap gap-2">
                                {['mode', 'tech', 'beauté', 'sport', 'maison', 'auto', 'jardin', 'bébé'].map(cat => (
                                  <button
                                    key={cat}
                                    onClick={() => {
                                      if (!automationSettings.target_categories?.includes(cat)) {
                                        const newCategories = [...(automationSettings.target_categories || []), cat];
                                        updateAutomationSettings({ target_categories: newCategories });
                                      }
                                    }}
                                    className={`px-3 py-1 text-xs rounded-full transition-colors ${
                                      automationSettings.target_categories?.includes(cat)
                                        ? 'bg-blue-500 text-white cursor-default'
                                        : 'bg-gray-200 text-gray-700 hover:bg-blue-100'
                                    }`}
                                  >
                                    {cat}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-3">
                              {automationSettings.target_categories?.map((category, idx) => (
                                <span 
                                  key={idx} 
                                  className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center"
                                >
                                  {category}
                                  <button 
                                    onClick={() => {
                                      const newCategories = automationSettings.target_categories.filter((_, i) => i !== idx);
                                      updateAutomationSettings({ target_categories: newCategories });
                                    }}
                                    className="ml-2 text-blue-600 hover:text-blue-800"
                                  >
                                    ×
                                  </button>
                                </span>
                              ))}
                            </div>
                            <div className="flex gap-2">
                              <input
                                type="text"
                                placeholder="Ajouter une catégorie personnalisée"
                                className="flex-1 p-2 border border-gray-300 rounded"
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter' && e.target.value.trim()) {
                                    const newCategories = [...(automationSettings.target_categories || []), e.target.value.trim()];
                                    updateAutomationSettings({ target_categories: newCategories });
                                    e.target.value = '';
                                  }
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Status Indicators */}
                      {automationStats && (
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-3">📊 État des Automatisations</h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className={`p-3 rounded-lg text-center ${
                              automationStats.automation_enabled.scraping ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              <div className="font-medium">Scraping</div>
                              <div className="text-sm">
                                {automationStats.automation_enabled.scraping ? '✅ Actif' : '❌ Inactif'}
                              </div>
                            </div>
                            <div className={`p-3 rounded-lg text-center ${
                              automationStats.automation_enabled.optimization ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              <div className="font-medium">Optimisation</div>
                              <div className="text-sm">
                                {automationStats.automation_enabled.optimization ? '✅ Actif' : '❌ Inactif'}
                              </div>
                            </div>
                            <div className={`p-3 rounded-lg text-center ${
                              automationStats.automation_enabled.publication ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              <div className="font-medium">Publication</div>
                              <div className="text-sm">
                                {automationStats.automation_enabled.publication ? '✅ Actif' : '❌ Inactif'}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Test Automation */}
                      {user?.subscription_plan === 'premium' && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                          <h4 className="font-medium text-gray-900 mb-2">🧪 Test d'Automatisation (Premium)</h4>
                          <p className="text-sm text-gray-600 mb-4">
                            Testez manuellement vos paramètres d'automatisation pour vérifier leur bon fonctionnement.
                          </p>
                          <button
                            onClick={testAutomation}
                            disabled={testingAutomation}
                            className={`px-4 py-2 rounded-lg text-white font-medium ${
                              testingAutomation 
                                ? 'bg-gray-400 cursor-not-allowed' 
                                : 'bg-orange-500 hover:bg-orange-600'
                            }`}
                          >
                            {testingAutomation ? '🔄 Test en cours...' : '🚀 Tester l\'automatisation'}
                          </button>
                        </div>
                      )}

                      {/* Help Section */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <h4 className="font-medium text-gray-900 mb-2">💡 Conseils pour Maximiser vos Résultats</h4>
                        <ul className="text-sm text-gray-700 space-y-2">
                          <li>• <strong>Scraping Quotidien :</strong> Collectez les tendances Google et Amazon chaque jour pour rester compétitif</li>
                          <li>• <strong>Catégories Spécifiques :</strong> Choisissez 3-5 catégories principales pour des résultats optimaux</li>
                          <li>• <strong>Optimisation Automatique :</strong> Laissez l'IA mettre à jour vos titres/descriptions selon les tendances</li>
                          <li>• <strong>Publication Sécurisée :</strong> Connectez vos boutiques avant d'activer la publication automatique</li>
                          <li>• <strong>Monitoring :</strong> Surveillez vos statistiques régulièrement pour ajuster la stratégie</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Stores Configuration Tab - Premium Only */}
              {activeSEOTab === 'stores' && (
                <div className="space-y-4 md:space-y-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
                    <h3 className="text-lg font-medium text-gray-900">🏪 Configuration SEO par Boutique</h3>
                    <div className="text-sm text-gray-600">
                      Configurez le scraping SEO spécifiquement pour chaque boutique connectée
                    </div>
                  </div>

                  {loadingStoresConfig ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                      <span className="ml-2 text-gray-600">Chargement des configurations...</span>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Summary Analytics */}
                      {storesAnalytics && (
                        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 md:p-6 border border-purple-200">
                          <h4 className="font-medium text-purple-900 mb-4">📊 Résumé des Boutiques</h4>
                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                            <div className="text-center p-2 md:p-0">
                              <div className="text-xl md:text-2xl font-bold text-purple-600">{storesAnalytics.summary.total_stores}</div>
                              <div className="text-xs md:text-sm text-purple-700">Boutiques</div>
                            </div>
                            <div className="text-center p-2 md:p-0">
                              <div className="text-xl md:text-2xl font-bold text-green-600">{storesAnalytics.summary.stores_with_scraping_enabled}</div>
                              <div className="text-xs md:text-sm text-green-700">Scraping Actif</div>
                            </div>
                            <div className="text-center p-2 md:p-0">
                              <div className="text-xl md:text-2xl font-bold text-blue-600">{storesAnalytics.summary.stores_with_auto_optimization}</div>
                              <div className="text-xs md:text-sm text-blue-700">Auto-Optimisation</div>
                            </div>
                            <div className="text-center p-2 md:p-0">
                              <div className="text-xl md:text-2xl font-bold text-orange-600">{storesAnalytics.summary.total_optimizations_all_stores}</div>
                              <div className="text-xs md:text-sm text-orange-700">Optimisations Total</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Stores List */}
                      {storesSeConfig.length === 0 ? (
                        <div className="text-center py-8 md:py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 mx-2 md:mx-0">
                          <div className="text-3xl md:text-4xl mb-4">🏪</div>
                          <h3 className="text-base md:text-lg font-medium text-gray-900 mb-2 px-4">Aucune boutique connectée</h3>
                          <p className="text-sm md:text-base text-gray-600 mb-4 px-4">Connectez vos boutiques e-commerce pour configurer le SEO automatique par boutique.</p>
                          <button
                            onClick={() => setActiveTab('integrations')}
                            className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 text-sm md:text-base"
                          >
                            Connecter une Boutique
                          </button>
                        </div>
                      ) : (
                        <div className="grid gap-6">
                          {storesSeConfig.map((storeData) => {
                            const { store, seo_config } = storeData;
                            const analytics = storesAnalytics?.stores_analytics.find(a => a.store_id === store.id);
                            
                            return (
                              <div key={store.id} className="bg-white border border-gray-200 rounded-lg p-4 md:p-6 hover:shadow-md transition-shadow">
                                <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 space-y-2 md:space-y-0">
                                  <div className="flex items-center space-x-3">
                                    <div className="text-xl md:text-2xl">
                                      {store.platform === 'shopify' && '🛍️'}
                                      {store.platform === 'woocommerce' && '🏪'}
                                      {store.platform === 'amazon' && '📦'}
                                      {store.platform === 'ebay' && '🔨'}
                                      {store.platform === 'etsy' && '🎨'}
                                    </div>
                                    <div>
                                      <h4 className="font-medium text-gray-900 text-sm md:text-base">{store.store_name}</h4>
                                      <p className="text-xs md:text-sm text-gray-600 capitalize">{store.platform}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <div className={`w-2 h-2 md:w-3 md:h-3 rounded-full ${seo_config.scraping_enabled ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                                    <span className="text-xs md:text-sm text-gray-600">
                                      {seo_config.scraping_enabled ? 'Actif' : 'Inactif'}
                                    </span>
                                  </div>
                                </div>

                                {/* Store Analytics */}
                                {analytics && (
                                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 md:gap-4 mb-4 p-3 md:p-4 bg-gray-50 rounded-lg">
                                    <div className="text-center p-1">
                                      <div className="text-sm md:text-lg font-semibold text-blue-600">{analytics.target_keywords_count}</div>
                                      <div className="text-xs text-gray-600">Mots-clés</div>
                                    </div>
                                    <div className="text-center p-1">
                                      <div className="text-sm md:text-lg font-semibold text-green-600">{analytics.target_categories_count}</div>
                                      <div className="text-xs text-gray-600">Catégories</div>
                                    </div>
                                    <div className="text-center p-1">
                                      <div className="text-sm md:text-lg font-semibold text-purple-600">{analytics.total_optimizations_applied}</div>
                                      <div className="text-xs text-gray-600">Optimisations</div>
                                    </div>
                                    <div className="text-center p-1">
                                      <div className="text-lg font-semibold text-orange-600">
                                        {analytics.average_performance_improvement > 0 ? 
                                          `+${(analytics.average_performance_improvement * 100).toFixed(1)}%` : 
                                          'N/A'
                                        }
                                      </div>
                                      <div className="text-xs text-gray-600">Performance</div>
                                    </div>
                                  </div>
                                )}

                                {/* Configuration Summary */}
                                <div className="space-y-2 mb-4">
                                  <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-600">Fréquence de scraping:</span>
                                    <span className="font-medium">{seo_config.scraping_frequency}</span>
                                  </div>
                                  <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-600">Auto-optimisation:</span>
                                    <span className={`font-medium ${seo_config.auto_optimization_enabled ? 'text-green-600' : 'text-red-600'}`}>
                                      {seo_config.auto_optimization_enabled ? 'Activée' : 'Désactivée'}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-600">Dernière analyse:</span>
                                    <span className="font-medium">
                                      {seo_config.last_scraping_run 
                                        ? new Date(seo_config.last_scraping_run).toLocaleDateString('fr-FR')
                                        : 'Jamais'
                                      }
                                    </span>
                                  </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex flex-wrap gap-2">
                                  <button
                                    onClick={() => openStoreConfigModal(store, seo_config)}
                                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                  >
                                    ⚙️ Configurer
                                  </button>
                                  <button
                                    onClick={() => testStoreScraping(store.id)}
                                    disabled={testingStoreScrapingId === store.id || !seo_config.scraping_enabled}
                                    className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  >
                                    {testingStoreScrapingId === store.id ? '🔄 Test...' : '🧪 Tester'}
                                  </button>
                                  {seo_config.auto_optimization_enabled && (
                                    <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                                      Auto-optimisation active
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Configuration Tab */}
              {activeSEOTab === 'config' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">⚙️ Configuration SEO</h3>
                  
                  {seoConfig ? (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="space-y-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Scraping Automatique</h4>
                            <p className="text-sm text-gray-600">Active le scraping automatique des tendances</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={seoConfig.scraping_enabled || false}
                              onChange={(e) => updateSeoConfig({ scraping_enabled: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Optimisation Automatique</h4>
                            <p className="text-sm text-gray-600">Applique automatiquement les optimisations approuvées</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={seoConfig.auto_optimization_enabled || false}
                              onChange={(e) => updateSeoConfig({ auto_optimization_enabled: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Publication Automatique</h4>
                            <p className="text-sm text-gray-600">Publie automatiquement sur les plateformes connectées</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={seoConfig.auto_publication_enabled || false}
                              onChange={(e) => updateSeoConfig({ auto_publication_enabled: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Fréquence de Scraping</h4>
                          <select
                            value={seoConfig.scraping_frequency || 'daily'}
                            onChange={(e) => updateSeoConfig({ scraping_frequency: e.target.value })}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="daily">Quotidien (recommandé) 🔥</option>
                            <option value="weekly">Hebdomadaire 📅</option>
                          </select>
                        </div>
                        
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Plateformes Cibles</h4>
                          <div className="flex flex-wrap gap-2">
                            {seoConfig.target_platforms?.map((platform, idx) => (
                              <span key={idx} className="bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm">
                                {platform}
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Seuil de Confiance</h4>
                          <input
                            type="range"
                            min="0.1"
                            max="1"
                            step="0.1"
                            value={seoConfig.confidence_threshold || 0.7}
                            onChange={(e) => updateSeoConfig({ confidence_threshold: parseFloat(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                          />
                          <p className="text-sm text-gray-600 mt-1">
                            {((seoConfig.confidence_threshold || 0.7) * 100).toFixed(0)}% minimum requis
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">⚙️</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration non disponible</h3>
                      <p className="text-gray-600">Chargement de la configuration en cours...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Images Tab - NOUVEAU: Gestion des Images */}
              {activeSEOTab === 'images' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">🖼️ Gestion des Images</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Configurez la génération et l'inclusion d'images dans vos fiches produit
                      </p>
                    </div>
                  </div>
                  
                  <ImageManagementSettings 
                    userConfig={user}
                    onConfigUpdate={(updatedConfig) => {
                      // Update user object with new settings
                      setUser(prevUser => ({
                        ...prevUser,
                        generate_images: updatedConfig.generate_images,
                        include_images_manual: updatedConfig.include_images_manual
                      }));
                      
                      // Show success notification
                      setNotification({
                        message: 'Préférences d\'images mises à jour avec succès',
                        type: 'success'
                      });
                    }}
                  />
                </div>
              )}

              {/* Markets Tab - NOUVEAU: Gestion des Marchés Multi-Pays */}
              {activeSEOTab === 'markets' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">🌍 Marchés Multi-Pays</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Configurez le scraping de prix et les gardes prix par pays pour optimiser vos publications
                      </p>
                    </div>
                  </div>
                  
                  <MarketSettingsManager 
                    userConfig={user}
                    onConfigUpdate={(updatedConfig) => {
                      // Show success notification
                      setNotification({
                        message: `Paramètres de marché ${updatedConfig.country_code} mis à jour avec succès`,
                        type: 'success'
                      });
                    }}
                  />
                </div>
              )}

              {/* Amazon SEO Tab - NOUVEAU: Optimisation SEO Amazon A9/A10 */}
              {activeSEOTab === 'amazon-seo' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">🚀 SEO Amazon A9/A10</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Optimisez vos listings Amazon selon les algorithmes A9 (recherche) et A10 (recommandations)
                      </p>
                    </div>
                  </div>
                  
                  <AmazonSEOOptimizer 
                    userConfig={user}
                    onConfigUpdate={(updatedConfig) => {
                      // Show success notification
                      setNotification({
                        message: 'Listing SEO Amazon optimisé avec succès',
                        type: 'success'
                      });
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Admin Tab - Enhanced with Contacts */}
        {activeTab === 'admin' && user?.is_admin && (
          <AdminPanel 
            affiliateConfig={affiliateConfig}
            loadingAffiliateConfig={loadingAffiliateConfig}
            loadAffiliateConfig={loadAffiliateConfig}
          />
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 space-y-4 sm:space-y-0">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">{t('historyTitle')}</h2>
                  {sheets.length > 0 && (
                    <p className="text-sm text-gray-600 mt-1">
                      💡 {t('bulkSelectHelp')}
                    </p>
                  )}
                </div>
                
                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                  {/* Selection Controls */}
                  {sheets.length > 0 && (
                    <div className="flex items-center space-x-2 text-sm">
                      <span className="text-gray-600">
                        {selectedSheets.length} {t('selectedSheetsCount')}
                      </span>
                      {selectedSheets.length < sheets.length ? (
                        <button
                          onClick={selectAllSheets}
                          className="text-purple-600 hover:text-purple-800 font-medium"
                        >
                          {t('selectAll')}
                        </button>
                      ) : (
                        <button
                          onClick={deselectAllSheets}
                          className="text-purple-600 hover:text-purple-800 font-medium"
                        >
                          {t('deselectAll')}
                        </button>
                      )}
                    </div>
                  )}
                  
                  {/* Bulk Publish Button - Always visible */}
                  <button
                    onClick={openBulkPublishModal}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center justify-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
                    </svg>
                    {selectedSheets.length > 0 
                      ? `Publier sélection (${selectedSheets.length})`
                      : t('publishAll')
                    }
                  </button>
                  
                  {/* Export Button - Only for selected sheets */}
                  {selectedSheets.length > 0 && (
                    <button
                      onClick={() => openExportModal('selected')}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center justify-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      EXPORT ({selectedSheets.length})
                    </button>
                  )}
                  
                  {/* Export All Button - When no selection */}
                  {selectedSheets.length === 0 && sheets.length > 0 && (
                    <button
                      onClick={() => openExportModal('all')}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center justify-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {t('exportAll')}
                    </button>
                  )}
                </div>
              </div>
              
              {sheets.length === 0 ? (
                <p className="text-gray-500 text-center py-8">{t('noSheetsGenerated') || "Aucune fiche produit générée pour le moment."}</p>
              ) : (
                <div className="space-y-4">
                  {sheets.map((sheet) => (
                    <div key={sheet.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start space-x-3">
                        {/* Selection Checkbox */}
                        <div className="flex items-center pt-1">
                          <input
                            type="checkbox"
                            checked={selectedSheets.includes(sheet.id)}
                            onChange={() => toggleSheetSelection(sheet.id)}
                            className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                          />
                        </div>
                        
                        {/* Sheet Content */}
                        <div className="flex-1 cursor-pointer" onClick={() => setSelectedSheet(sheet)}>
                          <div className="flex items-center space-x-2">
                            <h3 className="font-semibold text-gray-900">{sheet.product_name}</h3>
                            {sheet.is_ai_generated && (
                              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                                ✨ IA
                              </span>
                            )}
                            
                            {/* ✅ NOUVEAU: Badge prix vérifié dans l'historique */}
                            <PriceTruthBadge 
                              productName={sheet.product_name}
                              className="ml-2"
                            />
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{sheet.generated_title}</p>
                          <p className="text-xs text-gray-500 mt-2">
                            {t('generatedOn')} : {new Date(sheet.created_at).toLocaleString('fr-FR')}
                          </p>
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2">
                          {/* Individual Publish Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              // Set single sheet for individual publishing
                              setGeneratedSheet(sheet);
                              openPublishModal();
                            }}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs font-medium flex items-center"
                            title={t('publishToStore')}
                          >
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
                            </svg>
                            <span className="hidden sm:inline">{t('publish').toLowerCase()}</span>
                          </button>
                          
                          {/* View Details Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedSheet(sheet);
                            }}
                            className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                          >
                            {t('viewDetails')}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Account Management Tab */}
        {activeTab === 'account' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('accountManagement')}</h2>
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center">
                    <div className="text-red-600 mr-3">⚠️</div>
                    <div className="text-red-800 font-medium">{error}</div>
                  </div>
                </div>
              )}

              {/* Account Info */}
              <div className="mb-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  📋 {t('accountInfo')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">{t('name')}</p>
                    <p className="text-lg text-gray-900">{user?.name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Email</p>
                    <p className="text-lg text-gray-900">{user?.email}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">{t('subscriptionPlan')}</p>
                    <p className="text-lg text-gray-900 capitalize">
                      {stats?.subscription_plan || 'gratuit'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">{t('generatedSheets')}</p>
                    <p className="text-lg text-gray-900">{stats?.total_sheets || 0}</p>
                  </div>
                </div>
              </div>

              {/* Account Actions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Change Password Section */}
                <div className="p-6 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="text-lg font-semibold text-blue-900 mb-3">🔒 {t('accountSecurity')}</h4>
                  <p className="text-blue-700 text-sm mb-4">
                    {t('changePasswordSecurity')}
                  </p>
                  <button
                    onClick={() => setShowPasswordModal(true)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md transition duration-300 flex items-center justify-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 12H9v4a2 2 0 01-2 2H5v-6a2 2 0 011-1.732l4.055-2.055A7 7 0 1121 9z" />
                    </svg>
                    {t('changePassword')}
                  </button>
                </div>

                {/* Delete Account Section */}
                <div className="p-6 bg-red-50 rounded-lg border border-red-200">
                  <h4 className="text-lg font-semibold text-red-900 mb-3">🗑️ {t('accountDeletion')}</h4>
                  <p className="text-red-700 text-sm mb-4">
                    {t('deleteAccountWarning')}
                  </p>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-md transition duration-300 flex items-center justify-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    {t('deleteAccount')}
                  </button>
                </div>

              </div>

              {/* Account Tips */}
              <div className="mt-8 p-6 bg-yellow-50 rounded-lg border border-yellow-200">
                <h4 className="text-lg font-semibold text-yellow-900 mb-3">💡 {t('securityTips')}</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-yellow-800">
                  <div>
                    <h5 className="font-semibold mb-1">🔑 {t('password')}</h5>
                    <p>{t('passwordTip')}</p>
                  </div>
                  <div>
                    <h5 className="font-semibold mb-1">📧 {t('email')}</h5>
                    <p>{t('emailTip')}</p>
                  </div>
                  <div>
                    <h5 className="font-semibold mb-1">💾 {t('data')}</h5>
                    <p>{t('dataTip')}</p>
                  </div>
                  <div>
                    <h5 className="font-semibold mb-1">🔓 {t('loginTip')}</h5>
                    <p>{t('loginTipText')}</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

      {/* Chatbot */}
      <Chatbot />
      
      {/* Contact Form - Always accessible */}
      <ContactForm />
      
      {/* Sheet Details Modal */}
      {selectedSheet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Détails de la Fiche Produit</h2>
              <button
                onClick={() => setSelectedSheet(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Product Info */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">📦 Informations du Produit</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p><strong>Nom du produit :</strong> {selectedSheet.product_name}</p>
                  <p><strong>Description originale :</strong> {selectedSheet.original_description}</p>
                  <p><strong>Généré le :</strong> {new Date(selectedSheet.created_at).toLocaleString('fr-FR')}</p>
                  {selectedSheet.is_ai_generated && (
                    <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mt-2">
                      ✨ Généré par IA
                    </span>
                  )}
                </div>
              </div>

              {/* Generated Title */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🎯 Titre Généré</h3>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-blue-900 font-medium">{selectedSheet.generated_title}</p>
                </div>
              </div>

              {/* Marketing Description */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">📝 {t('marketingDescription')}</h3>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-purple-900">{selectedSheet.marketing_description}</p>
                </div>
              </div>

              {/* Product Images */}
              {selectedSheet.generated_images && selectedSheet.generated_images.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    🖼️ Images du Produit ({selectedSheet.generated_images.length})
                  </h3>
                  <div className={`grid gap-4 ${selectedSheet.generated_images.length === 1 ? 'grid-cols-1' : 'grid-cols-2 md:grid-cols-3'}`}>
                    {selectedSheet.generated_images.map((imageBase64, index) => (
                      <div key={index} className="relative">
                        <img 
                          src={`data:image/png;base64,${imageBase64}`}
                          alt={`${selectedSheet.product_name} - Image ${index + 1}`}
                          className="w-full h-48 object-cover rounded-lg shadow-lg"
                          onError={(e) => {
                            e.target.src = `data:image/jpeg;base64,${imageBase64}`;
                          }}
                        />
                        <div className="absolute top-2 right-2 bg-white bg-opacity-75 text-gray-800 text-xs px-2 py-1 rounded">
                          {index + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Features */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">⭐ {t('keyFeatures')}</h3>
                <div className="bg-green-50 rounded-lg p-4">
                  <ul className="space-y-2">
                    {selectedSheet.key_features?.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-green-600 mr-2">✓</span>
                        <span className="text-green-900">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* SEO Tags */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🔍 Tags SEO</h3>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="flex flex-wrap gap-2">
                    {selectedSheet.seo_tags?.map((tag, index) => (
                      <span key={index} className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded text-sm">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Price Suggestions */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">💰 {t('priceSuggestions')}</h3>
                <div className="bg-orange-50 rounded-lg p-4">
                  <p className="text-orange-900">{selectedSheet.price_suggestions}</p>
                </div>
              </div>

              {/* Target Audience */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🎯 {t('targetAudience')}</h3>
                <div className="bg-indigo-50 rounded-lg p-4">
                  <p className="text-indigo-900">{selectedSheet.target_audience}</p>
                </div>
              </div>

              {/* Call to Action */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🚀 {t('callToAction')}</h3>
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-red-900 font-medium">{selectedSheet.call_to_action}</p>
                </div>
              </div>

              {/* ContentAnalytics Feedback System */}
              {selectedSheet.generation_id && (
                <div className="border-t pt-6 mt-6">
                  <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('feedbackTitle')}</h3>
                    <p className="text-gray-600 text-sm mb-4">{t('feedbackQuestion')}</p>
                    
                    {feedbackSubmitted[selectedSheet.generation_id] !== undefined ? (
                      // Feedback déjà soumis
                      <div className="flex items-center justify-center bg-green-100 rounded-lg p-3">
                        <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-green-700 font-medium">{t('feedbackThanks')}</span>
                      </div>
                    ) : (
                      // Boutons de feedback
                      <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                        <button
                          onClick={() => submitFeedback(selectedSheet.generation_id, true)}
                          disabled={feedbackSubmitting[selectedSheet.generation_id]}
                          className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium transition duration-200"
                        >
                          {feedbackSubmitting[selectedSheet.generation_id] ? (
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          ) : (
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-4a2 2 0 012-2h2.5" />
                            </svg>
                          )}
                          {feedbackSubmitting[selectedSheet.generation_id] ? t('feedbackSubmitting') : t('feedbackUseful')}
                        </button>
                        
                        <button
                          onClick={() => submitFeedback(selectedSheet.generation_id, false)}
                          disabled={feedbackSubmitting[selectedSheet.generation_id]}
                          className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium transition duration-200"
                        >
                          {feedbackSubmitting[selectedSheet.generation_id] ? (
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          ) : (
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-.999 4.125m.023-8.25c-.076-.365-.183-.718-.31-1.056a13.265 13.265 0 00-1.299-2.497m1.609 3.553v.943a6.01 6.01 0 01-1.619 4.1c-.835 1.09-2.237 1.47-3.581.822a4.73 4.73 0 01-2.66-2.94c-.24-.852-.240-1.793.017-2.654M6.75 15a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 0v-3.675A55.378 55.378 0 003.75 9.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                          )}
                          {feedbackSubmitting[selectedSheet.generation_id] ? t('feedbackSubmitting') : t('feedbackNotUseful')}
                        </button>
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500 mt-3 text-center">{t('feedbackHelp')}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                onClick={() => openExportModal(null, selectedSheet.id)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                EXPORT
              </button>
              <button
                onClick={() => {
                  setGeneratedSheet(selectedSheet);
                  setSelectedSheet(null); // Fermer automatiquement le modal de détail
                  openPublishModal();
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md flex items-center justify-center text-sm font-medium"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
                </svg>
                {t('publish')}
              </button>
              <button
                onClick={() => setSelectedSheet(null)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      <ExportModal />

      {/* Publish to Store Modal */}
      {showPublishModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 flex items-center">
              <svg className="w-6 h-6 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
              </svg>
              {t('publishToStore')}
            </h2>
            
            {/* Success Message */}
            {publishSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-green-800 text-sm font-medium">{publishSuccess}</p>
                </div>
              </div>
            )}
            
            {/* Error Message */}
            {publishError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <p className="text-red-800 text-sm font-medium">{publishError}</p>
                </div>
              </div>
            )}
            
            {/* Store Selection */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('selectStore')}
                </label>
                <select
                  value={selectedStore}
                  onChange={(e) => setSelectedStore(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  disabled={publishingLoading}
                >
                  <option value="">{t('selectStore')}</option>
                  {connectedStores.map((store) => (
                    <option key={store.id} value={store.id}>
                      {store.store_name} ({store.platform})
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Product Info */}
              {generatedSheet && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-1">{t('productToPublish')}</h4>
                  <p className="text-sm text-gray-700">{generatedSheet.generated_title}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {generatedSheet.key_features?.length || 0} caractéristiques, {generatedSheet.seo_tags?.length || 0} tags SEO
                  </p>
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={closePublishModal}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  disabled={publishingLoading}
                >
                  Annuler
                </button>
                <button
                  onClick={publishToStore}
                  disabled={!selectedStore || publishingLoading || publishSuccess}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {publishingLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {t('publishingToStore')}...
                    </>
                  ) : t('publishProduct')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Publish Modal */}
      {showBulkPublishModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-2 sm:p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[95vh] overflow-y-auto">
            {/* Header */}
            <div className="flex justify-between items-center p-4 sm:p-6 border-b">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 flex items-center">
                <svg className="w-5 h-5 sm:w-6 sm:h-6 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2 5m2-5h8m4 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6h8z" />
                </svg>
                {t('publishSelectedSheets')} ({selectedSheets.length})
              </h2>
              <button
                onClick={closeBulkPublishModal}
                className="text-gray-500 hover:text-gray-700 p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-4 sm:p-6">
              {/* Success/Error Messages */}
              {message && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 text-sm font-medium">{message}</p>
                </div>
              )}
              
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 text-sm font-medium">{error}</p>
                </div>
              )}

              {/* Store Selection */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('selectStore')}
                  </label>
                  <select
                    value={selectedStore}
                    onChange={(e) => setSelectedStore(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                    disabled={bulkPublishingLoading}
                  >
                    <option value="">{t('selectStore')}</option>
                    {connectedStores.map((store) => (
                      <option key={store.id} value={store.id}>
                        {store.store_name} ({store.platform})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Selected Sheets Preview */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">
                      Fiches sélectionnées ({selectedSheets.length})
                    </h4>
                    {selectedSheets.length === sheets.length && sheets.length > 1 && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Toutes sélectionnées
                      </span>
                    )}
                  </div>
                  {selectedSheets.length === sheets.length && sheets.length > 1 && (
                    <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                      💡 Toutes vos fiches ont été automatiquement sélectionnées pour publication
                    </div>
                  )}
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {sheets.filter(sheet => selectedSheets.includes(sheet.id)).map((sheet) => (
                      <div key={sheet.id} className="flex items-center space-x-2 text-sm">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-gray-700">{sheet.product_name}</span>
                        {sheet.is_ai_generated && (
                          <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">IA</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bulk Publish Results */}
                {bulkPublishResults.length > 0 && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3">Résultats de publication</h4>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {bulkPublishResults.map((result, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm">
                          <div className={`w-2 h-2 rounded-full ${result.success ? 'bg-green-500' : 'bg-red-500'}`}></div>
                          <span className="text-gray-700">{result.sheet.product_name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded ${result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {result.success ? 'Publié' : 'Échec'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={closeBulkPublishModal}
                    className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                    disabled={bulkPublishingLoading}
                  >
                    Annuler
                  </button>
                  <button
                    onClick={bulkPublishToStore}
                    disabled={!selectedStore || bulkPublishingLoading}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {bulkPublishingLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {currentLanguage === 'fr' ? 'Publication en cours...' : 'Publishing...'}
                      </>
                    ) : currentLanguage === 'fr' ? 
                      `Publier ${selectedSheets.length} fiche${selectedSheets.length > 1 ? 's' : ''}` :
                      `Publish ${selectedSheets.length} sheet${selectedSheets.length > 1 ? 's' : ''}`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connect Store Modal */}
      {showConnectStoreModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-2 sm:p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-lg max-h-[95vh] overflow-y-auto">
            {/* Header */}
            <div className="flex justify-between items-center p-4 sm:p-6 border-b">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 flex items-center">
                <svg className="w-5 h-5 sm:w-6 sm:h-6 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {t('connectStore')}
              </h2>
              <button
                onClick={() => {
                  setShowConnectStoreModal(false);
                  setSelectedPlatform('');
                }}
                className="text-gray-500 hover:text-gray-700 p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-4 sm:p-6">
              {!selectedPlatform ? (
                <>
                  {/* Platform Selection */}
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">
                    Choisissez votre plateforme e-commerce
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
                    {[
                      { name: 'Shopify', icon: '🛍️', platform: 'shopify', color: 'bg-green-50 hover:bg-green-100 border-green-200' },
                      { name: 'WooCommerce', icon: '🏪', platform: 'woocommerce', color: 'bg-purple-50 hover:bg-purple-100 border-purple-200' },
                      { name: 'Amazon', icon: '📦', platform: 'amazon', color: 'bg-orange-50 hover:bg-orange-100 border-orange-200' },
                      { name: 'eBay', icon: '🔨', platform: 'ebay', color: 'bg-blue-50 hover:bg-blue-100 border-blue-200' },
                      { name: 'Etsy', icon: '🎨', platform: 'etsy', color: 'bg-pink-50 hover:bg-pink-100 border-pink-200' },
                      { name: 'Facebook', icon: '👥', platform: 'facebook', color: 'bg-blue-50 hover:bg-blue-100 border-blue-200' },
                      { name: 'Google Shopping', icon: '🔍', platform: 'google-shopping', color: 'bg-red-50 hover:bg-red-100 border-red-200' }
                    ].map((store) => (
                      <button
                        key={store.platform}
                        onClick={() => {
                          if (store.platform === 'amazon') {
                            // For Amazon, close modal and show dedicated integration component
                            setShowConnectStoreModal(false);
                            setSelectedPlatform('amazon-integration');
                          } else {
                            setSelectedPlatform(store.platform);
                          }
                        }}
                        className={`p-3 sm:p-4 border-2 rounded-lg text-center transition-colors ${store.color}`}
                      >
                        <div className="text-2xl sm:text-3xl mb-1 sm:mb-2">{store.icon}</div>
                        <div className="text-xs sm:text-sm font-medium text-gray-700">{store.name}</div>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  {/* Connection Form */}
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg flex items-center">
                    <div className="text-2xl mr-3">
                      {selectedPlatform === 'shopify' && '🛍️'}
                      {selectedPlatform === 'woocommerce' && '🏪'}
                      {selectedPlatform === 'amazon' && '📦'}
                      {selectedPlatform === 'ebay' && '🔨'}
                      {selectedPlatform === 'etsy' && '🎨'}
                      {selectedPlatform === 'facebook' && '👥'}
                      {selectedPlatform === 'google-shopping' && '🔍'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 capitalize">
                        Connexion {selectedPlatform.replace('-', ' ')}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Configurez vos identifiants de connexion
                      </p>
                    </div>
                  </div>

                  {/* Dynamic Form Fields */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nom de la boutique
                      </label>
                      <input
                        type="text"
                        value={storeConnectionForm.store_name || ''}
                        onChange={(e) => setStoreConnectionForm({...storeConnectionForm, store_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Ma Boutique"
                      />
                    </div>

                    {selectedPlatform === 'shopify' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Store URL
                          </label>
                          <input
                            type="text"
                            value={storeConnectionForm.store_url || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, store_url: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="https://monshop.myshopify.com"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Access Token
                          </label>
                          <input
                            type="password"
                            value={storeConnectionForm.access_token || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, access_token: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="shpat_..."
                          />
                        </div>
                      </>
                    )}

                    {selectedPlatform === 'woocommerce' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Site URL
                          </label>
                          <input
                            type="text"
                            value={storeConnectionForm.site_url || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, site_url: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="https://monsite.com"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Consumer Key
                          </label>
                          <input
                            type="text"
                            value={storeConnectionForm.consumer_key || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, consumer_key: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="ck_..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Consumer Secret
                          </label>
                          <input
                            type="password"
                            value={storeConnectionForm.consumer_secret || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, consumer_secret: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="cs_..."
                          />
                        </div>
                      </>
                    )}

                    {(selectedPlatform === 'amazon' || selectedPlatform === 'ebay' || selectedPlatform === 'etsy' || selectedPlatform === 'facebook' || selectedPlatform === 'google-shopping') && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            API Key
                          </label>
                          <input
                            type="password"
                            value={storeConnectionForm.api_key || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, api_key: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Votre clé API"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            API Secret
                          </label>
                          <input
                            type="password"
                            value={storeConnectionForm.api_secret || ''}
                            onChange={(e) => setStoreConnectionForm({...storeConnectionForm, api_secret: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Votre secret API"
                          />
                        </div>
                      </>
                    )}

                    {/* Instructions */}
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-semibold text-gray-800 mb-2">
                        💡 Comment obtenir vos identifiants :
                      </h4>
                      <p className="text-xs text-gray-600">
                        {selectedPlatform === 'shopify' && 'Admin Shopify → Apps → Manage private apps → Create private app'}
                        {selectedPlatform === 'woocommerce' && 'WooCommerce → Settings → Advanced → REST API → Create API Key'}
                        {selectedPlatform === 'amazon' && 'Amazon Seller Central → Settings → User Permissions → API Developer'}
                        {selectedPlatform === 'ebay' && 'eBay Developers → My Account → Keys'}
                        {selectedPlatform === 'etsy' && 'Etsy Developers → Your Account → Apps → Create New App'}
                        {selectedPlatform === 'facebook' && 'Facebook Business → Settings → Business Assets → Apps'}
                        {selectedPlatform === 'google-shopping' && 'Google Cloud Console → APIs & Services → Credentials'}
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-3 pt-4">
                      <button
                        onClick={() => {
                          setSelectedPlatform('');
                          setStoreConnectionForm({});
                        }}
                        disabled={connectingStore}
                        className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
                      >
                        ← Retour
                      </button>
                      <button
                        onClick={handleConnectStore}
                        disabled={connectingStore}
                        className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center"
                      >
                        {connectingStore ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Connexion...
                          </>
                        ) : 'Connecter'}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cancel Subscription Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">❌ Annuler l'Abonnement</h2>
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center">
                <div className="text-yellow-600 mr-3">⚠️</div>
                <div className="text-yellow-800">
                  <p className="font-medium">Attention</p>
                  <p className="text-sm">{t('cancelSubscriptionInfo')}</p>
                </div>
              </div>
            </div>
            <form onSubmit={cancelSubscription} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Raison de l'annulation (optionnel)
                </label>
                <textarea
                  rows={3}
                  value={cancelForm.reason}
                  onChange={(e) => setCancelForm({...cancelForm, reason: e.target.value})}
                  placeholder="Dites-nous pourquoi vous annulez (cela nous aide à nous améliorer)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-md"
                >
                  {loading ? 'Annulation...' : 'Confirmer l\'Annulation'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCancelModal(false);
                    setCancelForm({ reason: '' });
                    setError('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">🔒 Changer le Mot de Passe</h2>
            {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>}
            <form onSubmit={changePasswordDashboard} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mot de passe actuel
                </label>
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({...passwordForm, current_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({...passwordForm, new_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmer le nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={6}
                />
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-md"
                >
                  {loading ? 'Modification...' : 'Modifier le Mot de Passe'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                    setError('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">🗑️ Supprimer le Compte</h2>
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <div className="text-red-600 mr-3">⚠️</div>
                <div className="text-red-800">
                  <p className="font-medium">DANGER - Action irréversible</p>
                  <p className="text-sm">Cette action supprimera définitivement votre compte et toutes vos données :</p>
                  <ul className="text-sm mt-2 ml-4 list-disc">
                    <li>Toutes vos fiches produits générées</li>
                    <li>Votre historique de paiements</li>
                    <li>Toutes vos données personnelles</li>
                  </ul>
                </div>
              </div>
            </div>
            {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>}
            <form onSubmit={deleteAccount} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmez votre mot de passe
                </label>
                <input
                  type="password"
                  value={deleteForm.password}
                  onChange={(e) => setDeleteForm({...deleteForm, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Mot de passe actuel"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Raison de suppression (optionnel)
                </label>
                <textarea
                  rows={3}
                  value={deleteForm.reason}
                  onChange={(e) => setDeleteForm({...deleteForm, reason: e.target.value})}
                  placeholder="Dites-nous pourquoi vous supprimez votre compte..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-md"
                >
                  {loading ? 'Suppression...' : 'SUPPRIMER DÉFINITIVEMENT'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteForm({ password: '', reason: '' });
                    setError('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

        {/* Webhook Setup Guide Modal */}
        {showWebhookGuide && webhookGuide && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900">{webhookGuide.title}</h2>
                <button
                  onClick={() => setShowWebhookGuide(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
              
              <div className="p-6">
                {/* Webhook URL */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h3 className="font-medium text-gray-900 mb-2">🔗 URL du Webhook</h3>
                  <div className="flex items-center bg-white border rounded-lg p-3">
                    <code className="flex-1 text-sm text-gray-800">{webhookGuide.webhook_url}</code>
                    <button
                      onClick={() => navigator.clipboard.writeText(webhookGuide.webhook_url)}
                      className="ml-2 bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                    >
                      Copier
                    </button>
                  </div>
                </div>
                
                {/* Setup Steps */}
                <div className="space-y-4 mb-6">
                  <h3 className="font-medium text-gray-900">📋 Étapes de Configuration</h3>
                  {webhookGuide.steps?.map((step) => (
                    <div key={step.step} className="flex">
                      <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-4">
                        {step.step}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{step.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Verification */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h3 className="font-medium text-green-800 mb-2">✅ Vérification</h3>
                  <p className="text-sm text-green-700">{webhookGuide.verification}</p>
                </div>
                
                {/* Troubleshooting */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">🔧 Dépannage</h3>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {webhookGuide.troubleshooting?.map((tip, idx) => (
                      <li key={idx}>• {tip}</li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <div className="flex justify-end p-6 border-t">
                <button
                  onClick={() => setShowWebhookGuide(false)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        )}

        {/* SEO Setup Wizard Modal */}
        {showSEOWizard && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center p-6 border-b">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">🧙‍♂️ Assistant Configuration SEO Premium</h2>
                  <p className="text-sm text-gray-600">Étape {wizardStep} sur 3</p>
                </div>
                <button
                  onClick={() => setShowSEOWizard(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
              
              <div className="p-6">
                {/* Progress Bar */}
                <div className="mb-8">
                  <div className="flex items-center">
                    {[1, 2, 3].map((step) => (
                      <div key={step} className="flex items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          step <= wizardStep ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-600'
                        }`}>
                          {step}
                        </div>
                        {step < 3 && (
                          <div className={`flex-1 h-1 mx-4 ${
                            step < wizardStep ? 'bg-purple-600' : 'bg-gray-300'
                          }`}></div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Step Content */}
                {wizardStep === 1 && (
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🔗</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Vérification des Connexions</h3>
                      <p className="text-gray-600">Nous allons vérifier que vos boutiques e-commerce sont bien connectées.</p>
                    </div>
                    
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 mb-2">Connexions Requises :</h4>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>• Au moins une boutique e-commerce connectée (Shopify, WooCommerce, etc.)</li>
                        <li>• Identifiants API valides et testés</li>
                        <li>• Permissions de lecture et écriture des produits</li>
                      </ul>
                    </div>
                  </div>
                )}
                
                {wizardStep === 2 && (
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🔔</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration des Webhooks</h3>
                      <p className="text-gray-600">Les webhooks permettent de capturer automatiquement vos ventes pour optimiser le SEO.</p>
                    </div>
                    
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <h4 className="font-medium text-yellow-900 mb-2">Webhooks Recommandés :</h4>
                      <ul className="text-sm text-yellow-800 space-y-1">
                        <li>• Shopify : notifications de création de commande</li>
                        <li>• WooCommerce : notifications de commande terminée</li>
                        <li>• Configuration automatique des URLs de webhook</li>
                      </ul>
                    </div>
                  </div>
                )}
                
                {wizardStep === 3 && (
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🎯</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Test du Système Complet</h3>
                      <p className="text-gray-600">Validation finale que tout fonctionne correctement.</p>
                    </div>
                    
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-medium text-green-900 mb-2">Tests Automatiques :</h4>
                      <ul className="text-sm text-green-800 space-y-1">
                        <li>• Test de connectivité des boutiques</li>
                        <li>• Validation des webhooks configurés</li>
                        <li>• Test de génération d'optimisation SEO</li>
                        <li>• Vérification des permissions de publication</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex justify-between p-6 border-t">
                <button
                  onClick={prevWizardStep}
                  disabled={wizardStep === 1}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Précédent
                </button>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowSEOWizard(false)}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                  >
                    Annuler
                  </button>
                  {wizardStep < 3 ? (
                    <button
                      onClick={nextWizardStep}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                    >
                      Suivant
                    </button>
                  ) : (
                    <button
                      onClick={completeSEOWizard}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                    >
                      Terminer Configuration
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Store SEO Configuration Modal */}
        {showStoreConfigModal && selectedStoreForConfig && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-2 md:p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[95vh] md:max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center p-4 md:p-6 border-b">
                <div>
                  <h2 className="text-lg md:text-xl font-bold text-gray-900">
                    🏪 Configuration SEO - {selectedStoreForConfig.store.store_name}
                  </h2>
                  <p className="text-sm text-gray-600 capitalize">
                    {selectedStoreForConfig.store.platform}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowStoreConfigModal(false);
                    setSelectedStoreForConfig(null);
                  }}
                  className="text-gray-500 hover:text-gray-700 p-1"
                >
                  <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleStoreConfigSubmit} className="p-4 md:p-6 space-y-4 md:space-y-6">
                {/* Scraping Configuration */}
                <div className="bg-blue-50 rounded-lg p-3 md:p-4">
                  <h3 className="font-medium text-blue-900 mb-3 md:mb-4 text-sm md:text-base">🔍 Configuration du Scraping</h3>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
                      <div className="flex-1">
                        <label className="font-medium text-gray-900 text-sm md:text-base">Scraping activé</label>
                        <p className="text-xs md:text-sm text-gray-600">Active le scraping automatique pour cette boutique</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.scraping_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, scraping_enabled: e.target.checked}))}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div>
                      <label className="block font-medium text-gray-900 mb-1">Fréquence de scraping</label>
                      <select
                        value={storeConfigForm.scraping_frequency}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, scraping_frequency: e.target.value}))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="hourly">Toutes les heures</option>
                        <option value="daily">Quotidien</option>
                        <option value="weekly">Hebdomadaire</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Keywords Configuration */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-medium text-green-900 mb-4">🎯 Mots-clés Ciblés</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={addKeyword}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        + Ajouter un mot-clé
                      </button>
                    </div>
                    
                    {storeConfigForm.target_keywords.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {storeConfigForm.target_keywords.map((keyword, index) => (
                          <div key={index} className="bg-green-100 text-green-800 px-2 py-1 rounded flex items-center space-x-2">
                            <span>{keyword}</span>
                            <button
                              type="button"
                              onClick={() => removeKeyword(index)}
                              className="text-green-600 hover:text-green-800"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Categories Configuration */}
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-900 mb-4">📂 Catégories Ciblées</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={addCategory}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        + Ajouter une catégorie
                      </button>
                    </div>
                    
                    {storeConfigForm.target_categories.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {storeConfigForm.target_categories.map((category, index) => (
                          <div key={index} className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded flex items-center space-x-2">
                            <span>{category}</span>
                            <button
                              type="button"
                              onClick={() => removeCategory(index)}
                              className="text-yellow-600 hover:text-yellow-800"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Competitor URLs Configuration */}
                <div className="bg-red-50 rounded-lg p-4">
                  <h3 className="font-medium text-red-900 mb-4">🥊 URLs Concurrentes</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={addCompetitorUrl}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        + Ajouter une URL concurrente
                      </button>
                    </div>
                    
                    {storeConfigForm.competitor_urls.length > 0 && (
                      <div className="space-y-2">
                        {storeConfigForm.competitor_urls.map((url, index) => (
                          <div key={index} className="bg-red-100 text-red-800 px-3 py-2 rounded flex items-center justify-between">
                            <span className="text-sm truncate">{url}</span>
                            <button
                              type="button"
                              onClick={() => removeCompetitorUrl(index)}
                              className="text-red-600 hover:text-red-800 ml-2"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Optimization Settings */}
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-medium text-purple-900 mb-4">⚡ Paramètres d'Optimisation</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Auto-optimisation</label>
                        <p className="text-sm text-gray-600">Applique automatiquement les optimisations</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.auto_optimization_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, auto_optimization_enabled: e.target.checked}))}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Auto-publication</label>
                        <p className="text-sm text-gray-600">Publie automatiquement les optimisations</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.auto_publication_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, auto_publication_enabled: e.target.checked}))}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div>
                      <label className="block font-medium text-gray-900 mb-1">Seuil de confiance</label>
                      <input
                        type="range"
                        min="0.5"
                        max="1.0"
                        step="0.1"
                        value={storeConfigForm.confidence_threshold}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, confidence_threshold: parseFloat(e.target.value)}))}
                        className="w-full"
                      />
                      <div className="text-sm text-gray-600">{(storeConfigForm.confidence_threshold * 100).toFixed(0)}%</div>
                    </div>

                    <div>
                      <label className="block font-medium text-gray-900 mb-1">Focus géographique</label>
                      <select
                        value={storeConfigForm.geographic_focus[0] || 'FR'}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, geographic_focus: [e.target.value]}))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="FR">France</option>
                        <option value="EU">Europe</option>
                        <option value="US">États-Unis</option>
                        <option value="UK">Royaume-Uni</option>
                        <option value="CA">Canada</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Additional Features */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-4">🔧 Fonctionnalités Supplémentaires</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Suivi des prix</label>
                        <p className="text-sm text-gray-600">Surveille les prix concurrents</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.price_monitoring_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, price_monitoring_enabled: e.target.checked}))}
                        className="w-4 h-4 text-gray-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Optimisation contenu</label> 
                        <p className="text-sm text-gray-600">Améliore titres et descriptions</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.content_optimization_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, content_optimization_enabled: e.target.checked}))}
                        className="w-4 h-4 text-gray-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Suivi mots-clés</label>
                        <p className="text-sm text-gray-600">Analyse positions mots-clés</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.keyword_tracking_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, keyword_tracking_enabled: e.target.checked}))}
                        className="w-4 h-4 text-gray-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col md:flex-row justify-between pt-4 border-t space-y-2 md:space-y-0 md:space-x-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowStoreConfigModal(false);
                      setSelectedStoreForConfig(null);
                    }}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 order-2 md:order-1 text-sm md:text-base"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={storeConfigLoading}
                    className="bg-purple-600 text-white px-4 md:px-6 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed order-1 md:order-2 text-sm md:text-base"
                  >
                    {storeConfigLoading ? '⏳ Enregistrement...' : '💾 Enregistrer Configuration'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      {/* Modal Configuration Affiliation */}
      {showAffiliateConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">⚙️ Configuration du Programme d'Affiliation</h3>
              <button
                onClick={() => setShowAffiliateConfigModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSaveAffiliateConfig(); }} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Configuration des Commissions */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">💰 Commissions</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Commission Plan Pro (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={affiliateConfigForm.default_commission_rate_pro}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          default_commission_rate_pro: parseFloat(e.target.value) || 0
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Commission Plan Premium (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={affiliateConfigForm.default_commission_rate_premium}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          default_commission_rate_premium: parseFloat(e.target.value) || 0
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Type de Commission
                      </label>
                      <select
                        value={affiliateConfigForm.commission_type}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          commission_type: e.target.value
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="recurring">Récurrente (chaque mois)</option>
                        <option value="one_time">Unique (première fois seulement)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Configuration des Paiements */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">💳 Paiements</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Fréquence de Paiement
                      </label>
                      <select
                        value={affiliateConfigForm.payment_frequency}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          payment_frequency: e.target.value
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="weekly">Hebdomadaire</option>
                        <option value="monthly">Mensuelle</option>
                        <option value="quarterly">Trimestrielle</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Paiement Minimum (€)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={affiliateConfigForm.minimum_payout}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          minimum_payout: parseFloat(e.target.value) || 0
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Montant minimum requis pour déclencher un paiement
                      </p>
                    </div>
                  </div>
                </div>

                {/* Paramètres du Programme */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Paramètres</h4>
                  
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="program_enabled"
                        checked={affiliateConfigForm.program_enabled}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          program_enabled: e.target.checked
                        }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="program_enabled" className="ml-2 block text-sm text-gray-900">
                        Programme d'affiliation activé
                      </label>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="auto_approval"
                        checked={affiliateConfigForm.auto_approval}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          auto_approval: e.target.checked
                        }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="auto_approval" className="ml-2 block text-sm text-gray-900">
                        Approbation automatique des affiliés
                      </label>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Durée du Cookie (jours)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={affiliateConfigForm.cookie_duration_days}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          cookie_duration_days: parseInt(e.target.value) || 30
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Durée pendant laquelle l'affilié recevra la commission après le premier clic
                      </p>
                    </div>
                  </div>
                </div>

                {/* Message de Bienvenue */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">💬 Messages</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Message de Bienvenue
                      </label>
                      <textarea
                        rows="3"
                        value={affiliateConfigForm.welcome_message}
                        onChange={(e) => setAffiliateConfigForm(prev => ({
                          ...prev,
                          welcome_message: e.target.value
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Message affiché aux nouveaux affiliés..."
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Termes et Conditions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Termes et Conditions (optionnel)
                </label>
                <textarea
                  rows="4"
                  value={affiliateConfigForm.terms_and_conditions}
                  onChange={(e) => setAffiliateConfigForm(prev => ({
                    ...prev,
                    terms_and_conditions: e.target.value
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Termes et conditions du programme d'affiliation..."
                />
              </div>

              {/* Buttons */}
              <div className="flex flex-col md:flex-row justify-between space-y-2 md:space-y-0 md:space-x-4">
                <div className="space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowAffiliateConfigModal(false)}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={savingAffiliateConfig}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                  >
                    {savingAffiliateConfig ? 'Sauvegarde...' : '💾 Sauvegarder'}
                  </button>
                </div>
                
                <button
                  type="button"
                  onClick={bulkUpdateAffiliateCommissions}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg"
                >
                  🔄 Appliquer aux Affiliés Existants
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal d'aide Dashboard */}
      {showDashboardHelp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">📚 Guide du Dashboard</h2>
              <button
                onClick={() => setShowDashboardHelp(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              <div className="text-center mb-6">
                <h3 className="text-xl font-semibold text-purple-600 mb-2">
                  Bienvenue sur votre Dashboard ECOMSIMPLY !
                </h3>
                <p className="text-gray-600">
                  Découvrez toutes les fonctionnalités de votre espace personnel
                </p>
              </div>

              {/* Navigation Rapide */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h4 className="font-semibold text-purple-800 mb-3">🚀 Navigation Rapide</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <button
                    onClick={() => {setActiveTab('generator'); setShowDashboardHelp(false);}}
                    className="bg-white p-3 rounded-lg text-center hover:bg-purple-100 transition-colors"
                  >
                    <div className="text-2xl mb-1">⚡</div>
                    <div className="text-sm font-medium">Générateur</div>
                  </button>
                  <button
                    onClick={() => {setActiveTab('integrations'); setShowDashboardHelp(false);}}
                    className="bg-white p-3 rounded-lg text-center hover:bg-purple-100 transition-colors"
                  >
                    <div className="text-2xl mb-1">🔗</div>
                    <div className="text-sm font-medium">Intégrations</div>
                  </button>
                  <button
                    onClick={() => {setActiveTab('ai'); setShowDashboardHelp(false);}}
                    className="bg-white p-3 rounded-lg text-center hover:bg-purple-100 transition-colors"
                  >
                    <div className="text-2xl mb-1">🧠</div>
                    <div className="text-sm font-medium">IA Avancée</div>
                  </button>
                  <button
                    onClick={() => {setActiveTab('analytics'); setShowDashboardHelp(false);}}
                    className="bg-white p-3 rounded-lg text-center hover:bg-purple-100 transition-colors"
                  >
                    <div className="text-2xl mb-1">📊</div>
                    <div className="text-sm font-medium">Analytics</div>
                  </button>
                </div>
              </div>

              {/* Fonctionnalités principales */}
              <div className="space-y-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-bold text-gray-800 mb-2">⚡ Générateur de Fiches</h4>
                  <p className="text-gray-600 text-sm mb-2">
                    Créez instantanément des fiches produits optimisées avec l'IA {PLATFORM_CONFIG.GPT_MODEL}.
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Plan Gratuit: {PLATFORM_CONFIG.FREE_SHEETS_LIMIT} fiche/mois</li>
                    <li>• Plan Pro: {PLATFORM_CONFIG.PRO_SHEETS_LIMIT} fiches/mois</li>
                    <li>• Plan Premium: Fiches {PLATFORM_CONFIG.PREMIUM_SHEETS_UNLIMITED}</li>
                  </ul>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-bold text-gray-800 mb-2">🔗 Intégrations E-commerce</h4>
                  <p className="text-gray-600 text-sm mb-2">
                    Connectez jusqu'à {PLATFORM_CONFIG.ECOMMERCE_PLATFORMS_COUNT} plateformes e-commerce.
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Shopify, WooCommerce, Amazon</li>
                    <li>• Publication automatique par lot</li>
                    <li>• Synchronisation en temps réel</li>
                  </ul>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-bold text-gray-800 mb-2">🧠 IA Avancée (Pro/Premium)</h4>
                  <p className="text-gray-600 text-sm mb-2">
                    Fonctionnalités d'intelligence artificielle avancées.
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Analyse SEO automatique</li>
                    <li>• Étude concurrentielle</li>
                    <li>• Optimisation des prix</li>
                    <li>• Variantes produits</li>
                    <li>• Traduction multilingue</li>
                  </ul>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-bold text-gray-800 mb-2">📊 Analytics Pro</h4>
                  <p className="text-gray-600 text-sm mb-2">
                    Analyses approfondies de vos performances.
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Données mises à jour toutes les {PLATFORM_CONFIG.AUTO_UPDATE_SECONDS} secondes</li>
                    <li>• Historique sur {PLATFORM_CONFIG.ANALYTICS_DAYS} jours</li>
                    <li>• Performance produits</li>
                    <li>• Engagement clients</li>
                  </ul>
                </div>
              </div>

              {/* Support */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-2">💬 Besoin d'aide ?</h4>
                <p className="text-blue-700 text-sm mb-3">
                  Notre support est disponible {PLATFORM_CONFIG.SUPPORT_HOURS} pour vous accompagner.
                </p>
                <div className="flex flex-wrap gap-2">
                  <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                    💬 Chat Support
                  </button>
                  <button className="bg-white text-blue-600 px-3 py-1 rounded text-sm hover:bg-blue-50 border border-blue-200">
                    📧 Email Support
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
};

// Main App Component
// SUPPRIMÉ: TrialModal - Plus de popup de sélection, CTA direct vers Stripe Checkout

const App = () => {
  const { user, loading, token } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  
  // ===============================================
  // DIRECT STRIPE CHECKOUT - OFFRE UNIQUE PREMIUM
  // ===============================================
  
  const handleDirectPremiumCheckout = async () => {
    try {
      console.log('🔥 Direct Premium Checkout - Starting...');
      
      // Vérifier l'authentification
      if (!token) {
        console.log('❌ User not authenticated, showing login modal');
        setActiveModalTab('login');
        setShowLogin(true);
        return;
      }
      
      // Appel direct à l'endpoint billing checkout
      const response = await fetch(`${API}/billing/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan_type: 'premium',
          with_trial: true
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la création de la session');
      }
      
      const data = await response.json();
      
      if (data.success && data.checkout_url) {
        console.log('✅ Checkout session created, redirecting to Stripe...');
        window.location.href = data.checkout_url;
      } else {
        throw new Error(data.message || 'URL de checkout manquante');
      }
      
    } catch (error) {
      console.error('❌ Error in direct checkout:', error);
      alert('Erreur lors de la création de la session de paiement. Veuillez réessayer.');
    }
  };
  
  // États de l'application
  const [currentView, setCurrentView] = useState('home'); // 'home', 'dashboard'
  const [affiliateMode, setAffiliateMode] = useState(false);
  const [affiliateCode, setAffiliateCode] = useState('');
  const [showAffiliateLogin, setShowAffiliateLogin] = useState(false);
  const [affiliateLoginForm, setAffiliateLoginForm] = useState({ code: '' });
  const [affiliateError, setAffiliateError] = useState('');
  
  // États pour les modals (définis au niveau App pour accès global)
  const [showLogin, setShowLogin] = useState(false);
  const [activeModalTab, setActiveModalTab] = useState('login');
  
  // CRITICAL FIX: Automatically navigate to dashboard after successful login
  // BUT allow forcing home view when coming from demo
  useEffect(() => {
    const location = window.location;
    const forceHome = location.state?.forceHome;
    
    if (user && !loading && !forceHome) {
      console.log('✅ User logged in successfully, navigating to dashboard');
      setCurrentView('dashboard');
    } else if (!user && !loading) {
      console.log('🔄 User logged out, navigating to home');
      setCurrentView('home');
    } else if (forceHome) {
      console.log('🏠 Forcing home view from demo');
      setCurrentView('home');
    }
  }, [user, loading]);
  
  // SUPPRIMÉ: Toute la logique legacy TrialModal
  // Plus de modal de sélection, CTA direct vers Stripe Checkout
  
  // Affiliate configuration state (moved from AdminPanel to make it globally accessible)
  const [affiliateConfig, setAffiliateConfig] = useState(null);
  const [loadingAffiliateConfig, setLoadingAffiliateConfig] = useState(false);
  
  // Check if affiliate is logged in on component mount
  useEffect(() => {
    const savedAffiliateCode = localStorage.getItem('affiliate_code');
    if (savedAffiliateCode) {
      setAffiliateCode(savedAffiliateCode);
      setAffiliateMode(true);
    }
    
    // Check for affiliate referral in URL
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    if (refCode) {
      // Track the affiliate click
      trackAffiliateClick(refCode);
    }
  }, []);
  
  const trackAffiliateClick = async (code) => {
    try {
      const currentPage = window.location.href;
      const urlParams = new URLSearchParams(window.location.search);
      
      await axios.get(`${API}/affiliate/track/${code}`, {
        params: {
          landing_page: currentPage,
          utm_source: urlParams.get('utm_source'),
          utm_medium: urlParams.get('utm_medium'),
          utm_campaign: urlParams.get('utm_campaign')
        }
      });
    } catch (error) {
      console.error('Erreur tracking affilié:', error);
    }
  };
  
  const handleAffiliateLogin = async (e) => {
    e.preventDefault();
    setAffiliateError('');
    
    try {
      // Verify affiliate code exists and is approved
      const response = await axios.get(`${API}/affiliate/${affiliateLoginForm.code}/stats`);
      
      if (response.data) {
        localStorage.setItem('affiliate_code', affiliateLoginForm.code);
        setAffiliateCode(affiliateLoginForm.code);
        setAffiliateMode(true);
        setShowAffiliateLogin(false);
        setAffiliateLoginForm({ code: '' });
      }
    } catch (error) {
      console.error('Erreur connexion affilié:', error);
      if (error.response?.status === 404) {
        setAffiliateError('Code d\'affiliation invalide ou compte non approuvé');
      } else {
        setAffiliateError('Erreur de connexion. Veuillez réessayer.');
      }
    }
  };
  
  const handleAffiliateLogout = () => {
    localStorage.removeItem('affiliate_code');
    setAffiliateCode('');
    setAffiliateMode(false);
  };

  // Load affiliate configuration
  const loadAffiliateConfig = async () => {
    setLoadingAffiliateConfig(true);
    try {
      const response = await axios.get(`${API}/public/affiliate-config`);
      if (response.data.success) {
        const config = response.data.config;
        setAffiliateConfig(config);
      }
    } catch (error) {
      console.error('Erreur chargement config affiliation:', error);
    }
    setLoadingAffiliateConfig(false);
  };

  // Load affiliate config on component mount
  useEffect(() => {
    loadAffiliateConfig();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }
  
  // Affiliate Dashboard Mode
  if (affiliateMode && affiliateCode) {
    return <AffiliateDashboard affiliateCode={affiliateCode} onLogout={handleAffiliateLogout} />;
  }

  // Show affiliate login modal
  if (showAffiliateLogin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-green-900 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 w-full max-w-md mx-4">
          <div className="text-center mb-6">
            <div className="text-4xl mb-4">💰</div>
            <h2 className="text-2xl font-bold text-gray-900">Espace Affilié</h2>
            <p className="text-gray-600 mt-2">Connectez-vous avec votre code d'affiliation</p>
          </div>
          
          {affiliateError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {affiliateError}
            </div>
          )}
          
          <form onSubmit={handleAffiliateLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Code d'Affiliation
              </label>
              <input
                type="text"
                value={affiliateLoginForm.code}
                onChange={(e) => setAffiliateLoginForm({ code: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                placeholder="Ex: ABC12345"
                required
              />
            </div>
            
            <div className="flex space-x-3">
              <button
                type="submit"
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md font-medium transition-colors"
              >
                🚀 Accéder au Dashboard
              </button>
              <button
                type="button"
                onClick={() => setShowAffiliateLogin(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-md font-medium transition-colors"
              >
                Retour
              </button>
            </div>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Pas encore affilié ?{' '}
              <button
                onClick={() => {
                  setShowAffiliateLogin(false);
                  // The affiliate registration will be handled by LandingPage
                }}
                className="text-green-600 hover:text-green-700 font-medium"
              >
                Rejoindre le programme
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Regular user flow - pass affiliate login handler to LandingPage
  if (!user) {
    return (
      <>
        <LandingPage 
          onShowAffiliateLogin={() => setShowAffiliateLogin(true)} 
          affiliateConfig={affiliateConfig}
          onDirectPremiumCheckout={handleDirectPremiumCheckout}
        />
      </>
    );
  }
  
  // Navigation functions for logged in users
  const goToHome = () => setCurrentView('home');
  const goToDashboard = () => setCurrentView('dashboard');
  
  // Show home, dashboard ou amazon based on currentView
  if (currentView === 'home') {
    return (
      <>
        <LandingPage 
          onShowAffiliateLogin={() => setShowAffiliateLogin(true)} 
          showUserNavigation={true}
          affiliateConfig={affiliateConfig}
          onDirectPremiumCheckout={handleDirectPremiumCheckout}
        />
      </>
    );
  }
  

  
  // Debug: Add console log for render
  // Debug log for each render - single log to avoid React optimization issues
  console.log('🔍 App render - currentView:', currentView, 'user:', !!user);

  // For logged-in users, show dashboard, amazon ou home based on currentView
  if (user && !loading) {
    if (currentView === 'dashboard') {
      return (
        <>
          <Dashboard 
            onGoToHome={goToHome} 
            affiliateConfig={affiliateConfig}
            loadingAffiliateConfig={loadingAffiliateConfig}
            loadAffiliateConfig={loadAffiliateConfig}
          />
        </>
      );
    }
    
    // Logged-in user viewing home
    return (
      <>
        <LandingPage 
          onShowAffiliateLogin={() => setShowAffiliateLogin(true)} 
          showUserNavigation={true}
          affiliateConfig={affiliateConfig}
          onDirectPremiumCheckout={handleDirectPremiumCheckout}
        />
      </>
    );
  }

  // For non-logged-in users (priority after trial modal)
  return (
    <>
      <LandingPage 
        onShowAffiliateLogin={() => setShowAffiliateLogin(true)} 
        affiliateConfig={affiliateConfig}
        onDirectPremiumCheckout={handleDirectPremiumCheckout}
      />
    </>
  );
};

const AppWithAuth = () => {
  return (
    <LanguageProvider>
      <AuthProvider>
        <Routes>
          <Route path="/demo" element={<PremiumDemo />} />
          <Route 
            path="/integrations/amazon" 
            element={
              <ProtectedIntegrationRoute>
                <AmazonIntegrationPage 
                  onGoToHome={() => window.location.href = '/'} 
                  onGoToDashboard={() => window.location.href = '/'} 
                />
              </ProtectedIntegrationRoute>
            } 
          />
          <Route 
            path="/integrations/shopify" 
            element={
              <ProtectedIntegrationRoute>
                <ShopifyIntegrationPage 
                  onGoToHome={() => window.location.href = '/'} 
                  onGoToDashboard={() => window.location.href = '/'} 
                />
              </ProtectedIntegrationRoute>
            } 
          />
          <Route path="/*" element={<App />} />
        </Routes>
      </AuthProvider>
    </LanguageProvider>
  );
};

export default AppWithAuth;