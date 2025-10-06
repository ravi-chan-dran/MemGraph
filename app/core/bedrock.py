"""AWS Bedrock integration for Claude and Titan models."""

import json
import time
import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

from .config import settings


class BedrockClient:
    """Client for interacting with AWS Bedrock services with retry/backoff."""
    
    def __init__(self):
        """Initialize the Bedrock client."""
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region
        )
        self.claude_model_id = settings.bedrock_claude_model_id
        self.titan_model_id = settings.bedrock_titan_emb_model_id
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                if attempt == self.max_retries - 1:
                    raise e
                delay = self.retry_delay * (2 ** attempt)
                time.sleep(delay)
        return None
    
    def claude_complete(self, system_prompt: str, user_prompt: str, temperature: float = 0) -> str:
        """Generate text using Claude model with retry/backoff."""
        def _call_claude():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{system_prompt}\n\n{user_prompt}"
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.claude_model_id,
                body=body,
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        try:
            result = self._retry_with_backoff(_call_claude)
            return result if result else ""
        except Exception as e:
            print(f"Error in claude_complete: {e}")
            return ""
    
    def titan_embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Titan model with chunking and retry/backoff."""
        if not texts:
            return []
        
        # Chunk texts if they exceed max size
        chunk_size = settings.max_embedding_chunk_size
        all_embeddings = []
        
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            
            def _call_titan():
                body = json.dumps({
                    "inputText": chunk[0] if len(chunk) == 1 else chunk
                })
                
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.titan_model_id,
                    body=body,
                    contentType="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                
                if len(chunk) == 1:
                    return [response_body['embedding']]
                else:
                    return [item['embedding'] for item in response_body['embeddings']]
            
            try:
                chunk_embeddings = self._retry_with_backoff(_call_titan)
                if chunk_embeddings:
                    all_embeddings.extend(chunk_embeddings)
            except Exception as e:
                print(f"Error in titan_embed chunk {i//chunk_size}: {e}")
                # Add zero embeddings for failed chunks
                all_embeddings.extend([[0.0] * 1536 for _ in chunk])
        
        return all_embeddings
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate text using Claude model (legacy method)."""
        return self.claude_complete("", prompt)
    
    def generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings using Titan model (legacy method)."""
        return self.titan_embed(texts)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using Claude."""
        system_prompt = """
        Extract entities from the following text and return them in JSON format with categories:
        - PERSON: People mentioned
        - ORGANIZATION: Companies, institutions, groups
        - LOCATION: Places, cities, countries
        - CONCEPT: Ideas, topics, concepts
        - EVENT: Events, meetings, occurrences
        
        Return only valid JSON with the structure:
        {"PERSON": [], "ORGANIZATION": [], "LOCATION": [], "CONCEPT": [], "EVENT": []}
        """
        
        response = self.claude_complete(system_prompt, text)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"PERSON": [], "ORGANIZATION": [], "LOCATION": [], "CONCEPT": [], "EVENT": []}
        return {"PERSON": [], "ORGANIZATION": [], "LOCATION": [], "CONCEPT": [], "EVENT": []}


# Global Bedrock client instance
bedrock_client = BedrockClient()
