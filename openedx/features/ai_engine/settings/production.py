"""
Production settings for AI Engine.
"""


def plugin_settings(settings):
    """
    Production-specific AI Engine settings.
    """
    provider = settings.AI_ENGINE_LLM_PROVIDER

    # Validate API keys are set in production
    if provider == 'gemini' and not settings.GOOGLE_AI_API_KEY:
        raise ValueError('GOOGLE_AI_API_KEY must be set when using Gemini provider')

    if provider == 'claude' and not settings.ANTHROPIC_API_KEY:
        raise ValueError('ANTHROPIC_API_KEY must be set when using Claude provider')

    if provider == 'openai' and not settings.OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY must be set when using OpenAI provider')

    # Ensure rate limiting is enabled in production
    if settings.AI_ENGINE_LLM_RATE_LIMIT_PER_MINUTE > 100:
        raise ValueError(
            'AI_ENGINE_LLM_RATE_LIMIT_PER_MINUTE should not exceed 100 in production '
            'to prevent excessive API costs'
        )
