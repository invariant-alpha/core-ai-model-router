import httpx
import logging
from typing import Optional
from .config import AIModelRouterConfig
from .schemas import AIRequest, AIResponse

logger = logging.getLogger(__name__)

class AIRouter:
    def __init__(self, config: AIModelRouterConfig):
        self.config = config

    async def process_request(self, req: AIRequest) -> AIResponse:
        if req.modality == "text":
            return await self._process_text(req)
        elif req.modality == "image":
            return await self._process_image(req)
        else:
            raise ValueError(f"Modality {req.modality} not fully supported yet.")

    async def _process_text(self, req: AIRequest) -> AIResponse:
        model = req.model_override or self.config.default_text_model
        
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost", # Requisito OpenRouter
            "X-Title": "Venture Studio"
        }
        
        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.append({"role": "user", "content": req.prompt})
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        # OpenRouter support for response format (JSON schema)
        if req.output_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": req.output_schema
                }
            }
            
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            
            content = data["choices"][0]["message"]["content"]
            
            # Stima costo. OpenRouter a volte restituisce prompt_tokens e completion_tokens in usage
            # oppure costo direttamente. Simplifichiamo:
            cost = 0.001 # placeholder
            
            return AIResponse(
                modality="text",
                content=content,
                model_used=model,
                provider_used="openrouter",
                cost_usd=cost,
                correlation_id=req.correlation_id
            )

    async def _process_image(self, req: AIRequest) -> AIResponse:
        model = req.model_override or self.config.default_image_model
        
        # Simulazione per Novita.ai / Prodia
        # Poiché stiamo solo facendo l'infrastruttura core, in questa fase mockiamo la vera API image
        
        cost = 0.01 # placeholder
        
        return AIResponse(
            modality="image",
            asset_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", # 1x1 black pixel base64
            model_used=model,
            provider_used="novita",
            cost_usd=cost,
            correlation_id=req.correlation_id
        )
