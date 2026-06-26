import asyncio
import logging
import uuid
from datetime import datetime

try:
    from core_bus.client import RedisBusClient
    from core_bus.schemas import EventEnvelope
except ImportError:
    RedisBusClient = None
    EventEnvelope = None

from .config import AIModelRouterConfig
from .schemas import AIRequest, AIResponse
from .router import AIRouter

logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting core-ai-model-router...")

    config = AIModelRouterConfig()
    router = AIRouter(config)
    
    if not RedisBusClient:
        logger.error("core-bus missing. Running without Bus.")
        return

    bus_client = RedisBusClient()
    await bus_client.connect()

    async def on_ai_requested(envelope: EventEnvelope):
        logger.info(f"Received AI request: {envelope.correlation_id}")
        req = AIRequest.model_validate(envelope.payload)
        
        # Retry loop basic implementation
        retries = 0
        success = False
        response = None
        error_msg = None
        
        while retries < config.max_retries and not success:
            try:
                response = await router.process_request(req)
                success = True
            except Exception as e:
                logger.error(f"Attempt {retries + 1} failed: {e}")
                retries += 1
                error_msg = str(e)
                if retries < config.max_retries:
                    await asyncio.sleep(2 ** retries) # Exponential backoff
        
        if success and response:
            resp_envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="ai.response.completed",
                source_module="core-ai-model-router",
                timestamp=datetime.utcnow(),
                correlation_id=envelope.correlation_id,
                payload=response.model_dump()
            )
            await bus_client.publish("ai.response.completed", resp_envelope)
            
            # Emetti evento di costo per il FinOps Module
            cost_envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="finops.cost.recorded",
                source_module="core-ai-model-router",
                timestamp=datetime.utcnow(),
                correlation_id=envelope.correlation_id,
                payload={"cost_usd": response.cost_usd, "type": "ai_inference"}
            )
            await bus_client.publish("finops.cost.recorded", cost_envelope)
        else:
            fail_envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="ai.response.failed",
                source_module="core-ai-model-router",
                timestamp=datetime.utcnow(),
                correlation_id=envelope.correlation_id,
                payload={"error": error_msg}
            )
            await bus_client.publish("ai.response.failed", fail_envelope)

    await bus_client.subscribe("ai.request.created", "ai_router_group", on_ai_requested)

    logger.info("core-ai-model-router is listening for requests...")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down core-ai-model-router...")
    finally:
        await bus_client.close()

if __name__ == "__main__":
    asyncio.run(main())
