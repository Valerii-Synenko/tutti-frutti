from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    max_response_tokens: int = 500

    catalogue_service_url: str = "http://catalogue-service:8000"

    service_name: str = "fruit-assistant-service"


settings = Settings()
