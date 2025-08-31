#!/usr/bin/env python3

"""
Test script to verify Fal.ai image generation functionality
"""

import asyncio
import os
import sys
import base64

# Add the backend directory to Python path
sys.path.append('/app/backend')

from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Test if we can import fal_client
try:
    import fal_client
    print("✅ fal_client imported successfully")
except ImportError:
    print("❌ fal_client not available")
    exit(1)

async def test_fal_image_generation():
    """Test fal.ai image generation directly"""
    
    # Check if FAL_KEY is available
    fal_key = os.environ.get('FAL_KEY')
    if not fal_key:
        print("❌ FAL_KEY not found in environment")
        return False
        
    print(f"✅ FAL_KEY found: {fal_key[:20]}...")
    
    # Set the API key
    os.environ["FAL_KEY"] = fal_key
    
    try:
        # Test product generation
        product_name = "iPhone 15 Pro"
        product_description = "Smartphone premium avec caméra avancée"
        
        prompt = f"Professional product photography of {product_name}. {product_description}. Studio lighting, clean white background, commercial photography, high resolution, product catalog style, marketing material, e-commerce optimized, sharp focus, premium quality, no shadows, centered composition, smartphone, mobile device, technology, sleek design, modern phone, professional product image, commercial quality"
        
        print(f"🖼️ Testing image generation for: {product_name}")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        # Submit request to fal.ai
        handler = await fal_client.submit_async(
            "fal-ai/flux-pro",  # Using Flux Pro for highest quality
            arguments={
                "prompt": prompt,
                "image_size": "landscape_4_3",  # Good for product shots
                "num_inference_steps": 28,      # Higher quality
                "guidance_scale": 3.5,          # Better prompt adherence
                "seed": None,                    # Random for variety
                "enable_safety_checker": True
            }
        )
        
        print("⏳ Waiting for image generation...")
        result = await handler.get()
        
        if result and "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]
            print(f"✅ Image generated successfully: {image_url}")
            
            # Try to download and convert to base64
            import requests
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                print(f"✅ Image downloaded and converted to base64 ({len(image_base64)} chars)")
                
                # Save a small sample to verify format
                sample_b64 = image_base64[:100] + "..." if len(image_base64) > 100 else image_base64
                print(f"📄 Base64 sample: {sample_b64}")
                
                return True
            else:
                print(f"❌ Failed to download image: HTTP {response.status_code}")
                return False
        else:
            print("❌ No images returned from fal.ai")
            print(f"📄 Full result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error during image generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🧪 Starting Fal.ai image generation test")
    print("=" * 50)
    
    success = await test_fal_image_generation()
    
    print("=" * 50)
    if success:
        print("🎉 Image generation test PASSED")
    else:
        print("💥 Image generation test FAILED")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)