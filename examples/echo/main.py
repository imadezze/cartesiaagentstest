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
from line.events import AgentResponse, UserStoppedSpeaking, UserTranscriptionReceived

# Set the log level to INFO
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


class EchoNode(ReasoningNode):
    def __init__(self, node_id: str):
        """
        Initialize the Echo node.

        Args:
            node_id: The ID of the node.
        """
        super().__init__(
            node_id=node_id,
            system_prompt="You are an echo agent that repeats back what users say.",
        )
        self.sleep_ms = int(os.environ.get("SLEEP_MS", "0"))
        logger.info(f"EchoNode initialized with sleep_ms={self.sleep_ms}")

    async def process_context(self, context: ConversationContext) -> AsyncGenerator[AgentResponse, None]:
        if self.sleep_ms > 0:
            await asyncio.sleep(self.sleep_ms / 1000.0)

        latest_user_message = context.get_latest_user_transcript_message()
        echo_content = f"You said: {latest_user_message}"
        logger.info(f"Echoing back: {echo_content}")
        yield AgentResponse(content=echo_content)


async def handle_new_call(system: VoiceAgentSystem, call_request: CallRequest):
    """Configure nodes and bridges for echo functionality."""
    logger.info(
        f"Starting echo call for {call_request.call_id} from {call_request.from_} to {call_request.to}"
    )

    node = EchoNode(node_id="echo")
    bridge = Bridge(node)
    system.with_speaking_node(node, bridge)

    bridge.on(UserTranscriptionReceived).map(node.add_event)

    (bridge.on(UserStoppedSpeaking).stream(node.generate).broadcast())

    await system.start()
    await system.wait_for_shutdown()


app = VoiceAgentApp(handle_new_call)

if __name__ == "__main__":
    app.run()
