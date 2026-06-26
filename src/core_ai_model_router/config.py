from pydantic import BaseModel, Field

class AIModelRouterConfig(BaseModel):
    openrouter_api_key: str = Field(default="", description="Key di OpenRouter")
    novita_api_key: str = Field(default="", description="Key di Novita.ai")
    default_text_model: str = Field(default="anthropic/claude-3-sonnet", description="Default per text")
    default_image_model: str = Field(default="stable-diffusion-xl", description="Default per image")
    max_retries: int = Field(default=3, description="Numero di tentativi massimi")
