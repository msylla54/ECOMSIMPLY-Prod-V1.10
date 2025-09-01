"""
Email Service Module for ECOMSIMPLY
Handles SMTP email sending for trial notifications, reminders, and confirmations
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending trial notifications and reminders"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'ecomsimply.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '465'))
        self.username = os.environ.get('SMTP_USERNAME', 'contact@ecomsimply.com')
        self.password = os.environ.get('SMTP_PASSWORD', '')
        self.use_ssl = os.environ.get('SMTP_USE_SSL', 'true').lower() == 'true'
        self.sender_email = os.environ.get('SENDER_EMAIL', 'contact@ecomsimply.com')
        
    def _create_connection(self):
        """Create SMTP connection with SSL/TLS"""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=5)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
                server.starttls()
            
            server.login(self.username, self.password)
            logger.info(f"✅ SMTP connection established to {self.smtp_server}:{self.smtp_port}")
            return server
        except Exception as e:
            logger.error(f"❌ Failed to create SMTP connection: {str(e)}")
            raise
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email with HTML and optional text content"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # Create text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            with self._create_connection() as server:
                server.sendmail(self.sender_email, to_email, message.as_string())
                logger.info(f"✅ Email sent successfully to {to_email}: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_trial_welcome_email(self, user_email: str, user_name: str, plan_type: str, trial_end_date: datetime) -> bool:
        """Send welcome email for trial users"""
        
        plan_name = "Premium"
        price = "99€"
        
        subject = f"🎉 Bienvenue dans votre essai gratuit {plan_name} - ECOMSIMPLY"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .trial-info {{ background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Votre essai gratuit a commencé !</h1>
            </div>
            
            <div class="content">
                <h2>Bonjour {user_name},</h2>
                
                <p>Félicitations ! Votre essai gratuit de 3 jours pour le plan <strong>{plan_name}</strong> a commencé avec succès.</p>
                
                <div class="trial-info">
                    <h3>📋 Détails de votre essai :</h3>
                    <ul>
                        <li><strong>Plan :</strong> {plan_name} ({price}/mois)</li>
                        <li><strong>Début de l'essai :</strong> Aujourd'hui</li>
                        <li><strong>Fin de l'essai :</strong> {trial_end_date.strftime('%d/%m/%Y à %H:%M')}</li>
                        <li><strong>Accès :</strong> Toutes les fonctionnalités {plan_name}</li>
                    </ul>
                </div>
                
                <h3>✨ Que pouvez-vous faire pendant votre essai ?</h3>
                <ul>
                    <li>🖼️ Générer des images haute qualité avec l'IA</li>
                    <li>📊 Accéder à tous les outils Premium avancés</li>
                    <li>💼 Créer des fiches produits professionnelles</li>
                    <li>📈 Utiliser les analytics avancés</li>
                    <li>🔧 Bénéficier du support prioritaire</li>
                </ul>
                
                <div class="warning">
                    <h3>⚠️ Important à retenir :</h3>
                    <p>Après les 3 jours d'essai gratuit, votre abonnement sera automatiquement renouvelé au prix de <strong>{price}/mois</strong>.</p>
                    <p>Vous pouvez annuler à tout moment depuis votre tableau de bord pour éviter tout prélèvement.</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="https://ecomsimply.com" class="button">🏠 Accéder au Tableau de Bord</a>
                    <a href="https://ecomsimply.com/help" class="button">📚 Guide d'Utilisation</a>
                </div>
                
                <p>Si vous avez des questions, n'hésitez pas à nous contacter à <a href="mailto:contact@ecomsimply.com">contact@ecomsimply.com</a></p>
                
                <p>Bonne découverte ! 🎉</p>
                
                <p>L'équipe ECOMSIMPLY</p>
            </div>
            
            <div class="footer">
                <p>© 2025 ECOMSIMPLY - Votre assistant IA pour l'e-commerce</p>
                <p>Pour vous désabonner ou gérer vos préférences email, <a href="https://ecomsimply.com/unsubscribe">cliquez ici</a></p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_trial_reminder_email(self, user_email: str, user_name: str, plan_type: str, days_remaining: int, trial_end_date: datetime) -> bool:
        """Send reminder email for trial users"""
        
        plan_name = "Premium"
        price = "99€"
        
        if days_remaining == 3:
            subject = f"⏰ Plus que 3 jours d'essai gratuit {plan_name} - ECOMSIMPLY"
        elif days_remaining == 1:
            subject = f"🚨 Dernier jour d'essai gratuit {plan_name} - ECOMSIMPLY"
        else:
            subject = f"⏰ Plus que {days_remaining} jours d'essai gratuit {plan_name} - ECOMSIMPLY"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .countdown {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }}
                .button {{ display: inline-block; background: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .button-cancel {{ background: #6c757d; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⏰ Votre essai gratuit se termine bientôt</h1>
            </div>
            
            <div class="content">
                <h2>Bonjour {user_name},</h2>
                
                <div class="countdown">
                    <h2 style="color: #dc3545; margin: 0;">Plus que {days_remaining} jour{'s' if days_remaining > 1 else ''} !</h2>
                    <p>Votre essai gratuit {plan_name} se termine le {trial_end_date.strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
                
                <p>Nous espérons que vous appréciez votre expérience avec ECOMSIMPLY {plan_name} ! 🚀</p>
                
                <h3>🎯 Ce qui se passe ensuite :</h3>
                <ul>
                    <li>✅ <strong>Si vous ne faites rien :</strong> Votre abonnement {plan_name} continuera automatiquement à {price}/mois</li>
                    <li>❌ <strong>Si vous souhaitez annuler :</strong> Cliquez sur le bouton "Annuler" ci-dessous (aucun prélèvement ne sera effectué)</li>
                </ul>
                
                <h3>💡 Pourquoi continuer avec {plan_name} ?</h3>
                <ul>
                    <li>🖼️ Images IA haute qualité illimitées</li>
                    <li>📊 Analytics avancés pour optimiser vos ventes</li>
                    <li>🔧 Support prioritaire et réactif</li>
                    <li>📈 Nouvelles fonctionnalités en avant-première</li>
                    <li>💰 ROI prouvé : nos clients augmentent leurs ventes de 40% en moyenne</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://ecomsimply.com/dashboard" class="button">✨ Continuer avec {plan_name}</a>
                    <a href="https://ecomsimply.com/cancel-trial" class="button button-cancel">❌ Annuler mon essai</a>
                </div>
                
                <p><strong>Questions ?</strong> Contactez-nous à <a href="mailto:contact@ecomsimply.com">contact@ecomsimply.com</a> - nous sommes là pour vous aider ! 💬</p>
                
                <p>Merci de faire confiance à ECOMSIMPLY ! 🙏</p>
                
                <p>L'équipe ECOMSIMPLY</p>
            </div>
            
            <div class="footer">
                <p>© 2025 ECOMSIMPLY - Votre assistant IA pour l'e-commerce</p>
                <p>Pour vous désabonner ou gérer vos préférences email, <a href="https://ecomsimply.com/unsubscribe">cliquez ici</a></p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_trial_expired_email(self, user_email: str, user_name: str, plan_type: str, subscription_activated: bool) -> bool:
        """Send email when trial expires"""
        
        plan_name = "Premium"
        price = "99€"
        
        if subscription_activated:
            subject = f"✅ Votre abonnement {plan_name} est maintenant actif - ECOMSIMPLY"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                    .button {{ display: inline-block; background: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎉 Bienvenue dans {plan_name} !</h1>
                </div>
                
                <div class="content">
                    <h2>Bonjour {user_name},</h2>
                    
                    <div class="success">
                        <h3>✅ Votre abonnement {plan_name} est maintenant actif !</h3>
                        <p>Le prélèvement de {price} a été effectué avec succès. Vous continuez à bénéficier de toutes les fonctionnalités {plan_name}.</p>
                    </div>
                    
                    <p>Merci de faire confiance à ECOMSIMPLY ! Nous sommes ravis de continuer cette aventure avec vous. 🚀</p>
                    
                    <h3>🎯 Vos avantages {plan_name} :</h3>
                    <ul>
                        <li>🖼️ Génération d'images IA illimitée</li>
                        <li>📊 Analytics avancés et insights</li>
                        <li>🔧 Support prioritaire 24/7</li>
                        <li>📈 Nouvelles fonctionnalités en avant-première</li>
                        <li>💼 Outils professionnels complets</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="https://ecomsimply.com/dashboard" class="button">🏠 Accéder au Tableau de Bord</a>
                    </div>
                    
                    <p>Des questions ? Contactez-nous à <a href="mailto:contact@ecomsimply.com">contact@ecomsimply.com</a></p>
                    
                    <p>Excellent continuation ! 💪</p>
                    
                    <p>L'équipe ECOMSIMPLY</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 ECOMSIMPLY - Votre assistant IA pour l'e-commerce</p>
                    <p>Facture et gestion de l'abonnement : <a href="https://ecomsimply.com/billing">Mon Compte</a></p>
                </div>
            </body>
            </html>
            """
        else:
            subject = f"😢 Votre essai {plan_name} s'est terminé - ECOMSIMPLY"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .info {{ background: #e2e3e5; border-left: 4px solid #6c757d; padding: 15px; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>😢 Votre essai gratuit s'est terminé</h1>
                </div>
                
                <div class="content">
                    <h2>Bonjour {user_name},</h2>
                    
                    <p>Votre essai gratuit {plan_name} de 3 jours s'est terminé. Nous espérons que vous avez apprécié découvrir toutes nos fonctionnalités ! 💙</p>
                    
                    <div class="info">
                        <p>Votre compte continue avec l'accès Premium complet. Vous pouvez utiliser toutes les fonctionnalités premium d'ECOMSIMPLY.</p>
                    </div>
                    
                    <h3>🎯 Envie de continuer l'aventure {plan_name} ?</h3>
                    <p>Réactivez votre abonnement {plan_name} à tout moment pour seulement {price}/mois :</p>
                    
                    <ul>
                        <li>🖼️ Images IA haute qualité illimitées</li>
                        <li>📊 Analytics avancés</li>
                        <li>🔧 Support prioritaire</li>
                        <li>📈 Nouvelles fonctionnalités exclusives</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="https://ecomsimply.com/upgrade" class="button">🚀 Réactiver {plan_name}</a>
                    </div>
                    
                    <p>Merci d'avoir testé ECOMSIMPLY ! Nous restons disponibles pour toute question. 😊</p>
                    
                    <p>L'équipe ECOMSIMPLY</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 ECOMSIMPLY - Votre assistant IA pour l'e-commerce</p>
                </div>
            </body>
            </html>
            """
        
        return self.send_email(user_email, subject, html_content)

# Global email service instance
email_service = EmailService()