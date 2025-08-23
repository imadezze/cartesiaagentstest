import asyncio
import os
from typing import AsyncGenerator

from loguru import logger

from line import (
    Bridge,
    CallRequest,
    ConversationContext,
    ReasoningNode,
    VoiceAgentApp,
    VoiceAgentSystem,
)
from line.events import AgentResponse, EndCall, UserStoppedSpeaking, UserTranscriptionReceived

# Set the log level to INFO
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


class CounterNode(ReasoningNode):
    def __init__(self, node_id: str):
        """
        Initialize the Counter node.

        Args:
            node_id: The ID of the node.
        """
        super().__init__(
            node_id=node_id,
            system_prompt="",
        )
        self.current_count = 0
        self.max_count = int(os.environ.get("MAX_COUNT", "100"))
        self.sleep_ms = int(os.environ.get("SLEEP_MS", "0"))
        logger.info(f"CounterNode initialized with max_count={self.max_count}, sleep_ms={self.sleep_ms}")

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | EndCall, None]:
        if self.sleep_ms > 0:
            await asyncio.sleep(self.sleep_ms / 1000.0)

        self.current_count += 1

        if self.current_count >= self.max_count:
            logger.info(f"Counter reached maximum value {self.max_count}, ending call")
            yield AgentResponse(content=f"{self.current_count}. Counter complete!")
            yield EndCall()
        else:
            logger.info(f"Counter at: {self.current_count}")
            yield AgentResponse(content=str(self.current_count))


async def handle_new_call(system: VoiceAgentSystem, call_request: CallRequest):
    """Configure nodes and bridges for counter functionality."""
    logger.info(
        f"Starting counter call for {call_request.call_id} from {call_request.from_} to {call_request.to}"
    )

    node = CounterNode(node_id="counter")
    bridge = Bridge(node)
    system.with_speaking_node(node, bridge)

    bridge.on(UserTranscriptionReceived).map(node.add_event)

    (bridge.on(UserStoppedSpeaking).stream(node.generate).broadcast())

    await system.start()
    await system.send_initial_message("0")
    await system.wait_for_shutdown()


app = VoiceAgentApp(handle_new_call)

if __name__ == "__main__":
    app.run()
