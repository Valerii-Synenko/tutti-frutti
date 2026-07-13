from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://tuttifrutti:tuttifrutti@orders-db:5432/orders"

    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"

    inventory_grpc_target: str = "inventory-service:50051"

    service_name: str = "orders-service"


settings = Settings()
