"""
Amazon Pricing Routes - Phase 4
Routes API pour la gestion des prix et règles Amazon
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from models.amazon_pricing import (
    PricingRule, PricingCalculation, PricingHistory, PricingBatch,
    PricingRuleResponse, PricingCalculationResponse, PricingHistoryResponse, 
    PricingBatchResponse, PricingDashboardData, PricingStrategy, 
    PricingRuleStatus
)
from services.amazon_pricing_rules_service import pricing_rules_service
from amazon.pricing_engine import pricing_engine
from modules.security import get_current_user_from_token

logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter(prefix="/api/amazon/pricing", tags=["Amazon Pricing"])


# ==================== MODÈLES DE REQUÊTE ====================

class CreatePricingRuleRequest(BaseModel):
    sku: str = Field(..., description="SKU Amazon du produit")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace Amazon")
    min_price: float = Field(..., gt=0, description="Prix minimum autorisé")
    max_price: float = Field(..., gt=0, description="Prix maximum autorisé")
    variance_pct: float = Field(default=5.0, ge=0, le=100, description="Variance % autorisée")
    map_price: Optional[float] = Field(None, description="Prix MAP")
    strategy: PricingStrategy = Field(..., description="Stratégie de pricing")
    margin_target: Optional[float] = Field(None, ge=0, le=100, description="Marge cible %")
    auto_update: bool = Field(default=True, description="Mise à jour automatique")
    update_frequency: int = Field(default=300, description="Fréquence MAJ en secondes")


class UpdatePricingRuleRequest(BaseModel):
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    variance_pct: Optional[float] = Field(None, ge=0, le=100)
    map_price: Optional[float] = None
    strategy: Optional[PricingStrategy] = None
    margin_target: Optional[float] = Field(None, ge=0, le=100)
    auto_update: Optional[bool] = None
    update_frequency: Optional[int] = None
    status: Optional[PricingRuleStatus] = None


class CalculatePriceRequest(BaseModel):
    sku: str = Field(..., description="SKU du produit")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace")
    dry_run: bool = Field(default=True, description="Simulation sans publication")


class PublishPriceRequest(BaseModel):
    sku: str = Field(..., description="SKU du produit")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace")
    method: str = Field(default="listings_items", description="listings_items ou feeds")
    force_update: bool = Field(default=False, description="Forcer même si prix identique")


class BatchPricingRequest(BaseModel):
    skus: List[str] = Field(..., description="Liste des SKUs à traiter")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace")
    force_update: bool = Field(default=False, description="Forcer MAJ même si prix identique")
    dry_run: bool = Field(default=False, description="Simulation sans publication")


# ==================== ROUTES RÈGLES DE PRICING ====================

@router.post("/rules", response_model=PricingRuleResponse)
async def create_pricing_rule(
    request: CreatePricingRuleRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Créer une nouvelle règle de pricing"""
    try:
        logger.info(f"Creating pricing rule for SKU {request.sku} by user {current_user['user_id']}")
        
        # Créer la règle
        rule = PricingRule(
            user_id=current_user['user_id'],
            sku=request.sku,
            marketplace_id=request.marketplace_id,
            min_price=request.min_price,
            max_price=request.max_price,
            variance_pct=request.variance_pct,
            map_price=request.map_price,
            strategy=request.strategy,
            margin_target=request.margin_target,
            auto_update=request.auto_update,
            update_frequency=request.update_frequency
        )
        
        rule_id = await pricing_rules_service.create_pricing_rule(rule)
        
        return PricingRuleResponse(
            success=True,
            rule=rule,
            message=f"Règle de pricing créée pour SKU {request.sku}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pricing rule: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la règle")


@router.get("/rules", response_model=List[PricingRule])
async def get_pricing_rules(
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    status: Optional[PricingRuleStatus] = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'éléments"),
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer les règles de pricing de l'utilisateur"""
    try:
        rules = await pricing_rules_service.get_user_pricing_rules(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return rules
        
    except Exception as e:
        logger.error(f"Error getting pricing rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des règles")


@router.get("/rules/{rule_id}", response_model=PricingRule)
async def get_pricing_rule(
    rule_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer une règle de pricing par ID"""
    try:
        rule = await pricing_rules_service.get_pricing_rule(
            user_id=current_user['user_id'],
            rule_id=rule_id
        )
        
        if not rule:
            raise HTTPException(status_code=404, detail="Règle non trouvée")
        
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pricing rule {rule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de la règle")


@router.put("/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: str,
    request: UpdatePricingRuleRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Mettre à jour une règle de pricing"""
    try:
        # Vérifier que la règle existe
        existing_rule = await pricing_rules_service.get_pricing_rule(
            user_id=current_user['user_id'],
            rule_id=rule_id
        )
        
        if not existing_rule:
            raise HTTPException(status_code=404, detail="Règle non trouvée")
        
        # Préparer les mises à jour
        updates = {}
        for field, value in request.model_dump(exclude_unset=True).items():
            if value is not None:
                updates[field] = value
        
        # Validation des prix
        if 'min_price' in updates or 'max_price' in updates:
            min_price = updates.get('min_price', existing_rule.min_price)
            max_price = updates.get('max_price', existing_rule.max_price)
            
            if max_price <= min_price:
                raise HTTPException(
                    status_code=400, 
                    detail="Le prix maximum doit être supérieur au prix minimum"
                )
        
        # Appliquer les mises à jour
        success = await pricing_rules_service.update_pricing_rule(
            user_id=current_user['user_id'],
            rule_id=rule_id,
            updates=updates
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Échec de la mise à jour")
        
        # Récupérer la règle mise à jour
        updated_rule = await pricing_rules_service.get_pricing_rule(
            user_id=current_user['user_id'],
            rule_id=rule_id
        )
        
        return PricingRuleResponse(
            success=True,
            rule=updated_rule,
            message="Règle de pricing mise à jour"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pricing rule {rule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour de la règle")


@router.delete("/rules/{rule_id}")
async def delete_pricing_rule(
    rule_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Supprimer une règle de pricing"""
    try:
        success = await pricing_rules_service.delete_pricing_rule(
            user_id=current_user['user_id'],
            rule_id=rule_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Règle non trouvée")
        
        return {"success": True, "message": "Règle de pricing supprimée"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pricing rule {rule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de la règle")


# ==================== ROUTES CALCUL ET PUBLICATION ====================

@router.post("/calculate", response_model=PricingCalculationResponse)
async def calculate_price(
    request: CalculatePriceRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Calculer le prix optimal pour un SKU"""
    try:
        logger.info(f"Calculating price for SKU {request.sku} by user {current_user['user_id']}")
        
        # Récupérer la règle de pricing
        rule = await pricing_rules_service.get_pricing_rule_by_sku(
            user_id=current_user['user_id'],
            sku=request.sku,
            marketplace_id=request.marketplace_id
        )
        
        if not rule:
            raise HTTPException(
                status_code=404, 
                detail=f"Aucune règle de pricing trouvée pour SKU {request.sku}"
            )
        
        # Obtenir le prix actuel (simulé pour l'instant)
        current_price = None  # TODO: Récupérer via SP-API
        
        # Calculer le prix optimal
        calculation = await pricing_engine.calculate_optimal_price(
            rule=rule,
            current_price=current_price
        )
        
        return PricingCalculationResponse(
            success=True,
            calculation=calculation,
            message=f"Calcul effectué pour SKU {request.sku}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating price for SKU {request.sku}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du calcul de prix")


@router.post("/publish", response_model=Dict[str, Any])
async def publish_price(
    request: PublishPriceRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_from_token)
):
    """Publier un prix optimisé sur Amazon"""
    try:
        logger.info(f"Publishing price for SKU {request.sku} by user {current_user['user_id']}")
        
        # Récupérer la règle de pricing
        rule = await pricing_rules_service.get_pricing_rule_by_sku(
            user_id=current_user['user_id'],
            sku=request.sku,
            marketplace_id=request.marketplace_id
        )
        
        if not rule:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune règle de pricing trouvée pour SKU {request.sku}"
            )
        
        # Calculer le prix optimal
        calculation = await pricing_engine.calculate_optimal_price(rule=rule)
        
        # Vérifier si une publication est nécessaire
        if not request.force_update and calculation.price_change == 0:
            return {
                "success": True,
                "message": "Aucun changement de prix nécessaire",
                "calculation": calculation.model_dump(),
                "published": False
            }
        
        # Vérifier les contraintes
        if not calculation.within_rules:
            return {
                "success": False,
                "message": "Prix calculé ne respecte pas les règles définies",
                "calculation": calculation.model_dump(),
                "published": False,
                "warnings": calculation.warnings
            }
        
        # Publier le prix
        publication_result = await pricing_engine.publish_price(
            sku=request.sku,
            marketplace_id=request.marketplace_id,
            new_price=calculation.recommended_price,
            method=request.method
        )
        
        # Sauvegarder l'historique
        history_entry = pricing_engine.create_pricing_history_entry(
            user_id=current_user['user_id'],
            rule=rule,
            calculation=calculation,
            publication_result=publication_result
        )
        
        background_tasks.add_task(
            pricing_rules_service.save_pricing_history,
            history_entry
        )
        
        # Mettre à jour le timestamp de dernière application
        background_tasks.add_task(
            pricing_rules_service.update_rule_last_applied,
            rule.id
        )
        
        return {
            "success": publication_result.get('success', False),
            "message": "Prix publié avec succès" if publication_result.get('success') else "Échec de la publication",
            "calculation": calculation.model_dump(),
            "publication_result": publication_result,
            "published": publication_result.get('success', False),
            "history_id": history_entry.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing price for SKU {request.sku}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la publication du prix")


@router.post("/batch", response_model=PricingBatchResponse)
async def create_batch_pricing(
    request: BatchPricingRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_from_token)
):
    """Lancer un traitement de pricing par lot"""
    try:
        logger.info(f"Creating batch pricing for {len(request.skus)} SKUs by user {current_user['user_id']}")
        
        # Créer le batch
        batch = PricingBatch(
            user_id=current_user['user_id'],
            skus=request.skus,
            marketplace_id=request.marketplace_id,
            force_update=request.force_update,
            dry_run=request.dry_run,
            total_skus=len(request.skus)
        )
        
        batch_id = await pricing_rules_service.create_pricing_batch(batch)
        
        # Lancer le traitement en arrière-plan
        background_tasks.add_task(
            process_batch_pricing,
            batch_id,
            current_user['user_id']
        )
        
        return PricingBatchResponse(
            success=True,
            batch=batch,
            message=f"Traitement par lot lancé pour {len(request.skus)} SKUs"
        )
        
    except Exception as e:
        logger.error(f"Error creating batch pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du traitement par lot")


@router.get("/batch/{batch_id}", response_model=PricingBatch)
async def get_batch_pricing(
    batch_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer le statut d'un traitement par lot"""
    try:
        batch = await pricing_rules_service.get_pricing_batch(
            user_id=current_user['user_id'],
            batch_id=batch_id
        )
        
        if not batch:
            raise HTTPException(status_code=404, detail="Traitement par lot non trouvé")
        
        return batch
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch pricing {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du traitement")


# ==================== ROUTES HISTORIQUE ====================

@router.get("/history", response_model=PricingHistoryResponse)
async def get_pricing_history(
    sku: Optional[str] = Query(None, description="Filtrer par SKU"),
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    days_back: int = Query(30, ge=1, le=365, description="Nombre de jours en arrière"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'éléments"),
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer l'historique de pricing"""
    try:
        history = await pricing_rules_service.get_pricing_history(
            user_id=current_user['user_id'],
            sku=sku,
            marketplace_id=marketplace_id,
            days_back=days_back,
            skip=skip,
            limit=limit
        )
        
        # Compter le total pour pagination
        total_count = len(history)  # Approximation
        
        return PricingHistoryResponse(
            success=True,
            history=history,
            total_count=total_count,
            page=skip // limit + 1,
            per_page=limit,
            message=f"{len(history)} entrées d'historique récupérées"
        )
        
    except Exception as e:
        logger.error(f"Error getting pricing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")


@router.get("/history/{sku}", response_model=List[PricingHistory])
async def get_sku_pricing_history(
    sku: str,
    marketplace_id: str = Query("A13V1IB3VIYZZH", description="ID marketplace"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'éléments"),
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer l'historique pour un SKU spécifique"""
    try:
        history = await pricing_rules_service.get_sku_pricing_history(
            user_id=current_user['user_id'],
            sku=sku,
            marketplace_id=marketplace_id,
            limit=limit
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting SKU pricing history for {sku}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique SKU")


# ==================== ROUTES DASHBOARD ====================

@router.get("/dashboard", response_model=PricingDashboardData)
async def get_pricing_dashboard(
    marketplace_id: str = Query("A13V1IB3VIYZZH", description="ID marketplace"),
    current_user = Depends(get_current_user_from_token)
):
    """Récupérer les données du dashboard pricing"""
    try:
        dashboard_data = await pricing_rules_service.get_dashboard_data(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting pricing dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du dashboard")


# ==================== FONCTIONS UTILITAIRES ====================

async def process_batch_pricing(batch_id: str, user_id: str):
    """Traiter un lot de pricing en arrière-plan"""
    try:
        logger.info(f"Processing batch pricing {batch_id}")
        
        # Récupérer le batch
        batch = await pricing_rules_service.get_pricing_batch(user_id, batch_id)
        if not batch:
            logger.error(f"Batch {batch_id} not found")
            return
        
        # Marquer comme démarré
        await pricing_rules_service.pricing_batches_collection.update_one(
            {"id": batch_id},
            {"$set": {"status": "processing", "started_at": datetime.utcnow()}}
        )
        
        # Traiter chaque SKU
        results = []
        processed = 0
        successful = 0
        failed = 0
        
        for sku in batch.skus:
            try:
                # Récupérer la règle
                rule = await pricing_rules_service.get_pricing_rule_by_sku(
                    user_id=user_id,
                    sku=sku,
                    marketplace_id=batch.marketplace_id
                )
                
                if not rule:
                    results.append({
                        "sku": sku,
                        "success": False,
                        "error": "Aucune règle de pricing trouvée"
                    })
                    failed += 1
                else:
                    # Calculer le prix
                    calculation = await pricing_engine.calculate_optimal_price(rule=rule)
                    
                    if batch.dry_run:
                        # Mode simulation
                        results.append({
                            "sku": sku,
                            "success": True,
                            "simulation": True,
                            "calculation": calculation.model_dump()
                        })
                        successful += 1
                    else:
                        # Publication réelle
                        if calculation.within_rules and (batch.force_update or calculation.price_change != 0):
                            publication_result = await pricing_engine.publish_price(
                                sku=sku,
                                marketplace_id=batch.marketplace_id,
                                new_price=calculation.recommended_price
                            )
                            
                            # Sauvegarder l'historique
                            history_entry = pricing_engine.create_pricing_history_entry(
                                user_id=user_id,
                                rule=rule,
                                calculation=calculation,
                                publication_result=publication_result
                            )
                            
                            await pricing_rules_service.save_pricing_history(history_entry)
                            
                            results.append({
                                "sku": sku,
                                "success": publication_result.get('success', False),
                                "calculation": calculation.model_dump(),
                                "publication_result": publication_result
                            })
                            
                            if publication_result.get('success'):
                                successful += 1
                            else:
                                failed += 1
                        else:
                            results.append({
                                "sku": sku,
                                "success": True,
                                "skipped": True,
                                "reason": "Aucun changement nécessaire ou hors règles"
                            })
                            successful += 1
                
                processed += 1
                
                # Mettre à jour le progrès
                await pricing_rules_service.update_batch_progress(
                    batch_id=batch_id,
                    processed_skus=processed,
                    successful_updates=successful,
                    failed_updates=failed,
                    results=results
                )
                
                # Pause entre les SKUs pour éviter la surcharge API
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing SKU {sku} in batch {batch_id}: {str(e)}")
                results.append({
                    "sku": sku,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                processed += 1
        
        logger.info(f"Batch pricing {batch_id} completed: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Error processing batch pricing {batch_id}: {str(e)}")
        
        # Marquer le batch comme échoué
        await pricing_rules_service.pricing_batches_collection.update_one(
            {"id": batch_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "errors": [str(e)]
                }
            }
        )