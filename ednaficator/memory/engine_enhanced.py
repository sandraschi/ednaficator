"""
Enhanced Memory Engine for Ednaficator

Provides persistent storage and retrieval of conversation context, user preferences,
and workflow templates with integration to basic-memory MCP server.
"""

import asyncio
import json
import logging
import aiofiles
import aiofiles.os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, asdict
from loguru import logger

# Define types for better type checking
JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

@dataclass
class Interaction:
    """Represents a single user interaction with the system."""
    timestamp: str
    user_input: str
    response: str
    intent: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    success: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        """Create from dictionary."""
        return cls(**data)


class MemoryEngine:
    """
    Enhanced memory system for Ednaficator with MCP integration.
    
    Features:
    - Asynchronous file operations
    - Basic-memory MCP integration
    - Conversation history with semantic search
    - User preference learning
    - Workflow template management
    - Austrian service knowledge base
    """
    
    def __init__(self, memory_path: Union[str, Path], mcp_endpoint: str = None):
        """
        Initialize the memory engine.
        
        Args:
            memory_path: Directory path for storing memory files
            mcp_endpoint: Optional URL for basic-memory MCP server
        """
        self.memory_path = Path(memory_path)
        self.mcp_endpoint = mcp_endpoint
        self._initialized = False
        
        # Memory stores
        self.conversations: List[Interaction] = []
        self.user_preferences: Dict[str, Any] = {}
        self.workflow_templates: Dict[str, List[Dict[str, Any]]] = {}
        self.austrian_knowledge: Dict[str, Dict[str, Any]] = {}
        
        # Default values
        self._default_preferences = {
            "language": "german_austrian",
            "timezone": "Europe/Vienna",
            "currency": "EUR",
            "date_format": "%d.%m.%Y",
            "time_format": "%H:%M",
            "temperature_unit": "celsius",
            "location": "Vienna, Austria",
            "preferred_name": "",
            "notifications_enabled": True,
            "privacy_level": "medium"
        }
        
        # Ensure memory path exists
        self.memory_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize the memory system and load existing data."""
        if self._initialized:
            return
            
        logger.info("Initializing Memory Engine...")
        
        # Load data from disk
        await asyncio.gather(
            self._load_conversations(),
            self._load_user_preferences(),
            self._load_workflow_templates(),
            self._load_austrian_knowledge()
        )
        
        # Initialize MCP connection if configured
        if self.mcp_endpoint:
            await self._initialize_mcp_connection()
        
        self._initialized = True
        logger.info(f"Memory Engine initialized with {len(self.conversations)} conversations")
    
    async def _initialize_mcp_connection(self) -> None:
        """Initialize connection to basic-memory MCP server."""
        # TODO: Implement MCP client initialization
        logger.info(f"Initializing MCP connection to {self.mcp_endpoint}")
        # This would be implemented to connect to the MCP server
    
    # File Operations
    async def _load_json_file(self, filename: str, default: Any = None) -> Any:
        """Load data from a JSON file with error handling."""
        file_path = self.memory_path / filename
        
        if not await aiofiles.os.path.exists(file_path):
            return default if default is not None else {}
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading {filename}: {e}")
            return default if default is not None else {}
    
    async def _save_json_file(self, filename: str, data: Any) -> bool:
        """Save data to a JSON file with error handling."""
        file_path = self.memory_path / filename
        
        try:
            # Create a temporary file first
            temp_path = file_path.with_suffix('.tmp')
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Atomic rename on success
            await aiofiles.os.replace(temp_path, file_path)
            return True
            
        except (OSError, TypeError) as e:
            logger.error(f"Error saving {filename}: {e}")
            # Clean up temp file if it exists
            if await aiofiles.os.path.exists(temp_path):
                await aiofiles.os.remove(temp_path)
            return False
    
    # Data Loading Methods
    async def _load_conversations(self) -> None:
        """Load conversation history from disk."""
        data = await self._load_json_file("conversations.json", [])
        self.conversations = [
            Interaction.from_dict(item) if isinstance(item, dict) else item
            for item in data
        ]
        logger.info(f"Loaded {len(self.conversations)} conversations")
    
    async def _load_user_preferences(self) -> None:
        """Load user preferences from disk."""
        self.user_preferences = {
            **self._default_preferences,
            **await self._load_json_file("user_preferences.json", {})
        }
        logger.info("Loaded user preferences")
    
    async def _load_workflow_templates(self) -> None:
        """Load workflow templates from disk."""
        default_workflows = {
            "vacation_mode": [
                {"server": "homecontrol-mcp", "action": "vacation_mode", "params": {}},
                {"server": "basic-memory", "action": "store_note", "params": {"note": "Vacation started"}},
                {"server": "wien-services-mcp", "action": "hold_mail", "params": {}}
            ],
            "morning_routine": [
                {"server": "homecontrol-mcp", "action": "morning_scene", "params": {}},
                {"server": "weather-mcp", "action": "get_forecast", "params": {"location": "Vienna"}},
                {"server": "calendar-mcp", "action": "get_schedule", "params": {"range": "today"}}
            ]
        }
        
        self.workflow_templates = {
            **default_workflows,
            **await self._load_json_file("workflow_templates.json", {})
        }
        logger.info(f"Loaded {len(self.workflow_templates)} workflow templates")
    
    async def _load_austrian_knowledge(self) -> None:
        """Load Austrian-specific knowledge base."""
        default_knowledge = {
            "government_services": {
                "wien.gv.at": "Vienna city services",
                "help.gv.at": "Austrian government portal",
                "finanzonline.bmf.gv.at": "Tax services"
            },
            "transport": {
                "wienerlinien.at": "Vienna public transport",
                "oebb.at": "Austrian railways",
                "oebb.at/en": "ÖBB (English)",
                "scotty.vor.at": "Journey planner",
                "wienmobil.at": "Vienna mobility"
            },
            "shopping": {
                "geizhals.at": "Price comparison",
                "willhaben.at": "Marketplace",
                "billa.at": "Supermarket",
                "spar.at": "Supermarket",
                "hofer.at": "Discount supermarket"
            },
            "emergency": {
                "police": "133",
                "fire": "122",
                "ambulance": "144",
                "european_emergency": "112",
                "poison_control": "+43 1 406 43 43",
                "crisis_help": "142 (Telefonseelsorge)"
            },
            "utilities": {
                "wienenergie.at": "Energy provider",
                "wien.gv.at/ma48": "Waste management",
                "wienerwohnen.at": "Public housing",
                "wien.gv.at/verkehr/verwaltung/parken.html": "Parking information"
            },
            "healthcare": {
                "gesundheit.gv.at": "Health portal",
                "krankenkassen.at": "Health insurance",
                "apotheken-umschau.de/notdienstsuche/": "Emergency pharmacy finder"
            },
            "public_transport": {
                "oebb.at": "Austrian Federal Railways",
                "wienerlinien.at": "Vienna public transport",
                "westbahn.at": "Westbahn train service",
                "flughafen-wien.at": "Vienna International Airport",
                "wien.gv.at/verkehr/linien": "Vienna public transport lines"
            },
            "tourism": {
                "wien.info": "Vienna tourist information",
                "austria.info": "Austria tourist information",
                "schoenbrunn.at": "Schönbrunn Palace",
                "khm.at": "Kunsthistorisches Museum",
                "belvedere.at": "Belvedere Museum"
            },
            "education": {
                "univie.ac.at": "University of Vienna",
                "tuwien.at": "Vienna University of Technology",
                "wu.ac.at": "Vienna University of Economics and Business",
                "akbild.ac.at": "Academy of Fine Arts Vienna",
                "mdw.ac.at": "University of Music and Performing Arts Vienna"
            },
            "culture": {
                "wien.gv.at/stadtleben/kultur.html": "Vienna cultural events",
                "volkstheater.at": "Volkstheater Vienna",
                "burgtheater.at": "Burgtheater",
                "staatsoper.at": "Vienna State Opera",
                "musikverein.at": "Wiener Musikverein"
            },
            "sports": {
                "skrapid.at": "SK Rapid Wien",
                "fk-austria.at": "FK Austria Wien",
                "generali-arena.at": "Generali Arena (football)",
                "erstebank-open.com": "Erste Bank Open (tennis)",
                "vienna.org/sport/": "Vienna sports information"
            }
        }
        
        self.austrian_knowledge = {
            **default_knowledge,
            **await self._load_json_file("austrian_knowledge.json", {})
        }
        logger.info("Loaded Austrian knowledge base")
    
    # Public API Methods
    async def store_interaction(
        self,
        user_input: str,
        response: str,
        intent: Dict[str, Any],
        actions_taken: List[Dict[str, Any]] = None,
        success: bool = True,
        metadata: Dict[str, Any] = None
    ) -> Interaction:
        """
        Store a conversation interaction for learning and context.
        
        Args:
            user_input: The user's input text
            response: The system's response
            intent: The parsed intent from NLP
            actions_taken: List of actions taken to generate the response
            success: Whether the interaction was successful
            metadata: Additional metadata about the interaction
            
        Returns:
            The stored Interaction object
        """
        if not self._initialized:
            await self.initialize()
        
        interaction = Interaction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_input=user_input,
            response=response,
            intent=intent,
            actions_taken=actions_taken or [],
            success=success,
            metadata=metadata or {}
        )
        
        self.conversations.append(interaction)
        
        # Keep conversation history manageable
        max_history = self.user_preferences.get("max_conversation_history", 1000)
        if len(self.conversations) > max_history:
            self.conversations = self.conversations[-max_history:]
        
        # Save to disk asynchronously
        asyncio.create_task(self._save_conversations())
        
        # Learn from the interaction
        asyncio.create_task(self._learn_from_interaction(interaction))
        
        return interaction
    
    async def get_context(
        self,
        current_input: str = None,
        lookback: int = 5,
        include_workflows: bool = True,
        include_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Get relevant context for the current interaction.
        
        Args:
            current_input: The current user input for context
            lookback: Number of recent interactions to include
            include_workflows: Whether to include relevant workflows
            include_knowledge: Whether to include relevant knowledge
            
        Returns:
            Dictionary containing relevant context
        """
        if not self._initialized:
            await self.initialize()
        
        context = {
            "user_preferences": self.user_preferences.copy(),
            "recent_interactions": [
                i.to_dict() for i in self.conversations[-lookback:]
            ] if self.conversations else [],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "relevant_workflows": [],
            "austrian_knowledge": {}
        }
        
        # Add relevant workflows if requested and input is provided
        if include_workflows and current_input:
            context["relevant_workflows"] = await self._find_relevant_workflows(current_input)
        
        # Add relevant knowledge if requested and input is provided
        if include_knowledge and current_input:
            context["austrian_knowledge"] = await self._find_relevant_knowledge(current_input)
        
        return context
    
    async def update_user_preference(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Update a user preference.
        
        Args:
            key: Preference key
            value: New value for the preference
            save: Whether to save to disk immediately
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        self.user_preferences[key] = value
        
        if save:
            return await self._save_user_preferences()
        return True
    
    async def get_workflow_template(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get a workflow template by name.
        
        Args:
            name: Name of the workflow template
            
        Returns:
            The workflow template or None if not found
        """
        if not self._initialized:
            await self.initialize()
            
        return self.workflow_templates.get(name)
    
    async def save_workflow_template(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        overwrite: bool = False
    ) -> bool:
        """
        Save a workflow template.
        
        Args:
            name: Name of the workflow
            steps: List of steps in the workflow
            overwrite: Whether to overwrite if exists
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        if name in self.workflow_templates and not overwrite:
            logger.warning(f"Workflow '{name}' already exists and overwrite=False")
            return False
        
        self.workflow_templates[name] = steps
        return await self._save_workflow_templates()
    
    # Helper Methods
    async def _find_relevant_workflows(self, text: str) -> List[Dict[str, Any]]:
        """Find workflows relevant to the given text."""
        text_lower = text.lower()
        relevant = []
        
        for name, steps in self.workflow_templates.items():
            if any(word in text_lower for word in name.split('_')):
                relevant.append({"name": name, "steps": steps})
        
        return relevant
    
    async def _find_relevant_knowledge(self, text: str) -> Dict[str, Any]:
        """Find knowledge relevant to the given text."""
        text_lower = text.lower()
        relevant = {}
        
        for category, items in self.austrian_knowledge.items():
            if any(word in text_lower for word in category.split('_')):
                relevant[category] = items
                continue
                
            # Check items within the category
            relevant_items = {
                k: v for k, v in items.items()
                if any(word in text_lower for word in k.split())
            }
            
            if relevant_items:
                relevant[category] = relevant_items
        
        return relevant
    
    async def _learn_from_interaction(self, interaction: Interaction) -> None:
        """Learn from a successful interaction."""
        if not interaction.success:
            return
        
        user_input = interaction.user_input.lower()
        updated = False
        
        # Learn time preferences
        if any(word in user_input for word in ["morgen", "morgens", "morning"]):
            time_str = datetime.now(timezone.utc).strftime("%H:%M")
            if self.user_preferences.get("morning_routine_time") != time_str:
                self.user_preferences["morning_routine_time"] = time_str
                updated = True
        
        # Learn language preferences
        if any(word in user_input for word in ["bitte", "danke", "grüß", "servus"]):
            if self.user_preferences.get("language") != "german_austrian":
                self.user_preferences["language"] = "german_austrian"
                updated = True
        
        # Learn location preferences
        vienna_terms = ["wien", "vienna", "wiener", "österreich", "austria"]
        if any(term in user_input for term in vienna_terms):
            if self.user_preferences.get("location") != "Vienna, Austria":
                self.user_preferences["location"] = "Vienna, Austria"
                updated = True
        
        # Save if preferences were updated
        if updated:
            await self._save_user_preferences()
    
    # Save Methods
    async def _save_conversations(self) -> bool:
        """Save conversations to disk."""
        data = [i.to_dict() if hasattr(i, 'to_dict') else i 
               for i in self.conversations]
        return await self._save_json_file("conversations.json", data)
    
    async def _save_user_preferences(self) -> bool:
        """Save user preferences to disk."""
        return await self._save_json_file("user_preferences.json", self.user_preferences)
    
    async def _save_workflow_templates(self) -> bool:
        """Save workflow templates to disk."""
        return await self._save_json_file("workflow_templates.json", self.workflow_templates)
    
    async def _save_austrian_knowledge(self) -> bool:
        """Save Austrian knowledge to disk."""
        return await self._save_json_file("austrian_knowledge.json", self.austrian_knowledge)
