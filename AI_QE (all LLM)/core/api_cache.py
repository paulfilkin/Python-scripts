"""
API credential validation cache.
Avoids repeated validation of known-good API keys.
"""

from pathlib import Path
import json
import hashlib
from datetime import datetime, timedelta


class APICredentialCache:
    """Cache successful API credential validations."""
    
    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path.home() / '.cache' / 'really_smart_review'
        
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / 'validated_keys.json'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load validation cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save validation cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def _hash_key(self, api_key: str) -> str:
        """Create hash of API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def is_validated(self, api_key: str, model: str, validity_days: int = 7) -> bool:
        """Check if API key was recently validated successfully."""
        key_hash = self._hash_key(api_key)
        
        if key_hash not in self.cache:
            return False
        
        entry = self.cache[key_hash]
        
        # Check if validation is still valid
        validated_at = datetime.fromisoformat(entry['validated_at'])
        if datetime.now() - validated_at > timedelta(days=validity_days):
            return False
        
        # Check if model matches
        if entry.get('model') != model:
            return False
        
        return True
    
    def mark_validated(self, api_key: str, model: str):
        """Mark API key as successfully validated."""
        key_hash = self._hash_key(api_key)
        
        self.cache[key_hash] = {
            'validated_at': datetime.now().isoformat(),
            'model': model
        }
        
        self._save_cache()
    
    def invalidate(self, api_key: str):
        """Remove API key from cache (e.g., after auth failure)."""
        key_hash = self._hash_key(api_key)
        if key_hash in self.cache:
            del self.cache[key_hash]
            self._save_cache()