import json
import os
from typing import List, Optional, Dict, Any
import httpx
from app.core.config import settings


class LLMProviderError(Exception):
    """Raised when LLM provider returns an error."""
    pass


class LLMClient:
    """Multi-provider LLM client for issue analysis."""
    
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def analyze_issue(
        self,
        issue_title: str,
        issue_body: str,
        comments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze a tracking issue and return structured summary."""
        if not self.is_available():
            raise LLMProviderError("LLM_API_KEY not configured")
        
        # Build context from issue and comments
        context = self._build_context(issue_title, issue_body, comments)
        prompt = self._build_prompt(context)
        
        if self.provider in ("openai-compatible", "ollama", "litedllm", "openrouter"):
            return await self._call_openai_compatible(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.provider == "gemini":
            return await self._call_gemini(prompt)
        else:
            raise LLMProviderError(f"Unknown provider: {self.provider}")
    
    def _build_context(self, title: str, body: str, comments: List[Dict[str, Any]]) -> str:
        """Build context string from issue data."""
        parts = [f"Issue: {title}", f"Body: {body or '(empty)'}"]
        
        # Include recent comments (last 20) for context
        recent_comments = comments[-20:] if comments else []
        for comment in recent_comments:
            author = comment.get("user", {}).get("login", "unknown")
            body = comment.get("body", "")
            parts.append(f"Comment by {author}: {body[:2000]}")
        
        return "\n\n".join(parts)
    
    def _build_prompt(self, context: str) -> str:
        """Build the analysis prompt."""
        return f"""You are analyzing a Rust compiler tracking issue. Provide a structured analysis in JSON format.

Issue Context:
{context}

Return a JSON object with these exact keys:
- "summary": concise 2-3 sentence summary of the issue's current state
- "key_points": array of 3-5 key technical points or decisions
- "blockers": array of current blockers or soundness concerns
- "unresolved_questions": array of open design questions from the issue
- "advisory": true

Do not include any text outside the JSON object. All findings must be grounded in the provided context."""
    
    async def _call_openai_compatible(self, prompt: str) -> Dict[str, Any]:
        base_url = self.base_url or "https://api.openai.com/v1"
        url = f"{base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a Rust compiler expert analyzing tracking issues."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"},
                },
            )
            
            if response.status_code >= 400:
                error_detail = response.text
                raise LLMProviderError(f"OpenAI-compatible API error {response.status_code}: {error_detail}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
            result["advisory"] = True
            return result
    
    async def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.model,
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            
            if response.status_code >= 400:
                error_detail = response.text
                raise LLMProviderError(f"Anthropic API error {response.status_code}: {error_detail}")
            
            data = response.json()
            content = data["content"][0]["text"]
            result = json.loads(content)
            result["advisory"] = True
            return result
    
    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        base_url = self.base_url or "https://generativelanguage.googleapis.com"
        url = f"{base_url}/v1beta/models/{self.model}:generateContent"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                },
                params={"key": self.api_key},
                json={
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 2000,
                        "responseMimeType": "application/json",
                    },
                },
            )
            
            if response.status_code >= 400:
                error_detail = response.text
                raise LLMProviderError(f"Gemini API error {response.status_code}: {error_detail}")
            
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(content)
            result["advisory"] = True
            return result


llm_client = LLMClient()