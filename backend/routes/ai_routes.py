#!/usr/bin/env python3
"""
AI Routes - AI Sessions and Events Management
Endpoints for managing AI conversations and product generation history
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

# Create router
ai_router = APIRouter(prefix="/api/ai", tags=["ai"])

# Pydantic models
class ProductGenerationRequest(BaseModel):
    product_name: str
    product_description: Optional[str] = None
    category: Optional[str] = None
    target_audience: Optional[str] = None
    language: Optional[str] = "fr"
    include_seo: Optional[bool] = True
    include_images: Optional[bool] = True

class AISessionCreate(BaseModel):
    session_type: str  # "product_generation", "chat", "support"
    initial_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

# Import database connection
from database import get_db

@ai_router.post("/product-generation")
async def generate_product_sheet(request: Request, generation_data: ProductGenerationRequest):
    """
    Generate a product sheet using AI
    """
    try:
        db_instance = await get_db()
        
        # Extract user info from JWT token (simplified for now)
        # In a real implementation, you'd decode the JWT token
        user_id = "demo_user"  # Placeholder
        
        # Create product generation record
        generation_doc = {
            "userId": user_id,
            "product_name": generation_data.product_name.strip(),
            "product_description": generation_data.product_description,
            "category": generation_data.category,
            "target_audience": generation_data.target_audience,
            "language": generation_data.language,
            "include_seo": generation_data.include_seo,
            "include_images": generation_data.include_images,
            "status": "completed",  # For demo purposes
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "outputs": {
                "title": f"{generation_data.product_name} - Version Optimisée",
                "description": f"Description générée par IA pour {generation_data.product_name}. Produit de haute qualité avec caractéristiques premium.",
                "seo_keywords": ["produit", "qualité", "premium"],
                "meta_description": f"Découvrez {generation_data.product_name} - Le choix idéal pour vos besoins."
            }
        }
        
        # Insert generation record
        result = await db_instance["product_generations"].insert_one(generation_doc)
        
        if result.inserted_id:
            logger.info(f"Product generation created - ID: {result.inserted_id}, Product: {generation_data.product_name}")
            
            return {
                "ok": True,
                "generation_id": str(result.inserted_id),
                "outputs": generation_doc["outputs"],
                "message": "Fiche produit générée avec succès"
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la génération")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating product sheet: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la génération")

@ai_router.get("/product-generations")
async def get_product_generations(request: Request, limit: int = 20):
    """
    Get product generation history for the current user
    """
    try:
        db_instance = await get_db()
        
        # Extract user info from JWT token (simplified for now)
        user_id = "demo_user"  # Placeholder
        
        # Find product generations
        generations_cursor = db_instance["product_generations"].find(
            {"userId": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        generations = await generations_cursor.to_list(length=limit)
        
        return {
            "ok": True,
            "generations": generations,
            "total": len(generations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching product generations: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")

@ai_router.post("/session")
async def create_ai_session(request: Request, session_data: AISessionCreate):
    """
    Create a new AI session for tracking conversations
    """
    try:
        db_instance = await get_db()
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        user_id = "demo_user"  # Placeholder
        
        # Create session document
        session_doc = {
            "sessionId": session_id,
            "userId": user_id,
            "sessionType": session_data.session_type,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": session_data.metadata or {}
        }
        
        # Insert session
        result = await db_instance["ai_sessions"].insert_one(session_doc)
        
        if result.inserted_id:
            logger.info(f"AI session created - Session ID: {session_id}, Type: {session_data.session_type}")
            
            return {
                "ok": True,
                "session_id": session_id,
                "message": "Session IA créée avec succès"
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la création de la session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating AI session: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la création de session")

@ai_router.get("/sessions")
async def get_ai_sessions(request: Request, limit: int = 10):
    """
    Get AI sessions for the current user
    """
    try:
        db_instance = await get_db()
        
        user_id = "demo_user"  # Placeholder
        
        # Find AI sessions
        sessions_cursor = db_instance["ai_sessions"].find(
            {"userId": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        sessions = await sessions_cursor.to_list(length=limit)
        
        return {
            "ok": True,
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error fetching AI sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des sessions")