#!/usr/bin/env python3
"""
MOCK PUBLISHERS SERVICE - DISABLED FOR PRODUCTION
This service is disabled in production for security reasons.
"""

import logging

logger = logging.getLogger(__name__)

class MockPublisher:
    """
    Mock publisher service - DISABLED in production
    """
    def __init__(self, *args, **kwargs):
        logger.warning("🔒 PRODUCTION: Mock publisher service is disabled")
        
    def publish(self, *args, **kwargs):
        """Mock publishing disabled in production"""
        logger.error("🔒 PRODUCTION ERROR: Mock publisher service called - disabled for security")
        raise Exception("Mock services are disabled in production environment")
        
    def update(self, *args, **kwargs):
        """Mock update disabled in production"""
        logger.error("🔒 PRODUCTION ERROR: Mock publisher service called - disabled for security")
        raise Exception("Mock services are disabled in production environment")
        
    def delete(self, *args, **kwargs):
        """Mock delete disabled in production"""
        logger.error("🔒 PRODUCTION ERROR: Mock publisher service called - disabled for security")
        raise Exception("Mock services are disabled in production environment")