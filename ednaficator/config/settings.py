"""
Configuration Management for Ednaficator

Handles loading and managing configuration from files,
environment variables, and Austrian-specific settings.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from multiple sources
    
    Priority order:
    1. Custom config file (if provided)
    2. Environment variables
    3. Default config
    """
    
    # Start with default configuration
    config = get_default_config()
    
    # Load from config file if provided
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)
            config.update(file_config)
    
    # Override with environment variables
    env_config = load_from_environment()
    config.update(env_config)
    
    return config


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for Ednaficator"""
    return {
        # Core settings
        "debug": False,
        "log_level": "INFO",
        "timezone": "Europe/Vienna",
        "language": "de-AT",
        
        # Memory settings
        "memory_path": "./edna_memory",
        "max_conversation_history": 1000,
        "auto_save_interval": 300,  # 5 minutes
        
        # MCP settings
        "mcp_discovery_timeout": 10,
        "mcp_call_timeout": 30,
        "mcp_retry_attempts": 3,
        
        # Local LLM settings
        "local_llm_endpoint": "http://localhost:11434",  # Ollama default
        "local_llm_model": "llama3.1:8b",
        "local_llm_temperature": 0.7,
        "local_llm_max_tokens": 2048,
        
        # Austrian services
        "austrian_services": {
            "wien_gov_api": None,  # Requires registration
            "oebb_api_key": None,  # Requires registration  
            "geizhals_scraping": True,
            "finanz_online_integration": False
        },
        
        # Privacy settings
        "data_retention_days": 365,
        "export_conversations": True,
        "anonymize_logs": True,
        "local_processing_only": True,
        
        # Home automation
        "homecontrol": {
            "default_security_mode": "away",
            "vacation_mode_enhancements": True,
            "ai_analysis_enabled": True
        },
        
        # Notification preferences
        "notifications": {
            "enabled": True,
            "channels": ["console", "log"],  # Could add "email", "sms"
            "quiet_hours": {
                "start": "22:00",
                "end": "07:00"
            }
        },
        
        # Development settings
        "development": {
            "mock_mcp_servers": False,
            "debug_workflows": False,
            "log_all_interactions": True
        }
    }


def load_from_environment() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    env_config = {}
    
    # Core settings
    if "EDNA_DEBUG" in os.environ:
        env_config["debug"] = os.environ["EDNA_DEBUG"].lower() == "true"
    
    if "EDNA_LOG_LEVEL" in os.environ:
        env_config["log_level"] = os.environ["EDNA_LOG_LEVEL"]
    
    if "EDNA_MEMORY_PATH" in os.environ:
        env_config["memory_path"] = os.environ["EDNA_MEMORY_PATH"]
    
    # Local LLM settings
    if "EDNA_LLM_ENDPOINT" in os.environ:
        env_config["local_llm_endpoint"] = os.environ["EDNA_LLM_ENDPOINT"]
    
    if "EDNA_LLM_MODEL" in os.environ:
        env_config["local_llm_model"] = os.environ["EDNA_LLM_MODEL"]
    
    # Austrian services API keys
    austrian_services = {}
    if "WIEN_GOV_API_KEY" in os.environ:
        austrian_services["wien_gov_api"] = os.environ["WIEN_GOV_API_KEY"]
    
    if "OEBB_API_KEY" in os.environ:
        austrian_services["oebb_api_key"] = os.environ["OEBB_API_KEY"]
    
    if austrian_services:
        env_config["austrian_services"] = austrian_services
    
    return env_config


def create_default_config_file(path: str):
    """Create a default configuration file"""
    config = get_default_config()
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"✅ Created default config file: {path}")


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration settings"""
    required_keys = ["memory_path", "local_llm_endpoint"]
    
    for key in required_keys:
        if key not in config:
            print(f"❌ Missing required config key: {key}")
            return False
    
    # Validate paths exist or can be created
    memory_path = Path(config["memory_path"])
    try:
        memory_path.mkdir(exist_ok=True, parents=True)
    except Exception as e:
        print(f"❌ Cannot create memory path {memory_path}: {e}")
        return False
    
    # Validate local LLM endpoint format
    llm_endpoint = config["local_llm_endpoint"]
    if not (llm_endpoint.startswith("http://") or llm_endpoint.startswith("https://")):
        print(f"❌ Invalid LLM endpoint format: {llm_endpoint}")
        return False
    
    print("✅ Configuration validation passed")
    return True


# Austrian-specific configuration helpers
class AustrianConfig:
    """Austrian-specific configuration utilities"""
    
    @staticmethod
    def get_vienna_districts() -> Dict[int, str]:
        """Get Vienna district mapping"""
        return {
            1: "Innere Stadt", 2: "Leopoldstadt", 3: "Landstraße",
            4: "Wieden", 5: "Margareten", 6: "Mariahilf",
            7: "Neubau", 8: "Josefstadt", 9: "Alsergrund",
            10: "Favoriten", 11: "Simmering", 12: "Meidling",
            13: "Hietzing", 14: "Penzing", 15: "Rudolfsheim-Fünfhaus",
            16: "Ottakring", 17: "Hernals", 18: "Währing",
            19: "Döbling", 20: "Brigittenau", 21: "Floridsdorf",
            22: "Donaustadt", 23: "Liesing"
        }
    
    @staticmethod
    def get_austrian_states() -> Dict[str, str]:
        """Get Austrian state mapping"""
        return {
            "Wien": "Vienna",
            "Niederösterreich": "Lower Austria", 
            "Oberösterreich": "Upper Austria",
            "Salzburg": "Salzburg",
            "Tirol": "Tyrol",
            "Vorarlberg": "Vorarlberg",
            "Kärnten": "Carinthia",
            "Steiermark": "Styria",
            "Burgenland": "Burgenland"
        }
    
    @staticmethod
    def get_emergency_numbers() -> Dict[str, str]:
        """Get Austrian emergency numbers"""
        return {
            "police": "133",
            "fire": "122",
            "ambulance": "144", 
            "emergency": "112",
            "gas_emergency": "128",
            "poison_control": "+43 1 406 43 43"
        }
