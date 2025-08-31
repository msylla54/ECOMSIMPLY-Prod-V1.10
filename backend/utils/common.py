"""
ECOMSIMPLY Utilities Module
Common utility functions used throughout the application
"""

import re
import json
import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId, json_util
import logging

logger = logging.getLogger("ecomsimply.utils")

class JSONEncoder:
    """Custom JSON encoder for MongoDB ObjectIds and other types"""
    
    @staticmethod
    def convert_objectid_to_str(obj: Any) -> Any:
        """Convert MongoDB ObjectIds to strings recursively"""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: JSONEncoder.convert_objectid_to_str(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [JSONEncoder.convert_objectid_to_str(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    @staticmethod
    def serialize_for_json(obj: Any) -> str:
        """Serialize object to JSON string with ObjectId support"""
        converted = JSONEncoder.convert_objectid_to_str(obj)
        return json.dumps(converted, default=str, ensure_ascii=False)

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:250] + ('.' + ext if ext else '')
        return sanitized
    
    @staticmethod
    def validate_price(price: Union[str, float, int]) -> tuple[bool, float]:
        """Validate and convert price"""
        try:
            price_float = float(price)
            if price_float < 0:
                return False, 0.0
            return True, round(price_float, 2)
        except (ValueError, TypeError):
            return False, 0.0
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, List[str]]:
        """Validate that required fields are present and not empty"""
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                missing_fields.append(field)
        return len(missing_fields) == 0, missing_fields

class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length with suffix"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if word not in stop_words]
        # Return unique keywords, limited by max_keywords
        return list(dict.fromkeys(keywords))[:max_keywords]

class DateUtils:
    """Date and time utilities"""
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string"""
        return dt.strftime(format_str)
    
    @staticmethod
    def get_age_in_days(dt: datetime) -> int:
        """Get age of datetime in days"""
        return (datetime.utcnow() - dt).days
    
    @staticmethod
    def is_recent(dt: datetime, days: int = 7) -> bool:
        """Check if datetime is within recent days"""
        return DateUtils.get_age_in_days(dt) <= days

class FileUtils:
    """File handling utilities"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    @staticmethod
    def is_allowed_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """Check if file type is allowed"""
        extension = FileUtils.get_file_extension(filename)
        return extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        name, ext = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
        unique_id = str(uuid.uuid4())[:8]
        sanitized_name = ValidationUtils.sanitize_filename(name)
        return f"{sanitized_name}_{unique_id}.{ext}" if ext else f"{sanitized_name}_{unique_id}"

class HashUtils:
    """Hashing utilities"""
    
    @staticmethod
    def generate_hash(data: str, algorithm: str = 'sha256') -> str:
        """Generate hash of data"""
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Generate short unique ID"""
        return str(uuid.uuid4()).replace('-', '')[:length]
    
    @staticmethod
    def generate_affiliate_code(length: int = 8) -> str:
        """Generate affiliate code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class ResponseUtils:
    """API response utilities"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Create success response"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error_response(message: str, error_code: str = "ERROR", details: Any = None) -> Dict[str, Any]:
        """Create error response"""
        response = {
            "success": False,
            "error": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details is not None:
            response["details"] = details
        return response
    
    @staticmethod
    def paginated_response(data: List[Any], total: int, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Create paginated response"""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit  # Ceiling division
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Convenience functions
def convert_objectid_to_str(obj: Any) -> Any:
    """Convert ObjectIds to strings"""
    return JSONEncoder.convert_objectid_to_str(obj)

def serialize_for_json(obj: Any) -> str:
    """Serialize object to JSON"""
    return JSONEncoder.serialize_for_json(obj)

def is_valid_email(email: str) -> bool:
    """Validate email"""
    return ValidationUtils.is_valid_email(email)

def generate_unique_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())