"""
Configuration Manager
Handles application configuration, API keys, and environment settings
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration and environment settings"""
    
    def __init__(self, env_file: str = ".env"):
        """Initialize configuration manager"""
        self.env_file = env_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and defaults"""
        # Load environment variables from .env file
        load_dotenv(self.env_file)
        
        return {
            # API Configuration
            "api_key": self._get_api_key(),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-pro"),
            "api_timeout": int(os.getenv("API_TIMEOUT", "30")),
            
            # File Paths
            "branches_file": os.getenv("BRANCHES_FILE", "branches.json"),
            "suggestions_file": os.getenv("SUGGESTIONS_FILE", "suggestions.json"),
            "user_data_file": os.getenv("USER_DATA_FILE", "user_data.json"),
            "session_data_file": os.getenv("SESSION_DATA_FILE", "session_data.json"),
            
            # Conversation Settings
            "default_language": os.getenv("DEFAULT_LANGUAGE", "English"),
            "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.6")),
            "interruption_threshold": float(os.getenv("INTERRUPTION_THRESHOLD", "0.4")),
            
            # Debug Settings
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            "verbose_logging": os.getenv("VERBOSE_LOGGING", "false").lower() == "true",
            
            # Session Settings
            "auto_save": os.getenv("AUTO_SAVE", "true").lower() == "true",
            "backup_sessions": os.getenv("BACKUP_SESSIONS", "false").lower() == "true",
            "max_chat_history": int(os.getenv("MAX_CHAT_HISTORY", "100")),
        }
    
    def _get_api_key(self) -> str:
        """Get API key with fallback to hardcoded value"""
        # Try environment variable first
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
        
        # Fallback to hardcoded value for reliability
        # Only load from environment variable, do not use any hardcoded or fallback value
        return os.getenv("GEMINI_API_KEY", "")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get all file paths configuration"""
        return {
            "branches_file": self.get("branches_file"),
            "suggestions_file": self.get("suggestions_file"),
            "user_data_file": self.get("user_data_file"),
            "session_data_file": self.get("session_data_file")
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API-related configuration"""
        return {
            "api_key": self.get("api_key"),
            "model": self.get("gemini_model"),
            "timeout": self.get("api_timeout")
        }
    
    def get_conversation_config(self) -> Dict[str, Any]:
        """Get conversation-related configuration"""
        return {
            "default_language": self.get("default_language"),
            "confidence_threshold": self.get("confidence_threshold"),
            "interruption_threshold": self.get("interruption_threshold"),
            "max_chat_history": self.get("max_chat_history")
        }
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get("debug_mode", False)
    
    def is_verbose_logging(self) -> bool:
        """Check if verbose logging is enabled"""
        return self.get("verbose_logging", False)
    
    def should_auto_save(self) -> bool:
        """Check if auto-save is enabled"""
        return self.get("auto_save", True)
    
    def should_backup_sessions(self) -> bool:
        """Check if session backup is enabled"""
        return self.get("backup_sessions", False)
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        self.config.update(updates)
    
    def reload_config(self) -> None:
        """Reload configuration from environment"""
        self.config = self._load_config()
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self.config.copy()
    
    def validate_config(self) -> Dict[str, str]:
        """Validate configuration and return any issues"""
        issues = {}
        
        # Validate API key
        if not self.get("api_key"):
            issues["api_key"] = "API key is required"
        
        # Validate file paths exist (for read-only files)
        required_files = ["user_data_file"]  # Only validate files that must exist
        for file_key in required_files:
            file_path = self.get(file_key)
            if file_path and not os.path.exists(file_path):
                issues[file_key] = f"Required file {file_path} not found"
        
        # Validate numeric ranges
        if not 0 <= self.get("confidence_threshold", 0.6) <= 1:
            issues["confidence_threshold"] = "Confidence threshold must be between 0 and 1"
        
        if not 0 <= self.get("interruption_threshold", 0.4) <= 1:
            issues["interruption_threshold"] = "Interruption threshold must be between 0 and 1"
        
        if self.get("max_chat_history", 100) < 1:
            issues["max_chat_history"] = "Max chat history must be positive"
        
        return issues
