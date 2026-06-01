"""
Standalone tests for the enhanced memory engine.
This version doesn't depend on other project modules.
"""

import asyncio
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

# Import the memory engine directly without importing the rest of the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ednaficator.memory.engine_enhanced import MemoryEngine, Interaction

# Test data
TEST_DATA_DIR = Path(__file__).parent / "test_data"
MEMORY_PATH = TEST_DATA_DIR / "memory"

# Sample test data
SAMPLE_INTERACTION = {
    "timestamp": "2025-08-10T10:30:00+02:00",
    "user_input": "Wie ist das Wetter in Wien?",
    "response": "Das Wetter in Wien ist sonnig bei 25°C.",
    "intent": {
        "category": "weather",
        "action": "query",
        "target": "current",
        "params": {"location": "Wien"},
        "confidence": 0.95
    },
    "actions_taken": [
        {"service": "weather", "action": "get_current", "params": {"location": "Wien"}}
    ],
    "success": True,
    "metadata": {"source": "test"}
}

# Fixtures
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Set up test environment before each test and clean up after."""
    # Create test directory
    MEMORY_PATH.mkdir(parents=True, exist_ok=True)
    
    yield  # This is where the test runs
    
    # Clean up after test
    if MEMORY_PATH.exists():
        shutil.rmtree(MEMORY_PATH)

@pytest.fixture
async def memory_engine():
    """Create a memory engine instance for testing."""
    engine = MemoryEngine(memory_path=MEMORY_PATH)
    await engine.initialize()
    return engine

# Helper functions
async def create_sample_memory_files():
    """Create sample memory files for testing."""
    # Create sample conversations
    conversations = [
        {
            "timestamp": "2025-08-09T10:00:00+02:00",
            "user_input": "Schalte das Licht an",
            "response": "Ich habe das Licht eingeschaltet.",
            "intent": {"category": "home", "action": "control_light", "state": "on"},
            "actions_taken": [{"device": "light", "action": "turn_on"}],
            "success": True,
            "metadata": {}
        },
        {
            "timestamp": "2025-08-09T10:05:00+02:00",
            "user_input": "Wie wird das Wetter?",
            "response": "Es wird heute sonnig mit 25°C.",
            "intent": {"category": "weather", "action": "query_forecast"},
            "actions_taken": [{"service": "weather", "action": "get_forecast"}],
            "success": True,
            "metadata": {}
        }
    ]
    
    # Create sample preferences
    preferences = {
        "language": "german_austrian",
        "timezone": "Europe/Vienna",
        "temperature_unit": "celsius",
        "morning_routine_time": "07:30"
    }
    
    # Write files
    (MEMORY_PATH / "conversations.json").write_text(json.dumps(conversations, ensure_ascii=False))
    (MEMORY_PATH / "user_preferences.json").write_text(json.dumps(preferences, ensure_ascii=False))
    
    # Create empty files for other data
    (MEMORY_PATH / "workflow_templates.json").write_text("{}")
    (MEMORY_PATH / "austrian_knowledge.json").write_text("{}")

# Tests
class TestMemoryEngineInitialization:
    """Tests for MemoryEngine initialization and setup."""
    
    async def test_initialization_creates_directory(self):
        """Test that initialization creates the memory directory if it doesn't exist."""
        # Ensure directory doesn't exist
        if MEMORY_PATH.exists():
            shutil.rmtree(MEMORY_PATH)
            
        engine = MemoryEngine(memory_path=MEMORY_PATH)
        await engine.initialize()
        
        assert MEMORY_PATH.exists()
        assert MEMORY_PATH.is_dir()
    
    async def test_initialization_loads_existing_data(self):
        """Test that initialization loads existing data from files."""
        await create_sample_memory_files()
        
        engine = MemoryEngine(memory_path=MEMORY_PATH)
        await engine.initialize()
        
        # Check conversations were loaded
        assert len(engine.conversations) == 2
        assert engine.conversations[0].user_input == "Schalte das Licht an"
        
        # Check preferences were loaded
        assert engine.user_preferences["language"] == "german_austrian"
        assert engine.user_preferences["morning_routine_time"] == "07:30"
    
    async def test_initialization_with_defaults(self):
        """Test initialization with default values when no data exists."""
        engine = MemoryEngine(memory_path=MEMORY_PATH)
        await engine.initialize()
        
        # Check default preferences
        assert engine.user_preferences["language"] == "german_austrian"
        assert engine.user_preferences["timezone"] == "Europe/Vienna"
        
        # Check empty collections
        assert engine.conversations == []
        assert engine.workflow_templates != {}
        assert engine.austrian_knowledge != {}


class TestInteractionHandling:
    """Tests for storing and retrieving interactions."""
    
    async def test_store_interaction(self, memory_engine):
        """Test storing a new interaction."""
        interaction = await memory_engine.store_interaction(
            user_input="Wie ist das Wetter?",
            response="Es ist sonnig.",
            intent={"category": "weather", "action": "query"},
            actions_taken=[{"service": "weather", "action": "get_current"}]
        )
        
        assert isinstance(interaction, Interaction)
        assert interaction.user_input == "Wie ist das Wetter?"
        assert interaction.response == "Es ist sonnig."
        assert interaction.intent["category"] == "weather"
        assert interaction.success is True
        
        # Check it was added to memory
        assert len(memory_engine.conversations) == 1
        assert memory_engine.conversations[0] == interaction
    
    async def test_store_interaction_with_metadata(self, memory_engine):
        """Test storing an interaction with metadata."""
        metadata = {"source": "test", "confidence": 0.95}
        interaction = await memory_engine.store_interaction(
            user_input="Test",
            response="Test response",
            intent={"category": "test"},
            actions_taken=[],
            metadata=metadata
        )
        
        assert interaction.metadata == metadata
    
    async def test_interaction_history_limited(self, memory_engine):
        """Test that interaction history is limited to max size."""
        # Set a small max history for testing
        memory_engine.user_preferences["max_conversation_history"] = 2
        
        # Add 3 interactions
        for i in range(3):
            await memory_engine.store_interaction(
                user_input=f"Test {i}",
                response=f"Response {i}",
                intent={"category": "test"},
                actions_taken=[]
            )
        
        # Should only keep the 2 most recent
        assert len(memory_engine.conversations) == 2
        assert memory_engine.conversations[0].user_input == "Test 1"
        assert memory_engine.conversations[1].user_input == "Test 2"


class TestContextRetrieval:
    """Tests for retrieving context from memory."""
    
    async def test_get_context_with_no_history(self, memory_engine):
        """Test getting context with no conversation history."""
        context = await memory_engine.get_context()
        
        assert isinstance(context, dict)
        assert "user_preferences" in context
        assert "recent_interactions" in context
        assert len(context["recent_interactions"]) == 0
    
    async def test_get_context_with_history(self, memory_engine):
        """Test getting context with conversation history."""
        # Add some test interactions
        for i in range(3):
            await memory_engine.store_interaction(
                user_input=f"Test {i}",
                response=f"Response {i}",
                intent={"category": "test"},
                actions_taken=[]
            )
        
        context = await memory_engine.get_context(lookback=2)
        
        assert len(context["recent_interactions"]) == 2
        assert context["recent_interactions"][0]["user_input"] == "Test 1"
        assert context["recent_interactions"][1]["user_input"] == "Test 2"
    
    async def test_get_context_with_workflows(self, memory_engine):
        """Test getting context with relevant workflows."""
        # Add a workflow
        await memory_engine.save_workflow_template(
            "morning_routine",
            [{"action": "wake_up"}, {"action": "read_news"}]
        )
        
        # Get context with workflow matching
        context = await memory_engine.get_context(
            current_input="Was ist meine Morgenroutine?",
            include_workflows=True
        )
        
        assert "relevant_workflows" in context
        assert len(context["relevant_workflows"]) > 0
        assert context["relevant_workflows"][0]["name"] == "morning_routine"


class TestPreferenceHandling:
    """Tests for user preference management."""
    
    async def test_update_preference(self, memory_engine):
        """Test updating a user preference."""
        # Initial value
        assert memory_engine.user_preferences.get("temperature_unit") == "celsius"
        
        # Update preference
        result = await memory_engine.update_user_preference("temperature_unit", "fahrenheit")
        
        # Check in-memory update
        assert result is True
        assert memory_engine.user_preferences["temperature_unit"] == "fahrenheit"
        
        # Verify file was updated
        with open(MEMORY_PATH / "user_preferences.json", 'r', encoding='utf-8') as f:
            saved_prefs = json.load(f)
            assert saved_prefs["temperature_unit"] == "fahrenheit"
    
    async def test_learn_from_interaction(self, memory_engine):
        """Test that the system learns from interactions."""
        # Initial value
        memory_engine.user_preferences["morning_routine_time"] = "07:00"
        
        # Create an interaction that should trigger learning
        interaction = Interaction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_input="Guten Morgen! Es ist 08:15 Uhr.",
            response="Guten Morgen! Ich aktualisiere Ihre Morgenroutine.",
            intent={"category": "greeting", "action": "morning_greeting"},
            actions_taken=[],
            success=True,
            metadata={}
        )
        
        # Trigger learning
        await memory_engine._learn_from_interaction(interaction)
        
        # Check if preference was updated
        assert memory_engine.user_preferences["morning_routine_time"] == "08:15"


class TestWorkflowManagement:
    """Tests for workflow template management."""
    
    async def test_save_and_retrieve_workflow(self, memory_engine):
        """Test saving and retrieving a workflow template."""
        # Save a workflow
        workflow_steps = [
            {"action": "wake_up", "time": "07:00"},
            {"action": "read_news", "source": "derstandard.at"},
            {"action": "check_calendar"}
        ]
        
        result = await memory_engine.save_workflow_template(
            "my_morning_routine",
            workflow_steps
        )
        
        assert result is True
        
        # Retrieve the workflow
        retrieved = await memory_engine.get_workflow_template("my_morning_routine")
        assert retrieved == workflow_steps
        
        # Check non-existent workflow
        assert await memory_engine.get_workflow_template("non_existent") is None
    
    async def test_find_relevant_workflows(self, memory_engine):
        """Test finding relevant workflows based on input text."""
        # Add some workflows
        await memory_engine.save_workflow_template("morning_routine", [{"action": "wake_up"}])
        await memory_engine.save_workflow_template("evening_routine", [{"action": "sleep"}])
        await memory_engine.save_workflow_template("vacation_checklist", [{"action": "pack_bags"}])
        
        # Find relevant workflows
        relevant = await memory_engine._find_relevant_workflows("Was ist meine Morgenroutine?")
        assert len(relevant) == 1
        assert relevant[0]["name"] == "morning_routine"
        
        # Test with different input
        relevant = await memory_engine._find_relevant_workflows("Zeig mir meine Routinen")
        assert len(relevant) == 2  # Should match both routines
        
        # Test with no matches
        relevant = await memory_engine._find_relevant_workflows("Wie ist das Wetter?")
        assert len(relevant) == 0


class TestAustrianKnowledge:
    """Tests for Austrian knowledge base functionality."""
    
    async def test_find_relevant_knowledge(self, memory_engine):
        """Test finding relevant Austrian knowledge."""
        # Add some knowledge
        memory_engine.austrian_knowledge["transport"] = {
            "oebb.at": "Austrian Railways",
            "wienerlinien.at": "Vienna Public Transport"
        }
        memory_engine.austrian_knowledge["shopping"] = {
            "geizhals.at": "Price comparison"
        }
        
        # Find relevant knowledge
        relevant = await memory_engine._find_relevant_knowledge("Wann fährt der nächste Zug?")
        assert "transport" in relevant
        assert "oebb.at" in relevant["transport"]
        assert "shopping" not in relevant  # Shouldn't match shopping
        
        # Test with different input
        relevant = await memory_engine._find_relevant_knowledge("Wo finde ich Preisvergleiche?")
        assert "shopping" in relevant
        assert "transport" not in relevant
        
        # Test with no matches
        relevant = await memory_engine._find_relevant_knowledge("Dies ist ein Test")
        assert relevant == {}


class TestPersistence:
    """Tests for data persistence."""
    
    async def test_conversation_persistence(self, memory_engine):
        """Test that conversations are persisted between instances."""
        # Add a conversation
        await memory_engine.store_interaction(
            user_input="Test",
            response="Test response",
            intent={"category": "test"},
            actions_taken=[]
        )
        
        # Create a new instance
        new_engine = MemoryEngine(memory_path=MEMORY_PATH)
        await new_engine.initialize()
        
        # Check the conversation was loaded
        assert len(new_engine.conversations) == 1
        assert new_engine.conversations[0].user_input == "Test"
    
    async def test_preference_persistence(self, memory_engine):
        """Test that preferences are persisted between instances."""
        # Update a preference
        await memory_engine.update_user_preference("temperature_unit", "fahrenheit")
        
        # Create a new instance
        new_engine = MemoryEngine(memory_path=MEMORY_PATH)
        await new_engine.initialize()
        
        # Check the preference was loaded
        assert new_engine.user_preferences["temperature_unit"] == "fahrenheit"


# Run tests
if __name__ == "__main__":
    pytest.main(["-v", "test_memory_engine_standalone.py"])
