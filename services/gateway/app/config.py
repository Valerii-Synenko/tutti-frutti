from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    users_service_url: str = "http://users-service:8000"
    catalogue_service_url: str = "http://catalogue-service:8000"
    orders_service_url: str = "http://orders-service:8000"
    assistant_service_url: str = "http://fruit-assistant-service:8000"
    inventory_grpc_target: str = "inventory-service:50051"

    service_name: str = "gateway"

    # Comma-separated list of origins allowed to call the gateway from a browser.
    # Defaults cover the UI's Vite preview (4173) and dev (5173) servers.
    cors_origins: str = "http://localhost:3001,http://localhost:4173,http://localhost:5173"


settings = Settings()
