from chat import ChatNode
from loguru import logger
from prompts import get_initial_message

from line import Bridge, CallRequest, VoiceAgentApp, VoiceAgentSystem
from line.events import UserStartedSpeaking, UserStoppedSpeaking, UserTranscriptionReceived

# Configure loguru to only log INFO and above
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


async def handle_new_call(system: VoiceAgentSystem, _call_request: CallRequest):
    chat_node = ChatNode()
    chat_bridge = Bridge(chat_node)
    system.with_speaking_node(chat_node, chat_bridge)

    chat_bridge.on(UserTranscriptionReceived).map(chat_node.add_event)

    (
        chat_bridge.on(UserStoppedSpeaking)
        .interrupt_on(UserStartedSpeaking, handler=chat_node.on_interrupt_generate)
        .stream(chat_node.generate)
        .broadcast()
    )

    await system.start()
    initial_message = get_initial_message()
    if initial_message:
        await system.send_initial_message(initial_message)
    await system.wait_for_shutdown()


app = VoiceAgentApp(handle_new_call)

if __name__ == "__main__":
    app.run()
