"""
Enhanced NLP Processor for Ednaficator

Handles Austrian German language understanding with local LLM integration.
"""

import re
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import aiohttp
import aiofiles
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Intent:
    """Structured representation of user intent."""
    category: str  # e.g., "weather", "home_control", "transport"
    action: str    # e.g., "get", "set", "search"
    target: str    # e.g., "temperature", "light", "train_schedule"
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_input: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Intent':
        """Create from dictionary."""
        return cls(**data)

class NLPProcessor:
    """Natural Language Processing for Austrian German with local LLM integration."""
    
    def __init__(self, local_llm_endpoint: str = "http://localhost:11434/api/generate"):
        self.local_llm_endpoint = local_llm_endpoint
        self.patterns = self._load_patterns()
        self.austrian_terms = self._load_austrian_terms()
    
    async def parse_intent(self, text: str) -> Intent:
        """Parse user input and extract intent with entities."""
        # Normalize input
        normalized = self._normalize_input(text)
        
        # Try pattern matching first
        intent = self._pattern_match(normalized)
        
        # Fall back to LLM if confidence is low
        if intent.confidence < 0.7:
            intent = await self._llm_parse(normalized)
        
        return intent
    
    def _normalize_input(self, text: str) -> str:
        """Normalize input text."""
        text = text.lower().strip()
        # Replace Austrian terms with standard German
        for term, replacement in self.austrian_terms.items():
            text = text.replace(term, replacement)
        return text
    
    def _pattern_match(self, text: str) -> Intent:
        """Match patterns against input text."""
        for intent_name, intent_data in self.patterns.items():
            for pattern in intent_data["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    entities = self._extract_entities(text, intent_data.get("entities", {}))
                    return Intent(
                        **intent_data["intent"],
                        entities=entities,
                        confidence=0.8,  # High confidence for pattern matches
                        raw_input=text
                    )
        return Intent("general", "unknown", "", {}, 0.3, text)
    
    async def _llm_parse(self, text: str) -> Intent:
        """Use LLM for intent parsing."""
        prompt = {
            "model": "llama2",
            "prompt": f"""
            Analyze this Austrian German input and extract intent:
            Input: {text}
            
            Respond with JSON: {{
                "category": "intent_category",
                "action": "action_type",
                "target": "target_entity",
                "entities": {{"key": "value"}},
                "confidence": 0.0
            }}"""
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.local_llm_endpoint,
                    json=prompt,
                    timeout=5.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        intent_data = json.loads(result.get("response", "{}"))
                        return Intent(**intent_data, raw_input=text)
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
        
        return Intent("general", "unknown", "", {}, 0.3, text)
    
    def _extract_entities(self, text: str, entity_patterns: Dict) -> Dict[str, str]:
        """Extract entities using regex patterns."""
        entities = {}
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                if match := re.search(pattern, text, re.IGNORECASE):
                    entities[entity_type] = match.group(1) if match.groups() else match.group(0)
        return entities
    
    def _load_patterns(self) -> Dict:
        """Load intent patterns."""
        return {
            "greeting": {
                "patterns": [r"hallo", r"servus", r"grü[ßs] di", r"grü[ßs] gott"],
                "intent": {"category": "greeting", "action": "greet", "target": "user"}
            },
            "weather": {
                "patterns": [r"wie.*wetter", r"regne?n", r"sonnig", r"temperatur"],
                "entities": {
                    "location": [r"in\s+(\w+)"],
                    "time": [r"morgen", r"übermorgen"]
                },
                "intent": {"category": "weather", "action": "get", "target": "weather"}
            },
            "transport": {
                "patterns": [r"wann\s+kommt", r"öbb", r"u[-\.]?bahn"],
                "entities": {
                    "transport_type": [r"(u[-\.]?bahn|stra[ßs]enbahn|bus|zug|öbb)"],
                    "direction": [r"(?:nach|in|richtung)\s+([A-Z][a-zäöüß\s-]+)"]
                },
                "intent": {"category": "transport", "action": "get", "target": "schedule"}
            }
        }
    
    def _load_austrian_terms(self) -> Dict[str, str]:
        """Load Austrian German terms."""
        return {
            "servus": "hallo",
            "grüß di": "hallo",
            "grüß gott": "guten tag",
            "paradiser": "tomate",
            "erdapfel": "kartoffel",
            "fisolen": "grüne bohnen"
        }
