#!/usr/bin/env python3
"""
Amazon SP-API Integration Demo Script - Bloc 1
This script demonstrates the Amazon SP-API integration functionality
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend path for imports
sys.path.append('/app/backend')

from services.amazon_connection_service import AmazonConnectionService
from models.amazon_spapi import SPAPIRegion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AmazonIntegrationDemo:
    """Demo class for Amazon SP-API integration"""
    
    def __init__(self):
        self.connection_service = None
        self.demo_user_id = f"demo-user-{int(datetime.utcnow().timestamp())}"
        
    async def setup(self):
        """Setup demo environment"""
        logger.info("🚀 Setting up Amazon SP-API integration demo...")
        
        # Setup database connection
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/ecomsimply')
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database()
        
        # Initialize connection service
        self.connection_service = AmazonConnectionService(db)
        logger.info("✅ Demo environment ready")
    
    async def demo_connection_creation(self):
        """Demonstrate connection creation process"""
        logger.info("📋 Demo: Creating Amazon connection...")
        
        try:
            # Create connection for France marketplace
            connection_result = await self.connection_service.create_connection(
                user_id=self.demo_user_id,
                marketplace_id='A13V1IB3VIYZZH',  # Amazon France
                region=SPAPIRegion.EU
            )
            
            logger.info("✅ Connection created successfully!")
            logger.info(f"   Connection ID: {connection_result['connection_id']}")
            logger.info(f"   OAuth State: {connection_result['state'][:20]}...")
            logger.info(f"   Authorization URL: {connection_result['authorization_url'][:60]}...")
            logger.info(f"   Expires At: {connection_result['expires_at']}")
            
            return connection_result['connection_id']
            
        except Exception as e:
            logger.error(f"❌ Connection creation failed: {e}")
            return None
    
    async def demo_user_connections_list(self):
        """Demonstrate listing user connections"""
        logger.info("📋 Demo: Listing user connections...")
        
        try:
            connections = await self.connection_service.get_user_connections(self.demo_user_id)
            
            logger.info(f"✅ Found {len(connections)} connections for user")
            
            for i, conn in enumerate(connections, 1):
                logger.info(f"   Connection {i}:")
                logger.info(f"     ID: {conn.connection_id}")
                logger.info(f"     Status: {conn.status}")
                logger.info(f"     Marketplace: {conn.marketplace_id}")
                logger.info(f"     Region: {conn.region}")
                if conn.seller_id:
                    logger.info(f"     Seller ID: {conn.seller_id}")
                if conn.error_message:
                    logger.info(f"     Error: {conn.error_message}")
            
            return connections
            
        except Exception as e:
            logger.error(f"❌ Failed to list connections: {e}")
            return []
    
    async def demo_oauth_state_cleanup(self):
        """Demonstrate OAuth state cleanup"""
        logger.info("🧹 Demo: OAuth state cleanup...")
        
        try:
            cleaned_count = await self.connection_service.cleanup_expired_states()
            logger.info(f"✅ Cleaned up {cleaned_count} expired OAuth states")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    async def demo_health_check(self):
        """Demonstrate health check functionality"""
        logger.info("💚 Demo: Health check...")
        
        try:
            health_data = await self.connection_service.health_check_connections()
            
            logger.info("✅ Health check completed:")
            logger.info(f"   Total Connections: {health_data.get('total_connections', 0)}")
            logger.info(f"   KMS Access: {'✅' if health_data.get('kms_access', False) else '❌'}")
            
            if 'status_breakdown' in health_data:
                logger.info("   Status Breakdown:")
                for status, count in health_data['status_breakdown'].items():
                    logger.info(f"     {status}: {count}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    async def demo_connection_disconnect(self, connection_id: str):
        """Demonstrate connection disconnection"""
        logger.info(f"🔌 Demo: Disconnecting connection {connection_id}...")
        
        try:
            success = await self.connection_service.disconnect_connection(
                connection_id=connection_id,
                user_id=self.demo_user_id
            )
            
            if success:
                logger.info("✅ Connection disconnected successfully")
            else:
                logger.warning("⚠️ Connection not found or already disconnected")
            
        except Exception as e:
            logger.error(f"❌ Disconnection failed: {e}")
    
    async def run_complete_demo(self):
        """Run complete demonstration"""
        logger.info("🎬 Starting Amazon SP-API Integration Demo")
        logger.info("="*60)
        
        await self.setup()
        
        # Demo 1: Health check
        await self.demo_health_check()
        print()
        
        # Demo 2: Create connection
        connection_id = await self.demo_connection_creation()
        print()
        
        # Demo 3: List connections
        connections = await self.demo_user_connections_list()
        print()
        
        # Demo 4: OAuth cleanup
        await self.demo_oauth_state_cleanup()
        print()
        
        # Demo 5: Disconnect connection (if created)
        if connection_id:
            await self.demo_connection_disconnect(connection_id)
            print()
        
        # Final health check
        await self.demo_health_check()
        
        logger.info("="*60)
        logger.info("🎉 Amazon SP-API Integration Demo completed!")
        
        # Show next steps
        logger.info("\n📚 Next Steps:")
        logger.info("1. Access the integration UI at /integrations/amazon")
        logger.info("2. Click 'Se connecter à Amazon' to start OAuth flow")
        logger.info("3. Complete authorization with your Amazon seller account")
        logger.info("4. Use the connection for product publishing")

async def main():
    """Main demo function"""
    demo = AmazonIntegrationDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())