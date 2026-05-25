import logging
from ...router import LLMRouter
from ...memory import HybridMemory

logger = logging.getLogger(__name__)

class ECCHooks:
    """Handlers for ECC-native agent events."""
    def __init__(self, user_id: str, project_id: str):
        self.memory = HybridMemory(user_id, project_id)

    async def on_session_start(self, query: str):
        """Automatically called by ECC SessionStart hook."""
        logger.info(f"ECC Session Start: Recalling context for '{query}'")
        recall_data = await self.memory.recall(query=query)
        return recall_data

    async def on_session_stop(self, last_interaction: str):
        """Automatically called by ECC Stop hook."""
        logger.info("ECC Session Stop: Saving interaction to persistent memory.")
        await self.memory.add_memory(last_interaction)
