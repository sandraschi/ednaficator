"""
Natural Language Processing for Ednaficator

Handles intent recognition, Austrian German processing,
and local LLM integration for privacy-first AI.
"""

import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass  
class Intent:
    """Parsed user intent"""
    category: str  # home, media, austrian_services, general
    action: str    # specific action to take
    target: str    # target of the action
    params: Dict   # parameters for the action
    workflow: Optional[str] = None  # predefined workflow name
    confidence: float = 0.0


class NLPProcessor:
    """
    Natural language processing for Austrian German
    
    Handles:
    - Intent recognition from user input
    - Austrian German language patterns
    - Local LLM integration
    - Privacy-first processing (no cloud)
    """
    
    def __init__(self, local_llm_endpoint: str):
        """
        Initialize the NLP processor with a local LLM endpoint.
        
        Args:
            local_llm_endpoint: Base URL for the local LLM API (e.g., http://localhost:11434)
        """
        self.local_llm_endpoint = local_llm_endpoint
        self.intent_patterns = self._load_intent_patterns()
        self.austrian_phrases = self._load_austrian_phrases()
        logger.info("NLP processor initialized")
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns"""
        return {
            # Home automation
            "home_security": [
                r"(sicher|secure|alarm|einbruch)",
                r"(haus|home|zuhause).*?(sicher|secure)",
                r"vacation.*mode",
                r"urlaub.*modus"
            ],
            "home_control": [
                r"(licht|light|beleuchtung)",
                r"(heizung|heating|temperatur)",
                r"(jalousien|blinds|rollläden)"
            ],
            
            # Media management
            "media_search": [
                r"(such|find|finde).*?(musik|music|film|movie|buch|book)",
                r"(spiel|play).*?(musik|music|playlist)",
                r"(zeig|show).*?(filme|movies|bücher|books)"
            ],
            
            # Austrian services
            "austrian_gov": [
                r"(wien|vienna).*?(service|dienst)",
                r"(parkschein|parking|permit)",
                r"(steuer|tax|finanz)",
                r"(öbb|bahn|train|zug)"
            ],
            
            # Shopping
            "shopping": [
                r"(preis|price|kosten|cost)",
                r"(kauf|buy|bestell|order)",
                r"(geizhals|preisvergleich)",
                r"(günstig|cheap|billig)"
            ],
            
            # Workflows
            "vacation_workflow": [
                r"urlaub.*modus",
                r"vacation.*mode", 
                r"(gehe|going).*urlaub",
                r"verreise"
            ],
            "morning_workflow": [
                r"guten.*morgen",
                r"morning.*routine",
                r"morgen.*ablauf"
            ]
        }
    
    def _load_austrian_phrases(self) -> Dict[str, str]:
        """Load Austrian German phrases and their meanings"""
        return {
            # Greetings
            "grüß gott": "hallo",
            "servus": "hallo/tschüss",
            "baba": "tschüss",
            "pfiat di": "auf wiedersehen",
            
            # Politeness
            "bitte schön": "bitte",
            "danke schön": "danke",
            "vergelt's gott": "danke",
            
            # Common expressions
            "passt scho": "ist in ordnung",
            "eh klar": "natürlich",
            "ur leiwand": "sehr gut",
            "ur": "sehr",
            "leiwand": "gut/toll",
            
            # Austrian specific
            "sackerl": "tüte",
            "erdäpfel": "kartoffeln", 
            "paradeiser": "tomaten",
            "topfen": "quark",
            "obers": "sahne"
        }
    
    async def parse_intent(self, user_input: str) -> Intent:
        """
        Parse user input and extract intent
        
        Args:
            user_input: Natural language input from user
            
        Returns:
            Intent object with parsed information
        """
        if not user_input or not user_input.strip():
            logger.warning("Empty user input received")
            return Intent(
                category="general",
                action="respond",
                target="empty_input",
                params={"error": "empty_input"},
                confidence=0.0
            )
            
        try:
            # Normalize input
            normalized = self._normalize_austrian_input(user_input)
            logger.debug(f"Normalized input: {normalized}")
            
            # Try pattern matching first (fast)
            intent = self._pattern_match_intent(normalized)
            
            # If pattern matching has low confidence, use local LLM (slower but more accurate)
            if intent.confidence < 0.7:
                logger.debug("Low confidence in pattern matching, trying LLM")
                intent = await self._llm_parse_intent(normalized)
            
            logger.info(f"Parsed intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error parsing intent: {e}", exc_info=True)
            return Intent(
                category="error",
                action="error_handling",
                target="intent_parsing",
                params={"error": str(e), "input": user_input},
                confidence=0.0
            )
    
    def _normalize_austrian_input(self, text: str) -> str:
        """
        Normalize Austrian German input to standard German
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
            
        text = text.lower().strip()
        
        # Replace Austrian phrases with standard German
        for austrian, standard in self.austrian_phrases.items():
            text = text.replace(austrian, standard)
        
        # Common Austrian spellings
        text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        text = text.replace("ß", "ss")
        
        return text
    
    def _pattern_match_intent(self, text: str) -> Intent:
        """
        Fast pattern-based intent recognition
        
        Args:
            text: Normalized input text
            
        Returns:
            Intent object with parsed information
        """
        # Check vacation workflow
        for pattern in self.intent_patterns["vacation_workflow"]:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent(
                    category="workflow",
                    action="execute_workflow",
                    target="vacation", 
                    params={"workflow": "vacation_mode"},
                    workflow="vacation_mode",
                    confidence=0.9
                )
        
        # Check morning workflow
        for pattern in self.intent_patterns["morning_workflow"]:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent(
                    category="workflow",
                    action="execute_workflow",
                    target="morning",
                    params={"workflow": "morning_routine"},
                    workflow="morning_routine", 
                    confidence=0.9
                )
        
        # Check home security
        for pattern in self.intent_patterns["home_security"]:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent(
                    category="home",
                    action="secure_home",
                    target="security_system",
                    params={"action": "secure"},
                    confidence=0.8
                )
        
        # Check media search
        for pattern in self.intent_patterns["media_search"]:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract what they're searching for
                target = "unknown"
                if "musik" in text or "music" in text:
                    target = "music"
                elif "film" in text or "movie" in text:
                    target = "movie"
                elif "buch" in text or "book" in text:
                    target = "book"
                
                return Intent(
                    category="media",
                    action="search",
                    target=target,
                    params={"query": text},
                    confidence=0.8
                )
        
        # Check Austrian services
        for pattern in self.intent_patterns["austrian_gov"]:
            if re.search(pattern, text, re.IGNORECASE):
                service_type = "general"
                if "park" in text:
                    service_type = "parking"
                elif "steuer" in text or "tax" in text:
                    service_type = "tax"
                elif "öbb" in text or "bahn" in text:
                    service_type = "transport"
                
                return Intent(
                    category="austrian_services",
                    action="help_with_service",
                    target=service_type,
                    params={"service_type": service_type, "query": text},
                    confidence=0.8
                )
        
        # Check shopping
        for pattern in self.intent_patterns["shopping"]:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent(
                    category="shopping",
                    action="price_check",
                    target="product",
                    params={"query": text},
                    confidence=0.7
                )
        
        # Default fallback
        return Intent(
            category="general",
            action="respond",
            target="conversation",
            params={"query": text},
            confidence=0.3
        )
    
    async def _llm_parse_intent(self, text: str) -> Intent:
        """
        Use local LLM for more sophisticated intent parsing
        
        Args:
            text: Normalized input text
            
        Returns:
            Parsed Intent object with extracted information
            
        Note:
            Falls back to pattern matching if LLM is unavailable
        """
        import httpx
        
        # Default fallback intent if LLM fails
        fallback_intent = self._pattern_match_intent(text)
        fallback_intent.confidence = max(0.1, fallback_intent.confidence - 0.1)  # Reduce confidence for fallback
        
        # Prepare the prompt for the LLM
        prompt = {
            "model": "llama2",  # Default model, can be configured
            "prompt": f"""
            Analyze the following user input and extract the intent in JSON format.
            Categories: home_control, media, austrian_services, shopping, general
            Actions: get, set, search, control, query
            
            Input: {text}
            
            Respond with a JSON object containing:
            - category: The main intent category
            - action: What the user wants to do
            - target: The target of the action
            - params: Key-value pairs of parameters
            - confidence: 0.0 to 1.0
            - workflow: Optional workflow name if applicable
            
            Example:
            {{
                "category": "home_control",
                "action": "set",
                "target": "light",
                "params": {{"state": "on", "location": "living room"}},
                "confidence": 0.9,
                "workflow": null
            }}
            """,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug(f"Sending request to LLM: {self.local_llm_endpoint}/api/generate")
                response = await client.post(
                    f"{self.local_llm_endpoint}/api/generate",
                    json=prompt,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract the JSON from the LLM response
                try:
                    # Handle Ollama's response format
                    if 'response' in result:
                        content = result['response'].strip()
                        # Clean up the response (might contain markdown code blocks)
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0].strip()
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0].strip()
                        
                        # Parse the JSON response
                        intent_data = json.loads(content)
                        
                        # Create and return the Intent object
                        return Intent(
                            category=intent_data.get('category', 'general'),
                            action=intent_data.get('action', 'unknown'),
                            target=intent_data.get('target', ''),
                            params=intent_data.get('params', {}),
                            workflow=intent_data.get('workflow'),
                            confidence=float(intent_data.get('confidence', 0.5))
                        )
                    else:
                        logger.warning(f"Unexpected LLM response format: {result}")
                        return fallback_intent
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(f"Failed to parse LLM response: {e}")
                    logger.debug(f"LLM raw response: {result}")
                    return fallback_intent
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            return fallback_intent
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"LLM request failed: {e}")
            return fallback_intent
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM parsing: {e}", exc_info=True)
            return fallback_intent
    
    async def generate_response_text(self, intent: Intent, results: List[Dict] = None) -> str:
        """
        Generate natural language response from intent and results
        
        Args:
            intent: Parsed intent
            results: Optional results from action execution
            
        Returns:
            Natural language response string
        """
        if results is None:
            results = []
            
        # Error handling
        if intent.category == "error":
            return "Entschuldigung, da ist etwas schiefgelaufen. Bitte versuche es später noch einmal."
        
        # Home automation responses
        if intent.category == "home":
            if intent.action == "secure_home":
                return "Alles klar! Das Haus ist jetzt gesichert. Alle Türen sind versperrt und die Kameras sind aktiv."
            return "Ich habe die Heimautomatisierung für dich gesteuert."
        
        # Media responses
        elif intent.category == "media":
            if results:
                return f"Ich habe {len(results)} Ergebnisse für dich gefunden!"
            return "Leider habe ich nichts Passendes gefunden."
        
        # Austrian services responses
        elif intent.category == "austrian_services":
            if intent.target == "transport":
                return "Hier sind die aktuellen Verbindungen der ÖBB:"
            elif intent.target == "parking":
                return "Hier sind Informationen zu Parkmöglichkeiten in Wien:"
            return "Gerne helfe ich dir mit den österreichischen Services!"
        
        # Workflow responses
        elif intent.category == "workflow" and intent.workflow:
            return f"Der {intent.workflow} wurde erfolgreich ausgeführt!"
        
        # Shopping responses
        elif intent.category == "shopping":
            if results:
                return f"Ich habe {len(results)} Produkte für dich gefunden!"
            return "Ich konnte leider keine passenden Produkte finden."
        
        # Default response
        return "Verstehe! Ich kümmere mich darum."
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text (times, locations, names, etc.)
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            Dictionary of entity types and their values
        """
        entities = {}
        
        # Time extraction
        time_patterns = [
            (r"(\d{1,2}):(\d{2})", "time"),  # 14:30
            (r"(\d{1,2})\s*(uhr|h)", "time"),  # 14 Uhr
            (r"(morgen|mittag|abend|nacht)", "time_of_day")  # morning, noon, evening, night
        ]
        
        for pattern, entity_type in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0] if matches else matches
        
        # Vienna districts
        vienna_districts = [
            "innere stadt", "leopoldstadt", "landstraße", "wieden",
            "margareten", "mariahilf", "neubau", "josefstadt", 
            "alsergrund", "favoriten"
        ]
        
        for district in vienna_districts:
            if district in text.lower():
                entities["vienna_district"] = district
                break
        
        return entities
