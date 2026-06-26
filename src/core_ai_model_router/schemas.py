from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class AIRequest(BaseModel):
    modality: Literal["text", "image", "audio", "video"]
    model_preference: Literal["fast", "smart", "cheap"] = "smart"
    model_override: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    output_schema: Optional[Dict[str, Any]] = None
    parameters: dict = {}
    correlation_id: str

class AIResponse(BaseModel):
    modality: str
    content: Optional[str] = None
    asset_base64: Optional[str] = None
    parsed_output: Optional[dict] = None
    model_used: str
    provider_used: str
    cost_usd: float
    correlation_id: str
