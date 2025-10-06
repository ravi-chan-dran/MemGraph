"""Configuration management for the Bedrock-powered Graph + Memory POC."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    bedrock_claude_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_CLAUDE_MODEL_ID")
    bedrock_titan_emb_model_id: str = Field(default="amazon.titan-embed-text-v1", env="BEDROCK_TITAN_EMB_MODEL_ID")
    
    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="test123456", env="NEO4J_PASSWORD")
    
    # Database Configuration
    db_url: str = Field(default="sqlite:///./memory.db", env="DB_URL")
    
    # MCP Configuration
    mcp_token: str = Field(default="changeme", env="MCP_TOKEN")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    relay_port: int = Field(default=8001, env="RELAY_PORT")
    mcp_port: int = Field(default=8002, env="MCP_PORT")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Bedrock Configuration
    max_retries: int = Field(default=3, env="BEDROCK_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="BEDROCK_RETRY_DELAY")
    max_tokens: int = Field(default=4000, env="BEDROCK_MAX_TOKENS")
    temperature: float = Field(default=0.0, env="BEDROCK_TEMPERATURE")
    
    # Memory Configuration
    max_embedding_chunk_size: int = Field(default=32, env="MAX_EMBEDDING_CHUNK_SIZE")
    default_confidence_threshold: float = Field(default=0.6, env="DEFAULT_CONFIDENCE_THRESHOLD")
    default_since_days: int = Field(default=30, env="DEFAULT_SINCE_DAYS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
