"""
LLM Provider implementations.

Provides a unified interface for different LLM providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    def __init__(self):
        """Initialize the provider."""
        self.temperature = settings.AI_ENGINE_LLM_TEMPERATURE
        self.max_tokens = settings.AI_ENGINE_LLM_MAX_TOKENS
        self.model_name = settings.AI_ENGINE_LLM_MODEL

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response (uses default if not specified)
            temperature: Temperature for generation (uses default if not specified)
            response_format: Expected format ('text' or 'json')

        Returns:
            Generated text response
        """
        pass


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.
    """

    def __init__(self):
        """Initialize Gemini provider."""
        super().__init__()
        self.api_key = settings.GOOGLE_AI_API_KEY

        if not self.api_key:
            log.warning("GOOGLE_AI_API_KEY not set, Gemini provider will fail")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate response using Google Gemini API.
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)

            # Create the model
            model = genai.GenerativeModel(self.model_name)

            # Configure generation
            generation_config = {
                "temperature": temperature or self.temperature,
                "max_output_tokens": max_tokens or self.max_tokens,
            }

            if response_format == 'json':
                generation_config["response_mime_type"] = "application/json"

            # Generate content
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            return response.text

        except ImportError:
            log.error("google-generativeai package not installed")
            raise RuntimeError(
                "Please install google-generativeai: pip install google-generativeai"
            )
        except Exception as e:
            log.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.
    """

    def __init__(self):
        """Initialize Claude provider."""
        super().__init__()
        self.api_key = settings.ANTHROPIC_API_KEY

        if not self.api_key:
            log.warning("ANTHROPIC_API_KEY not set, Claude provider will fail")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate response using Anthropic Claude API.
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Prepare system message for JSON responses
            system_message = None
            if response_format == 'json':
                system_message = "You must respond with valid JSON only. Do not include any explanation outside the JSON object."

            # Generate content
            message = client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_message if system_message else anthropic.NOT_GIVEN,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except ImportError:
            log.error("anthropic package not installed")
            raise RuntimeError(
                "Please install anthropic: pip install anthropic"
            )
        except Exception as e:
            log.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude generation failed: {e}")


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider.
    """

    def __init__(self):
        """Initialize OpenAI provider."""
        super().__init__()
        self.api_key = settings.OPENAI_API_KEY

        if not self.api_key:
            log.warning("OPENAI_API_KEY not set, OpenAI provider will fail")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate response using OpenAI API.
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            # Prepare response format
            response_format_param = {"type": "json_object"} if response_format == 'json' else {"type": "text"}

            # Generate content
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                response_format=response_format_param
            )

            return completion.choices[0].message.content

        except ImportError:
            log.error("openai package not installed")
            raise RuntimeError(
                "Please install openai: pip install openai"
            )
        except Exception as e:
            log.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI generation failed: {e}")


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for testing and development.
    """

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate a mock response.
        """
        log.info(f"MockLLM received prompt ({len(prompt)} chars)")

        if response_format == 'json':
            return '{"title": "Mock Course", "description": "This is a mock response", "learning_objectives": ["Learn concept A", "Learn concept B"]}'
        else:
            return f"This is a mock LLM response to a prompt of {len(prompt)} characters. In production, this would be replaced with actual LLM output."


def get_llm_provider() -> BaseLLMProvider:
    """
    Get the configured LLM provider.

    Returns:
        Instance of the configured LLM provider

    Raises:
        ValueError: If provider is not recognized
    """
    provider_name = settings.AI_ENGINE_LLM_PROVIDER.lower()

    providers = {
        'gemini': GeminiProvider,
        'claude': ClaudeProvider,
        'openai': OpenAIProvider,
        'mock': MockLLMProvider,
    }

    provider_class = providers.get(provider_name)

    if not provider_class:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Available providers: {', '.join(providers.keys())}"
        )

    return provider_class()


class CachedLLMProvider:
    """
    Wrapper that adds caching to an LLM provider.
    """

    def __init__(self, provider: BaseLLMProvider):
        """
        Initialize cached provider.

        Args:
            provider: Underlying LLM provider
        """
        self.provider = provider
        self.cache_ttl = settings.AI_ENGINE_CACHE_TTL

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: str = 'text'
    ) -> str:
        """
        Generate with caching.

        Only caches when temperature is 0 (deterministic).
        """
        temp = temperature if temperature is not None else self.provider.temperature

        # Only cache deterministic responses
        if temp == 0:
            cache_key = f"llm_response_{hash(prompt)}_{max_tokens}_{response_format}"
            cached_response = cache.get(cache_key)

            if cached_response:
                log.debug(f"Cache hit for LLM prompt (hash: {hash(prompt)})")
                return cached_response

            response = self.provider.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format
            )

            cache.set(cache_key, response, self.cache_ttl)
            return response

        else:
            # Don't cache non-deterministic responses
            return self.provider.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format
            )
