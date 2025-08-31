#!/usr/bin/env python3
"""
Messages Routes - Contact/Support System
Endpoints for managing contact messages and support tickets
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# Create router
messages_router = APIRouter(prefix="/api/messages", tags=["messages"])

# Pydantic models
class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    source: Optional[str] = "website"
    phone: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    status: str
    source: str
    created_at: datetime
    phone: Optional[str] = None

# Import database connection
from database import get_db

@messages_router.post("/contact")
async def submit_contact_message(message_data: ContactMessage):
    """
    Submit a new contact message
    """
    try:
        db_instance = await get_db()
        
        # Create message document
        message_doc = {
            "name": message_data.name.strip(),
            "email": message_data.email.strip(),
            "subject": message_data.subject.strip(),
            "message": message_data.message.strip(),
            "source": message_data.source or "website",
            "phone": message_data.phone.strip() if message_data.phone else None,
            "status": "new",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert message
        result = await db_instance["messages"].insert_one(message_doc)
        
        if result.inserted_id:
            logger.info(f"Contact message created - ID: {result.inserted_id}, Email: {message_data.email}")
            
            return {
                "ok": True,
                "message_id": str(result.inserted_id),
                "message": "Message envoyé avec succès. Nous vous répondrons sous 24h."
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact message: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de l'envoi du message")

@messages_router.get("/user/{user_id}")
async def get_user_messages(user_id: str):
    """
    Get messages for a specific user (for support dashboard)
    """
    try:
        db_instance = await get_db()
        
        # Find messages by user email or user_id if they're logged in
        messages_cursor = db_instance["messages"].find(
            {"$or": [{"userId": user_id}, {"email": user_id}]},
            {"_id": 0}
        ).sort("created_at", -1)
        
        messages = await messages_cursor.to_list(length=20)  # Limit to 20 most recent
        
        return {
            "ok": True,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error fetching user messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des messages")