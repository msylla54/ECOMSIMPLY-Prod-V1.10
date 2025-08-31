"""
Amazon Closed-Loop Optimizer - Phase 5
Optimiseur automatique pour la correction continue des listings Amazon
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
from dataclasses import dataclass

from models.amazon_monitoring import (
    ProductSnapshot, DesiredState, OptimizationDecision, MonitoringAlert,
    OptimizationAction, OptimizationStatus, BuyBoxStatus
)
from amazon.pricing_engine import pricing_engine
from integrations.amazon.client import AmazonSPAPIClient

logger = logging.getLogger(__name__)


@dataclass
class StateComparison:
    """Résultat de comparaison entre état désiré et observé"""
    has_differences: bool
    differences: Dict[str, Any]
    priority_score: int
    confidence_score: float
    risk_score: float


class AmazonClosedLoopOptimizer:
    """
    Optimiseur en boucle fermée pour Amazon
    
    Responsabilités:
    - Comparer l'état désiré vs l'état observé (snapshots)
    - Identifier les écarts nécessitant une correction
    - Générer et exécuter les actions de correction
    - Publier les changements via SP-API
    - Suivre l'efficacité des corrections
    """
    
    def __init__(self):
        self.sp_api_client = AmazonSPAPIClient()
        
        # Configuration des seuils
        self.thresholds = {
            'price_deviation_percent': 0.05,  # 5% d'écart max
            'buybox_loss_priority': 9,        # Priorité élevée
            'seo_score_minimum': 0.7,         # Score SEO minimum
            'correction_frequency_hours': 12,  # Fréquence max corrections
            'max_price_change_percent': 0.15,  # 15% changement prix max
        }
        
        # Statistiques
        self.stats = {
            'total_comparisons': 0,
            'differences_detected': 0,
            'corrections_applied': 0,
            'corrections_successful': 0,
            'corrections_failed': 0,
            'last_run': None
        }
    
    async def run_optimization_cycle(self):
        """Exécuter un cycle complet d'optimisation"""
        cycle_start = time.time()
        
        try:
            logger.info("🎯 Starting closed-loop optimization cycle")
            
            # 1. Récupérer tous les snapshots récents qui nécessitent une analyse
            snapshots = await self._get_snapshots_for_optimization()
            
            if not snapshots:
                logger.info("📭 No snapshots found for optimization")
                return
            
            logger.info(f"🔍 Analyzing {len(snapshots)} product snapshots")
            
            processed = 0
            corrections_made = 0
            
            # 2. Analyser chaque snapshot
            for snapshot in snapshots:
                try:
                    decision = await self._analyze_and_optimize(snapshot)
                    
                    if decision and decision.status == OptimizationStatus.COMPLETED:
                        corrections_made += 1
                    
                    processed += 1
                    
                    # Rate limiting entre analyses
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Error optimizing SKU {snapshot.sku}: {str(e)}")
                    continue
            
            # 3. Mettre à jour les statistiques
            duration = time.time() - cycle_start
            await self._update_cycle_stats(processed, corrections_made, duration)
            
            logger.info(f"✅ Optimization cycle completed: {processed} analyzed, {corrections_made} corrected, {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Critical error in optimization cycle: {str(e)}")
            raise
    
    async def _analyze_and_optimize(self, snapshot: ProductSnapshot) -> Optional[OptimizationDecision]:
        """Analyser un snapshot et appliquer les optimisations nécessaires"""
        
        try:
            logger.debug(f"🔍 Analyzing snapshot for SKU {snapshot.sku}")
            
            # 1. Récupérer l'état désiré pour ce SKU
            desired_state = await self._get_desired_state(
                snapshot.user_id, 
                snapshot.sku, 
                snapshot.marketplace_id
            )
            
            if not desired_state:
                logger.debug(f"⏭️ No desired state found for SKU {snapshot.sku}, skipping")
                return None
            
            # 2. Comparer état désiré vs observé
            comparison = await self._compare_states(desired_state, snapshot)
            
            self.stats['total_comparisons'] += 1
            
            if not comparison.has_differences:
                logger.debug(f"✅ SKU {snapshot.sku} is in desired state, no action needed")
                return None
            
            self.stats['differences_detected'] += 1
            
            # 3. Créer la décision d'optimisation
            decision = await self._create_optimization_decision(
                snapshot, desired_state, comparison
            )
            
            # 4. Vérifier les conditions de sécurité
            if not await self._safety_check(decision):
                logger.warning(f"⚠️ Safety check failed for SKU {snapshot.sku}, skipping optimization")
                decision.status = OptimizationStatus.FAILED
                decision.error_message = "Safety check failed"
                await self._save_optimization_decision(decision)
                return decision
            
            # 5. Exécuter l'optimisation
            success = await self._execute_optimization(decision)
            
            # 6. Sauvegarder la décision
            await self._save_optimization_decision(decision)
            
            if success:
                logger.info(f"✅ Successfully optimized SKU {snapshot.sku}: {decision.action_type.value}")
                self.stats['corrections_successful'] += 1
            else:
                logger.warning(f"❌ Failed to optimize SKU {snapshot.sku}: {decision.error_message}")
                self.stats['corrections_failed'] += 1
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Error analyzing snapshot for SKU {snapshot.sku}: {str(e)}")
            return None
    
    async def _compare_states(
        self, 
        desired: DesiredState, 
        observed: ProductSnapshot
    ) -> StateComparison:
        """Comparer l'état désiré avec l'état observé"""
        
        differences = {}
        priority_score = 1
        confidence_score = 1.0
        risk_score = 0.0
        
        # 1. Comparaison des prix
        if desired.desired_price and observed.current_price:
            price_diff_percent = abs(desired.desired_price - observed.current_price) / desired.desired_price
            
            if price_diff_percent > self.thresholds['price_deviation_percent']:
                differences['price'] = {
                    'desired': desired.desired_price,
                    'observed': observed.current_price,
                    'deviation_percent': price_diff_percent * 100,
                    'action_required': 'price_update'
                }
                priority_score = max(priority_score, 7)
                
                # Priorité élevée si Buy Box perdue à cause du prix
                if observed.buybox_status == BuyBoxStatus.LOST:
                    priority_score = self.thresholds['buybox_loss_priority']
        
        # 2. Comparaison SEO
        seo_differences = {}
        
        if desired.desired_title and observed.title:
            if desired.desired_title.strip() != observed.title.strip():
                seo_differences['title'] = {
                    'desired': desired.desired_title,
                    'observed': observed.title
                }
        
        if desired.desired_description and observed.description:
            if desired.desired_description.strip() != observed.description.strip():
                seo_differences['description'] = {
                    'desired': desired.desired_description,
                    'observed': observed.description
                }
        
        if desired.desired_bullet_points and observed.bullet_points:
            if set(desired.desired_bullet_points) != set(observed.bullet_points):
                seo_differences['bullet_points'] = {
                    'desired': desired.desired_bullet_points,
                    'observed': observed.bullet_points
                }
        
        if seo_differences:
            differences['seo'] = seo_differences
            priority_score = max(priority_score, 5)
        
        # 3. Comparaison Buy Box
        if observed.buybox_status in [BuyBoxStatus.LOST, BuyBoxStatus.NOT_ELIGIBLE]:
            differences['buybox'] = {
                'status': observed.buybox_status.value,
                'our_price': observed.current_price,
                'buybox_price': observed.buybox_price,
                'action_required': 'price_optimization'
            }
            priority_score = max(priority_score, self.thresholds['buybox_loss_priority'])
        
        # 4. Calcul des scores
        
        # Confidence basée sur la qualité des données
        confidence_score = observed.data_completeness_score
        
        # Risk basé sur l'amplitude des changements
        if 'price' in differences:
            price_change = differences['price']['deviation_percent']
            if price_change > 10:  # Plus de 10% de changement
                risk_score = min(risk_score + 0.3, 1.0)
        
        if len(differences.get('seo', {})) > 2:  # Plusieurs changements SEO
            risk_score = min(risk_score + 0.2, 1.0)
        
        has_differences = len(differences) > 0
        
        return StateComparison(
            has_differences=has_differences,
            differences=differences,
            priority_score=priority_score,
            confidence_score=confidence_score,
            risk_score=risk_score
        )
    
    async def _create_optimization_decision(
        self,
        snapshot: ProductSnapshot,
        desired_state: DesiredState,
        comparison: StateComparison
    ) -> OptimizationDecision:
        """Créer une décision d'optimisation"""
        
        # Déterminer le type d'action principal
        action_type = OptimizationAction.AUTO_CORRECTION
        
        if 'price' in comparison.differences:
            action_type = OptimizationAction.PRICE_UPDATE
        elif 'seo' in comparison.differences:
            action_type = OptimizationAction.SEO_UPDATE
        elif 'buybox' in comparison.differences:
            action_type = OptimizationAction.PRICE_UPDATE  # Correction pour récupérer Buy Box
        
        # Construire le plan d'exécution
        execution_plan = await self._build_execution_plan(comparison.differences)
        
        # Génération du raisonnement
        reasoning = self._generate_reasoning(comparison)
        
        decision = OptimizationDecision(
            job_id=snapshot.job_id,
            user_id=snapshot.user_id,
            sku=snapshot.sku,
            marketplace_id=snapshot.marketplace_id,
            current_snapshot_id=snapshot.id,
            desired_state_id=desired_state.id,
            action_type=action_type,
            priority=comparison.priority_score,
            detected_changes=comparison.differences,
            recommended_changes=execution_plan,
            reasoning=reasoning,
            confidence_score=comparison.confidence_score,
            risk_score=comparison.risk_score,
            execution_plan=execution_plan,
            status=OptimizationStatus.PENDING
        )
        
        return decision
    
    async def _build_execution_plan(self, differences: Dict[str, Any]) -> Dict[str, Any]:
        """Construire le plan d'exécution pour les corrections"""
        
        plan = {
            'steps': [],
            'sp_api_calls': [],
            'estimated_duration_minutes': 0
        }
        
        # 1. Corrections de prix
        if 'price' in differences:
            price_data = differences['price']
            
            plan['steps'].append({
                'action': 'update_price',
                'current_price': price_data['observed'],
                'new_price': price_data['desired'],
                'method': 'listings_items_api'
            })
            
            plan['sp_api_calls'].append({
                'api': 'listings_items',
                'method': 'PATCH',
                'endpoint': '/listings/2021-08-01/items/{sku}',
                'estimated_duration_seconds': 3
            })
            
            plan['estimated_duration_minutes'] += 1
        
        # 2. Corrections SEO
        if 'seo' in differences:
            seo_data = differences['seo']
            
            plan['steps'].append({
                'action': 'update_seo',
                'changes': seo_data,
                'method': 'listings_items_api'
            })
            
            plan['sp_api_calls'].append({
                'api': 'listings_items',
                'method': 'PATCH', 
                'endpoint': '/listings/2021-08-01/items/{sku}',
                'estimated_duration_seconds': 5
            })
            
            plan['estimated_duration_minutes'] += 2
        
        # 3. Corrections Buy Box (via pricing)
        if 'buybox' in differences:
            buybox_data = differences['buybox']
            
            if buybox_data.get('buybox_price') and buybox_data.get('our_price'):
                # Calculer prix compétitif
                competitive_price = buybox_data['buybox_price'] - 0.01
                
                plan['steps'].append({
                    'action': 'recover_buybox',
                    'current_price': buybox_data['our_price'],
                    'competitive_price': competitive_price,
                    'method': 'pricing_optimization'
                })
                
                plan['estimated_duration_minutes'] += 1
        
        return plan
    
    def _generate_reasoning(self, comparison: StateComparison) -> str:
        """Générer l'explication du raisonnement"""
        
        reasons = []
        
        if 'price' in comparison.differences:
            price_data = comparison.differences['price']
            deviation = price_data['deviation_percent']
            reasons.append(f"Prix dévie de {deviation:.1f}% par rapport à la stratégie définie")
        
        if 'seo' in comparison.differences:
            seo_changes = len(comparison.differences['seo'])
            reasons.append(f"{seo_changes} éléments SEO ne correspondent pas à l'état désiré")
        
        if 'buybox' in comparison.differences:
            buybox_status = comparison.differences['buybox']['status']
            reasons.append(f"Buy Box perdue (statut: {buybox_status}), correction nécessaire")
        
        reasoning = "Auto-correction déclenchée: " + "; ".join(reasons)
        reasoning += f" (Priorité: {comparison.priority_score}, Confiance: {comparison.confidence_score:.2f})"
        
        return reasoning
    
    async def _safety_check(self, decision: OptimizationDecision) -> bool:
        """Vérifications de sécurité avant exécution"""
        
        # 1. Vérifier fréquence des corrections
        recent_corrections = await self._get_recent_corrections(
            decision.sku, 
            decision.marketplace_id,
            hours=self.thresholds['correction_frequency_hours']
        )
        
        if len(recent_corrections) >= 3:  # Max 3 corrections par période
            logger.warning(f"⚠️ Too many recent corrections for SKU {decision.sku}")
            return False
        
        # 2. Vérifier amplitude des changements de prix
        if decision.action_type == OptimizationAction.PRICE_UPDATE:
            price_changes = decision.detected_changes.get('price', {})
            if price_changes:
                deviation = price_changes.get('deviation_percent', 0)
                if deviation > self.thresholds['max_price_change_percent'] * 100:
                    logger.warning(f"⚠️ Price change too large for SKU {decision.sku}: {deviation:.1f}%")
                    return False
        
        # 3. Vérifier score de confiance
        if decision.confidence_score < 0.7:
            logger.warning(f"⚠️ Low confidence score for SKU {decision.sku}: {decision.confidence_score:.2f}")
            return False
        
        # 4. Vérifier score de risque
        if decision.risk_score > 0.8:
            logger.warning(f"⚠️ High risk score for SKU {decision.sku}: {decision.risk_score:.2f}")
            return False
        
        return True
    
    async def _execute_optimization(self, decision: OptimizationDecision) -> bool:
        """Exécuter la décision d'optimisation"""
        
        try:
            decision.execution_started_at = datetime.utcnow()
            decision.status = OptimizationStatus.IN_PROGRESS
            start_time = time.time()
            
            success = False
            
            # Exécuter selon le type d'action
            if decision.action_type == OptimizationAction.PRICE_UPDATE:
                success = await self._execute_price_update(decision)
            
            elif decision.action_type == OptimizationAction.SEO_UPDATE:
                success = await self._execute_seo_update(decision)
            
            elif decision.action_type == OptimizationAction.AUTO_CORRECTION:
                success = await self._execute_auto_correction(decision)
            
            # Finaliser l'exécution
            decision.execution_completed_at = datetime.utcnow()
            decision.execution_duration_ms = int((time.time() - start_time) * 1000)
            
            if success:
                decision.status = OptimizationStatus.COMPLETED
                decision.success = True
                self.stats['corrections_applied'] += 1
            else:
                decision.status = OptimizationStatus.FAILED
                decision.success = False
            
            return success
            
        except Exception as e:
            decision.status = OptimizationStatus.FAILED
            decision.success = False
            decision.error_message = str(e)
            decision.execution_completed_at = datetime.utcnow()
            
            logger.error(f"❌ Error executing optimization for SKU {decision.sku}: {str(e)}")
            return False
    
    async def _execute_price_update(self, decision: OptimizationDecision) -> bool:
        """Exécuter une mise à jour de prix"""
        
        try:
            price_changes = decision.detected_changes.get('price', {})
            if not price_changes:
                return False
            
            new_price = price_changes['desired']
            
            # Utiliser le pricing engine existant
            result = await pricing_engine.publish_price(
                sku=decision.sku,
                marketplace_id=decision.marketplace_id,
                new_price=new_price,
                method="listings_items"
            )
            
            # Enregistrer la réponse SP-API
            decision.sp_api_responses.append(result)
            
            success = result.get('success', False)
            
            if not success:
                decision.error_message = result.get('error', 'Prix update failed')
            
            return success
            
        except Exception as e:
            decision.error_message = f"Error executing price update: {str(e)}"
            return False
    
    async def _execute_seo_update(self, decision: OptimizationDecision) -> bool:
        """Exécuter une mise à jour SEO"""
        
        try:
            seo_changes = decision.detected_changes.get('seo', {})
            if not seo_changes:
                return False
            
            # Construire le payload pour Listings Items API
            patches = []
            
            if 'title' in seo_changes:
                patches.append({
                    "op": "replace",
                    "path": "/attributes/item_name",
                    "value": seo_changes['title']['desired']
                })
            
            if 'description' in seo_changes:
                patches.append({
                    "op": "replace", 
                    "path": "/attributes/description",
                    "value": seo_changes['description']['desired']
                })
            
            if 'bullet_points' in seo_changes:
                patches.append({
                    "op": "replace",
                    "path": "/attributes/bullet_points",
                    "value": seo_changes['bullet_points']['desired']
                })
            
            if not patches:
                return False
            
            # Appel SP-API
            response = await self.sp_api_client.make_request(
                method="PATCH",
                endpoint=f"/listings/2021-08-01/items/{decision.sku}",
                json_data={
                    "productType": "PRODUCT",
                    "patches": patches
                },
                marketplace_id=decision.marketplace_id,
                params={"marketplaceIds": decision.marketplace_id}
            )
            
            # Enregistrer la réponse
            decision.sp_api_responses.append(response)
            
            success = response.get('success', False)
            
            if not success:
                decision.error_message = response.get('error', 'SEO update failed')
            
            return success
            
        except Exception as e:
            decision.error_message = f"Error executing SEO update: {str(e)}"
            return False
    
    async def _execute_auto_correction(self, decision: OptimizationDecision) -> bool:
        """Exécuter une correction automatique (combinaison prix + SEO)"""
        
        try:
            success_count = 0
            total_actions = 0
            
            # Exécuter correction de prix si nécessaire
            if 'price' in decision.detected_changes:
                total_actions += 1
                if await self._execute_price_update(decision):
                    success_count += 1
                
                # Attendre entre les actions
                await asyncio.sleep(2)
            
            # Exécuter correction SEO si nécessaire
            if 'seo' in decision.detected_changes:
                total_actions += 1
                if await self._execute_seo_update(decision):
                    success_count += 1
            
            # Succès si au moins une action réussie
            return success_count > 0 and success_count == total_actions
            
        except Exception as e:
            decision.error_message = f"Error executing auto correction: {str(e)}"
            return False
    
    # Helper methods (à implémenter avec service DB)
    
    async def _get_snapshots_for_optimization(self) -> List[ProductSnapshot]:
        """Récupérer les snapshots nécessitant une analyse"""
        # TODO: Implémenter avec service MongoDB
        return []
    
    async def _get_desired_state(
        self, 
        user_id: str, 
        sku: str, 
        marketplace_id: str
    ) -> Optional[DesiredState]:
        """Récupérer l'état désiré pour un SKU"""
        # TODO: Implémenter avec service MongoDB
        return None
    
    async def _save_optimization_decision(self, decision: OptimizationDecision):
        """Sauvegarder une décision d'optimisation"""
        # TODO: Implémenter avec service MongoDB
        pass
    
    async def _get_recent_corrections(
        self, 
        sku: str, 
        marketplace_id: str, 
        hours: int
    ) -> List[OptimizationDecision]:
        """Récupérer les corrections récentes pour un SKU"""
        # TODO: Implémenter avec service MongoDB
        return []
    
    async def _update_cycle_stats(self, processed: int, corrected: int, duration: float):
        """Mettre à jour les statistiques de cycle"""
        self.stats['last_run'] = datetime.utcnow()


# Instance globale de l'optimiseur
closed_loop_optimizer = AmazonClosedLoopOptimizer()