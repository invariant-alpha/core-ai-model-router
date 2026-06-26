import pytest
import respx
import httpx
from core_ai_model_router.config import AIModelRouterConfig
from core_ai_model_router.schemas import AIRequest
from core_ai_model_router.router import AIRouter

@pytest.fixture
def mock_config():
    return AIModelRouterConfig(
        openrouter_api_key="test_key",
        default_text_model="test-model"
    )

@pytest.mark.asyncio
@respx.mock
async def test_process_text(mock_config):
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Hello world!"}}]
        })
    )
    
    router = AIRouter(mock_config)
    req = AIRequest(
        modality="text",
        prompt="Say hello",
        correlation_id="corr_123"
    )
    
    resp = await router.process_request(req)
    
    assert resp.modality == "text"
    assert resp.content == "Hello world!"
    assert resp.model_used == "test-model"
    assert resp.cost_usd == 0.001

@pytest.mark.asyncio
async def test_process_image(mock_config):
    router = AIRouter(mock_config)
    req = AIRequest(
        modality="image",
        prompt="Draw a cat",
        correlation_id="corr_456"
    )
    
    resp = await router.process_request(req)
    
    assert resp.modality == "image"
    assert resp.asset_base64 is not None
    assert resp.model_used == "stable-diffusion-xl"
