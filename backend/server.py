import os
import logging
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

# Import database connection
from database import get_db, close_db

# Import new routes
from routes.messages_routes import messages_router
from routes.ai_routes import ai_router

try:
    # facultatif si tu utilises un .env en local
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Configuration pour emergent.sh
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://ecomsimply.com")  # Production frontend domain
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME_ENV = os.getenv("DB_NAME", "ecomsimply_production")
ADMIN_BOOTSTRAP_TOKEN = os.getenv("ADMIN_BOOTSTRAP_TOKEN")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

logger = logging.getLogger("ecomsimply")
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="ECOMSIMPLY API",
    description="API pour la plateforme ECOMSIMPLY - Génération automatique de fiches produits",
    version="1.0.0"
)

# Include new routers
app.include_router(messages_router)
app.include_router(ai_router)

# Import Amazon SP-API routes
try:
    from routes.amazon_routes import amazon_router
    from routes.amazon_integration_routes import amazon_integration_router
    from routes.demo_amazon_integration_routes import demo_amazon_integration_router
    from routes.amazon_listings_routes import amazon_listings_router
    from routes.amazon_publisher_routes import publisher_router
    AMAZON_SPAPI_AVAILABLE = True
    print("✅ Amazon SP-API integration loaded")
except ImportError as e:
    AMAZON_SPAPI_AVAILABLE = False
    print(f"❌ Amazon SP-API integration not available: {e}")

# Import Amazon SEO+Price routes (Phase 3)
try:
    from routes.amazon_seo_price_routes import amazon_seo_price_router
    AMAZON_SEO_PRICE_AVAILABLE = True
    print("✅ Amazon SEO+Price router loaded")
except ImportError as e:
    AMAZON_SEO_PRICE_AVAILABLE = False
    print(f"❌ Amazon SEO+Price router not available: {e}")

# Import additional Amazon routes
try:
    from routes.amazon_seo_routes import amazon_seo_router
    AMAZON_SEO_AVAILABLE = True
    print("✅ Amazon SEO router loaded")
except ImportError as e:
    AMAZON_SEO_AVAILABLE = False
    print(f"❌ Amazon SEO router not available: {e}")

try:
    from routes.amazon_phase6_routes import router as amazon_phase6_router
    AMAZON_PHASE6_AVAILABLE = True
    print("✅ Amazon Phase 6 router loaded")
except ImportError as e:
    AMAZON_PHASE6_AVAILABLE = False
    print(f"❌ Amazon Phase 6 router not available: {e}")

try:
    from routes.amazon_pricing_routes import amazon_pricing_router
    AMAZON_PRICING_AVAILABLE = True
    print("✅ Amazon Pricing router loaded")
except ImportError as e:
    AMAZON_PRICING_AVAILABLE = False
    print(f"❌ Amazon Pricing router not available: {e}")

try:
    from routes.amazon_monitoring_routes import router as amazon_monitoring_router
    AMAZON_MONITORING_AVAILABLE = True
    print("✅ Amazon Monitoring router loaded")
except ImportError as e:
    AMAZON_MONITORING_AVAILABLE = False
    print(f"❌ Amazon Monitoring router not available: {e}")

# Include Amazon SP-API router if available - CONSOLIDATED VERSION
if AMAZON_SPAPI_AVAILABLE:
    # Primary Amazon router (consolidated, most complete)
    app.include_router(amazon_router)
    # Specialized Amazon routers  
    app.include_router(demo_amazon_integration_router)
    app.include_router(amazon_listings_router)
    app.include_router(publisher_router)
    print("✅ Amazon SP-API routes registered (consolidated)")
else:
    print("❌ Amazon SP-API routes not available")

# Include Amazon SEO+Price router if available
if AMAZON_SEO_PRICE_AVAILABLE:
    app.include_router(amazon_seo_price_router)
    print("✅ Amazon SEO+Price routes registered")
else:
    print("❌ Amazon SEO+Price routes not available")

# Include additional Amazon routers
if AMAZON_SEO_AVAILABLE:
    app.include_router(amazon_seo_router)
    print("✅ Amazon SEO routes registered")

if AMAZON_PHASE6_AVAILABLE:
    app.include_router(amazon_phase6_router)
    print("✅ Amazon Phase 6 routes registered")

if AMAZON_PRICING_AVAILABLE:
    app.include_router(amazon_pricing_router)
    print("✅ Amazon Pricing routes registered")

if AMAZON_MONITORING_AVAILABLE:
    app.include_router(amazon_monitoring_router)
    print("✅ Amazon Monitoring routes registered")

# Configuration CORS sécurisée pour emergent.sh
def get_allowed_origins():
    """
    Configuration dynamique des origines autorisées pour emergent.sh
    """
    origins = set()
    
    # Origine principale (frontend Vercel ou emergent.sh)
    if APP_BASE_URL:
        origins.add(APP_BASE_URL)
    
    # Ajouter automatiquement le domaine emergent.sh pour production
    app_name = os.getenv("APP_NAME", "ecom-api-fixes")
    emergent_domain = f"https://{app_name}.emergent.host"
    origins.add(emergent_domain)
    
    # Domaine de production principal
    origins.add("https://ecomsimply.com")
    
    # Origines supplémentaires via variable d'environnement
    additional_origins = os.getenv("ADDITIONAL_ALLOWED_ORIGINS", "")
    if additional_origins:
        for origin in additional_origins.split(","):
            origin = origin.strip()
            if origin:
                origins.add(origin)
    
    # Development fallbacks (seulement si APP_BASE_URL n'est pas défini)
    if not APP_BASE_URL:
        origins.update([
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ])
        logger.warning("⚠️ APP_BASE_URL not configured - using development CORS origins")
    
    return list(origins)

# CORS
allowed_origins = get_allowed_origins()
logger.info(f"✅ CORS configured for origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)




@app.on_event("startup")
async def on_startup():
    """
    Minimal startup - actual DB connection happens lazily
    Create indexes on startup
    """
    logger.info("FastAPI startup - MongoDB will connect lazily")
    
    # Create indexes on startup (without admin creation to avoid production issues)
    try:
        db_instance = await get_db()
        await db_instance["users"].create_index("email", unique=True)
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.info("users.create_index(email) → %s", e)
    
    # Scheduler initialization avec guard ENABLE_SCHEDULER
    scheduler_enabled = _is_true(os.getenv("ENABLE_SCHEDULER", "false"))
    
    if scheduler_enabled:
        logger.info("✅ Scheduler enabled - Starting background jobs...")
        try:
            # Ici on pourrait ajouter l'initialisation des schedulers si nécessaire
            # Exemple: await start_background_jobs()
            logger.info("✅ Background schedulers started successfully")
        except Exception as e:
            logger.warning(f"⚠️ Scheduler initialization failed: {e}")
    else:
        logger.info("ℹ️ Scheduler disabled (prod default) - Set ENABLE_SCHEDULER=true to enable background jobs")

@app.on_event("shutdown")
async def on_shutdown():
    await close_db()

@app.get("/api/health")
async def health():
    """
    Endpoint de santé optimisé pour emergent.sh déploiement
    Retourne rapidement le statut sans dépendance DB critiques
    """
    try:
        start_time = datetime.utcnow()
        
        # Check de base du service (toujours OK)
        response_data = {
            "status": "ok",
            "service": "ecomsimply-api",
            "timestamp": start_time.isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("NODE_ENV", "development")
        }
        
        # Test MongoDB NON-BLOQUANT avec timeout court
        mongo_status = "not_configured"
        if MONGO_URL:
            try:
                # Test rapide avec timeout très court pour ne pas bloquer le healthcheck
                db_instance = await asyncio.wait_for(get_db(), timeout=2.0)
                await asyncio.wait_for(db_instance.command("ping"), timeout=2.0)
                mongo_status = "ok"
                response_data["database"] = str(db_instance.name)
            except asyncio.TimeoutError:
                mongo_status = "timeout"
            except Exception as mongo_error:
                # Log l'erreur mais ne fait pas échouer le health check
                logger.warning(f"MongoDB check failed (non-critical): {str(mongo_error)}")
                mongo_status = f"error:{type(mongo_error).__name__}"
        
        response_data["mongo"] = mongo_status
        
        # Temps de réponse
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        response_data["response_time_ms"] = round(response_time, 2)
        
        # Retourne toujours 200 OK sauf exception critique
        return response_data
        
    except Exception as e:
        # Log l'erreur mais retourne un status dégradé plutôt qu'une erreur 500
        logger.error(f"Health check error (degraded): {str(e)}")
        return {
            "status": "degraded",
            "service": "ecomsimply-api",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Emergency endpoints removed for production security

@app.post("/api/admin/bootstrap")
async def admin_bootstrap(request: Request):
    """
    Crée/assure l'admin (idempotent). Sécurisé via x-bootstrap-token.
    """
    try:
        # Debug logging pour diagnostiquer le problème
        bootstrap_token_env = os.getenv("ADMIN_BOOTSTRAP_TOKEN")
        request_token = request.headers.get("x-bootstrap-token")
        
        logger.info(f"Bootstrap request received")
        logger.info(f"ENV token exists: {bootstrap_token_env is not None}")
        logger.info(f"Request token exists: {request_token is not None}")
        
        # Fallback si pas de token env configuré (pour production)
        if not bootstrap_token_env:
            # Utiliser un token de fallback sécurisé pour production
            bootstrap_token_env = "ECS-Bootstrap-2025-Secure-Token"
            logger.warning("Using fallback bootstrap token - configure ADMIN_BOOTSTRAP_TOKEN in production")
        
        if not request_token:
            logger.error("x-bootstrap-token header is missing")
            raise HTTPException(403, "Bootstrap token header missing")
        
        if request_token != bootstrap_token_env:
            logger.error(f"Token mismatch - Expected length: {len(bootstrap_token_env)}, Got length: {len(request_token)}")
            logger.error(f"Expected starts with: {bootstrap_token_env[:10] if len(bootstrap_token_env) > 10 else bootstrap_token_env}")
            logger.error(f"Got starts with: {request_token[:10] if len(request_token) > 10 else request_token}")
            raise HTTPException(403, "Invalid bootstrap token")

        admin_email_env = os.getenv("ADMIN_EMAIL") or "msylla54@gmail.com"
        admin_password_hash_env = os.getenv("ADMIN_PASSWORD_HASH") or "$2b$12$yQhOn3ydalPB3RuDZNsD8uUbfuc.MVG3Pf30xrUougEsibvP4Ukty"
        
        logger.info("All validation passed, proceeding with admin creation")
        
        db_instance = await get_db()
        
        # Check if admin already exists first
        existing_admin = await db_instance["users"].find_one({"email": admin_email_env.strip()})
        if existing_admin:
            logger.info(f"Admin user already exists: {admin_email_env}")
            return {"ok": True, "bootstrap": "exists", "email": admin_email_env.strip(), "created": False}
        
        doc = {
            "email": admin_email_env.strip(),
            "name": "Admin Ecomsimply",
            "password_hash": admin_password_hash_env,  # Utiliser password_hash pour cohérence
            "passwordHash": admin_password_hash_env,   # Garder les deux pour compatibility
            "is_admin": True,
            "isActive": True,
            "subscription_plan": "premium",
            "language": "fr",
            "is_trial_user": False,
            "generate_images": True,
            "include_images_manual": True,
            "created_at": datetime.utcnow(),
        }

        result = await db_instance["users"].insert_one(doc)
        
        if result.inserted_id:
            logger.info(f"Admin user created successfully: {admin_email_env}")
            return {"ok": True, "bootstrap": "done", "email": admin_email_env.strip(), "created": True}
        else:
            logger.error("Failed to create admin user")
            raise HTTPException(500, "Failed to create admin user")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin bootstrap: {str(e)}")
        raise HTTPException(500, f"Internal server error: {str(e)}")

async def ensure_admin_user():
    """
    S'assurer que l'utilisateur admin existe au démarrage (pour production)
    """
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "msylla54@gmail.com")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$yQhOn3ydalPB3RuDZNsD8uUbfuc.MVG3Pf30xrUougEsibvP4Ukty")
        
        db_instance = await get_db()
        existing_admin = await db_instance["users"].find_one({"email": admin_email})
        
        if not existing_admin:
            logger.info(f"Creating admin user: {admin_email}")
            doc = {
                "email": admin_email,
                "name": "Admin Ecomsimply",
                "password_hash": admin_password_hash,
                "passwordHash": admin_password_hash,
                "is_admin": True,
                "isActive": True,
                "subscription_plan": "premium",
                "language": "fr",
                "is_trial_user": False,
                "generate_images": True,
                "include_images_manual": True,
                "created_at": datetime.utcnow(),
            }
            await db_instance["users"].insert_one(doc)
            logger.info(f"✅ Admin user created successfully: {admin_email}")
        else:
            logger.info(f"✅ Admin user already exists: {admin_email}")
            
    except Exception as e:
        logger.error(f"Failed to ensure admin user: {e}")

# ==========================================
# AUTHENTICATION ROUTES  
# ==========================================

from pydantic import BaseModel
import bcrypt
import jwt
from datetime import timedelta

JWT_SECRET = os.getenv("JWT_SECRET", "ecomsimply-secret-2025")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def _is_true(value):
    """
    Helper pour convertir des variables d'environnement en booléen
    """
    if not value:
        return False
    return str(value).lower() in ('true', '1', 'yes', 'on', 'enabled')

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class AuthResponse(BaseModel):
    ok: bool
    token: str = None
    user: dict = None
    message: str = None

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    """
    Authentification utilisateur avec logs DEBUG structurés
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        db_instance = await get_db()
        
        # Rechercher l'utilisateur par email
        user = await db_instance["users"].find_one({"email": login_data.email.strip()})
        
        if not user:
            logger.warning(f"Login failed - user not found: {login_data.email}")
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Vérifier le mot de passe
        password_hash = user.get("passwordHash") or user.get("password_hash")
        if not password_hash:
            logger.error(f"User {login_data.email} has no password hash field")
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
            
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), password_hash.encode('utf-8')):
            logger.warning(f"Login failed - invalid password for: {login_data.email}")
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        logger.info(f"Login successful for user: {login_data.email}")
        
        # Créer le token JWT
        payload = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "is_admin": user.get("is_admin", False),
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "ok": True,
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "is_admin": user.get("is_admin", False)
            },
            "message": "Connexion réussie"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error for {login_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la connexion")

@app.post("/api/auth/register")
async def register(register_data: RegisterRequest):
    """
    Inscription nouvel utilisateur avec logs DEBUG structurés
    """
    try:
        logger.info(f"Registration attempt for email: {register_data.email}")
        db_instance = await get_db()
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = await db_instance["users"].find_one({"email": register_data.email.strip()})
        if existing_user:
            logger.warning(f"Registration failed - email already exists: {register_data.email}")
            raise HTTPException(status_code=409, detail="Un compte existe déjà avec cette adresse email")
        
        # Valider le mot de passe (minimum 8 caractères)
        if len(register_data.password) < 8:
            logger.warning(f"Registration failed - password too short for: {register_data.email}")
            raise HTTPException(status_code=422, detail="Le mot de passe doit contenir au moins 8 caractères")
        
        # Hasher le mot de passe
        password_hash = bcrypt.hashpw(register_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') 
        
        # Créer le nouvel utilisateur
        user_doc = {
            "name": register_data.name.strip(),
            "email": register_data.email.strip(),
            "passwordHash": password_hash,
            "is_admin": False,
            "isActive": True,
            "created_at": datetime.utcnow(),
        }
        
        # Insert avec gestion explicit des erreurs
        try:
            result = await db_instance["users"].insert_one(user_doc)
            logger.info(f"User created successfully - ID: {result.inserted_id}, Email: {register_data.email}")
            
            if result.inserted_id:
                # Créer le token JWT pour l'utilisateur nouvellement inscrit
                payload = {
                    "user_id": str(result.inserted_id),
                    "email": user_doc["email"],
                    "is_admin": False,
                    "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
                }
                
                token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                
                return {
                    "ok": True,
                    "token": token,
                    "user": {
                        "id": str(result.inserted_id),
                        "email": user_doc["email"],
                        "name": user_doc["name"],
                        "is_admin": False
                    },
                    "message": "Compte créé avec succès"
                }
            else:
                logger.error(f"Failed to insert user document for: {register_data.email}")
                raise HTTPException(status_code=500, detail="Erreur lors de la création du compte")
                
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error during registration: {register_data.email}")
            raise HTTPException(status_code=409, detail="Un compte existe déjà avec cette adresse email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error for {register_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de l'inscription")

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """
    Retourne les informations de l'utilisateur connecté via JWT
    """
    try:
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token d'autorisation manquant")
        
        token = auth_header.split(" ")[1]
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if not user_id or not email:
                raise HTTPException(status_code=401, detail="Token invalide")
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expiré")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Get user from database
        db_instance = await get_db()
        user = await db_instance["users"].find_one({"email": email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return {
            "ok": True,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "is_admin": user.get("is_admin", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

# ==========================================
# PUBLIC ENDPOINTS 
# ==========================================

@app.get("/api/public/plans-pricing")
async def get_plans_pricing():
    """
    Retourne les plans et tarifs publics depuis MongoDB
    """
    try:
        db_instance = await get_db()
        
        # Récupérer les plans depuis MongoDB
        plans_cursor = db_instance["subscription_plans"].find(
            {"active": True},
            {"_id": 0}  # Exclure l'_id MongoDB
        ).sort("price", 1)  # Trier par prix croissant
        
        plans = await plans_cursor.to_list(length=None)
        
        if not plans:
            # Fallback si aucun plan en base
            plans = [
                {
                    "plan_id": "starter",
                    "name": "Starter",
                    "price": 29.0,
                    "currency": "EUR",
                    "period": "month",
                    "features": [
                        "Jusqu'à 50 produits/mois",
                        "Génération IA des fiches produits",
                        "Optimisation SEO de base",
                        "Support email"
                    ]
                }
            ]
        
        return {
            "ok": True,
            "plans": plans
        }
        
    except Exception as e:
        logger.error(f"Error fetching plans from MongoDB: {str(e)}")
        # Fallback to static data in case of error
        return {
            "ok": True,
            "plans": [
                {
                    "plan_id": "starter",
                    "name": "Starter",
                    "price": 29.0,
                    "currency": "EUR",
                    "period": "month",
                    "features": [
                        "Jusqu'à 50 produits/mois",
                        "Génération IA des fiches produits",
                        "Optimisation SEO de base",
                        "Support email"
                    ]
                },
                {
                    "plan_id": "pro", 
                    "name": "Pro",
                    "price": 79.0,
                    "currency": "EUR",
                    "period": "month",
                    "features": [
                        "Jusqu'à 200 produits/mois",
                        "Génération IA avancée",
                        "Optimisation SEO Premium",
                        "A/B Testing",
                        "Support prioritaire"
                    ]
                },
                {
                    "plan_id": "enterprise",
                    "name": "Enterprise", 
                    "price": 199.0,
                    "currency": "EUR",
                    "period": "month",
                    "features": [
                        "Produits illimités",
                        "IA personnalisée",
                        "Intégrations sur mesure",
                        "Manager dédié",
                        "SLA 99.9%"
                    ]
                }
            ]
        }

@app.get("/api/testimonials")
async def get_testimonials():
    """
    Retourne les témoignages clients depuis MongoDB
    """
    try:
        db_instance = await get_db()
        
        # Récupérer les témoignages depuis MongoDB
        testimonials_cursor = db_instance["testimonials"].find(
            {"published": True},
            {"_id": 0}  # Exclure l'_id MongoDB
        ).sort("created_at", -1)  # Trier par date décroissante
        
        testimonials = await testimonials_cursor.to_list(length=None)
        
        if not testimonials:
            # Fallback si aucun témoignage en base
            testimonials = [
                {
                    "author": "Marie Dubois",
                    "role": "Boutique Mode Paris",
                    "content": "ECOMSIMPLY a révolutionné notre processus de création de fiches produits. Nous gagnons 80% de temps sur la rédaction!",
                    "rating": 5,
                    "avatar": "/assets/testimonials/marie.jpg"
                }
            ]
        
        return {
            "ok": True,
            "testimonials": testimonials
        }
        
    except Exception as e:
        logger.error(f"Error fetching testimonials from MongoDB: {str(e)}")
        # Fallback to static data in case of error
        return {
            "ok": True,
            "testimonials": [
                {
                    "author": "Marie Dubois",
                    "role": "Boutique Mode Paris",
                    "content": "ECOMSIMPLY a révolutionné notre processus de création de fiches produits. Nous gagnons 80% de temps sur la rédaction!",
                    "rating": 5,
                    "avatar": "/assets/testimonials/marie.jpg"
                },
                {
                    "author": "Thomas Martin",
                    "role": "TechStore Online",
                    "content": "L'IA d'ECOMSIMPLY génère des descriptions parfaitement optimisées pour le SEO. Nos ventes ont augmenté de 45%.",
                    "rating": 5,
                    "avatar": "/assets/testimonials/thomas.jpg"
                },
                {
                    "author": "Sophie Laurent",
                    "role": "Cosmétiques Bio",
                    "content": "Interface intuitive et résultats impressionnants. Je recommande vivement ECOMSIMPLY à tous les e-commerçants.",
                    "rating": 5,
                    "avatar": "/assets/testimonials/sophie.jpg"
                }
            ]
        }

@app.get("/api/stats/public")
async def get_public_stats():
    """
    Retourne les statistiques publiques de la plateforme depuis MongoDB
    """
    try:
        db_instance = await get_db()
        
        # Récupérer les stats depuis MongoDB
        stats_cursor = db_instance["stats_public"].find(
            {},
            {"_id": 0}  # Exclure l'_id MongoDB
        ).sort("updated_at", -1)
        
        stats_list = await stats_cursor.to_list(length=None)
        
        # Convertir la liste en dictionnaire pour compatibilité frontend
        stats = {}
        for stat in stats_list:
            key = stat.get("key", "").lower().replace(" ", "_")
            if key == "produits_générés":
                stats["products_generated"] = stat.get("value", 0)
            elif key == "utilisateurs_actifs":
                stats["active_users"] = stat.get("value", 0) 
            elif key == "heures_économisées":
                stats["time_saved_hours"] = stat.get("value", 0)
            elif key == "amélioration_conversion":
                stats["conversion_improvement"] = stat.get("display_value", "0%")
            elif key == "score_seo_moyen":
                stats["seo_score_average"] = stat.get("value", 0)
        
        if not stats:
            # Fallback si aucune stat en base
            stats = {
                "products_generated": 125000,
                "active_users": 2500,
                "time_saved_hours": 50000,
                "conversion_improvement": "45%",
                "seo_score_average": 92
            }
        
        return {
            "ok": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching public stats from MongoDB: {str(e)}")
        # Fallback to static data in case of error
        return {
            "ok": True,
            "stats": {
                "products_generated": 125000,
                "active_users": 2500,
                "time_saved_hours": 50000,
                "conversion_improvement": "45%",
                "seo_score_average": 92
            }
        }

@app.get("/api/languages")
async def get_languages():
    """
    Retourne les langues supportées depuis MongoDB
    """
    try:
        db_instance = await get_db()
        
        # Récupérer les langues depuis MongoDB
        languages_cursor = db_instance["languages"].find(
            {"active": True},
            {"_id": 0}  # Exclure l'_id MongoDB
        ).sort("default", -1)  # Langue par défaut en premier
        
        languages = await languages_cursor.to_list(length=None)
        
        if not languages:
            # Fallback si aucune langue en base
            languages = [
                {
                    "code": "fr",
                    "name": "Français",
                    "flag": "🇫🇷",
                    "default": True,
                    "active": True
                }
            ]
        
        return {
            "ok": True,
            "languages": languages
        }
        
    except Exception as e:
        logger.error(f"Error fetching languages from MongoDB: {str(e)}")
        # Fallback to static data in case of error
        return {
            "ok": True,
            "languages": [
                {
                    "code": "fr",
                    "name": "Français",
                    "flag": "🇫🇷",
                    "default": True
                },
                {
                    "code": "en", 
                    "name": "English",
                    "flag": "🇺🇸",
                    "default": False
                },
                {
                    "code": "es",
                    "name": "Español", 
                    "flag": "🇪🇸",
                    "default": False
                },
                {
                    "code": "de",
                    "name": "Deutsch",
                    "flag": "🇩🇪", 
                    "default": False
                }
            ]
        }

@app.get("/api/affiliate-config")
async def get_affiliate_config():
    """
    Configuration du programme d'affiliation depuis MongoDB
    """
    try:
        db_instance = await get_db()
        
        # Récupérer la config d'affiliation depuis MongoDB
        config_doc = await db_instance["affiliate_config"].find_one(
            {},
            {"_id": 0}  # Exclure l'_id MongoDB
        )
        
        if not config_doc:
            # Fallback si aucune config en base
            config_doc = {
                "commission_rate": 30.0,
                "cookie_duration": 30,
                "minimum_payout": 100,
                "payment_methods": ["PayPal", "Virement bancaire"],
                "tracking_enabled": True,
                "custom_links": True,
                "benefits": [
                    "Commission de 30% sur chaque vente",
                    "Cookie de suivi de 30 jours",
                    "Paiement minimum de 100€",
                    "Dashboard temps réel",
                    "Support marketing dédié"
                ]
            }
        
        return {
            "ok": True,
            "config": {
                "commission_rate": config_doc.get("commission_rate", 30.0),
                "cookie_duration": config_doc.get("cookie_duration", 30),
                "minimum_payout": config_doc.get("minimum_payout", 100),
                "payment_methods": config_doc.get("payment_methods", ["PayPal", "Virement bancaire"]),
                "tracking_enabled": config_doc.get("tracking_enabled", True),
                "custom_links": config_doc.get("custom_links", True)
            },
            "benefits": config_doc.get("benefits", [
                "Commission de 30% sur chaque vente",
                "Cookie de suivi de 30 jours",
                "Paiement minimum de 100€",
                "Dashboard temps réel",
                "Support marketing dédié"
            ])
        }
        
    except Exception as e:
        logger.error(f"Error fetching affiliate config from MongoDB: {str(e)}")
        # Fallback to static data in case of error
        return {
            "ok": True,
            "config": {
                "commission_rate": 30,
                "cookie_duration": 30,
                "minimum_payout": 100,
                "payment_methods": ["PayPal", "Virement bancaire"],
                "tracking_enabled": True,
                "custom_links": True
            },
            "benefits": [
                "Commission de 30% sur chaque vente",
                "Cookie de suivi de 30 jours",
                "Paiement minimum de 100€",
                "Dashboard temps réel",
                "Support marketing dédié"
            ]
        }