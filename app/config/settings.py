from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    API_V1_STR: str = "/api/v1"

    QDRANT_COLLECTION_NAME: str
    QDRANT_EMBEDDING_DIM: int
    QDRANT_HOST: str
    QDRANT_PORT: int

    EMBEDDING_MODEL_DENSE: str
    EMBEDDING_MODEL_SPARSE: str

    RERANKER_MODEL: str
    RERANKER_TOP_K: int

    RETRIEVER_TOP_K: int

    OLLAMA_MODEL: str
    OLLAMA_EVAL_MODEL: str
    OLLAMA_TEMPERATURE: float
    OLLAMA_MAX_CONTEXT: int
    OLLAMA_MAX_TOKENS: int
    OLLAMA_API_HOST: str
    OLLAMA_API_PORT: int

    @computed_field
    @property
    def QDRANT_URL(self) -> str:
        return f"{self.QDRANT_HOST}:{self.QDRANT_PORT}/"

    @computed_field
    @property
    def OLLAMA_API_URL(self) -> str:
        return f"{self.OLLAMA_API_HOST}:{self.OLLAMA_API_PORT}/"

    model_config = SettingsConfigDict(case_sensitive=True)


settings: Settings = Settings()
