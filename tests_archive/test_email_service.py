#!/usr/bin/env python3

"""
Test script for SMTP email service
"""

import asyncio
import sys
sys.path.append('/app/backend')

from modules.email_service import email_service
from datetime import datetime, timedelta

async def test_email_sending():
    """Test SMTP email sending"""
    
    print("🧪 Testing SMTP Email Service with O2switch")
    print("=" * 50)
    
    # Test basic email sending
    print("📧 Testing basic email sending...")
    success = email_service.send_email(
        to_email="contact@ecomsimply.com",  # Send to ourselves for testing
        subject="🧪 Test Email - ECOMSIMPLY SMTP",
        html_content="""
        <html>
        <body>
            <h2>🎉 Test Email Successful!</h2>
            <p>This is a test email from ECOMSIMPLY SMTP service.</p>
            <p>If you receive this, the O2switch SMTP configuration is working correctly!</p>
            <p>Configuration used:</p>
            <ul>
                <li>Server: ecomsimply.com</li>
                <li>Port: 465 (SSL)</li>
                <li>Username: contact@ecomsimply.com</li>
            </ul>
            <p>✅ Email service is operational!</p>
        </body>
        </html>
        """
    )
    
    if success:
        print("✅ Basic email test PASSED")
    else:
        print("❌ Basic email test FAILED")
        return False
    
    # Test trial welcome email
    print("\n📧 Testing trial welcome email...")
    trial_end_date = datetime.now() + timedelta(days=7)
    success = email_service.send_trial_welcome_email(
        user_email="contact@ecomsimply.com",
        user_name="Test User",
        plan_type="pro",
        trial_end_date=trial_end_date
    )
    
    if success:
        print("✅ Trial welcome email test PASSED")
    else:
        print("❌ Trial welcome email test FAILED")
        return False
    
    # Test trial reminder email
    print("\n📧 Testing trial reminder email...")
    success = email_service.send_trial_reminder_email(
        user_email="contact@ecomsimply.com",
        user_name="Test User", 
        plan_type="premium",
        days_remaining=3,
        trial_end_date=trial_end_date
    )
    
    if success:
        print("✅ Trial reminder email test PASSED")
    else:
        print("❌ Trial reminder email test FAILED")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All email tests PASSED!")
    print("📧 Check contact@ecomsimply.com for test emails")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_email_sending())
    exit(0 if result else 1)