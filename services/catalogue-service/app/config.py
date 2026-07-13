from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://catalogue-db:27017"
    mongo_db_name: str = "catalogue"

    # Shared with users-service so this service can validate JWTs without a network hop.
    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"

    service_name: str = "catalogue-service"


settings = Settings()
