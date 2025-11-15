"""
Common settings for AI Engine.
"""


def plugin_settings(settings):
    """
    Add AI Engine specific settings.
    """
    # LLM Provider Configuration
    settings.AI_ENGINE_LLM_PROVIDER = settings.ENV_TOKENS.get(
        'AI_ENGINE_LLM_PROVIDER',
        'gemini'  # Options: 'gemini', 'claude', 'openai'
    )

    settings.AI_ENGINE_LLM_MODEL = settings.ENV_TOKENS.get(
        'AI_ENGINE_LLM_MODEL',
        {
            'gemini': 'gemini-2.0-flash-exp',
            'claude': 'claude-3-5-haiku-20241022',
            'openai': 'gpt-4o-mini'
        }.get(settings.AI_ENGINE_LLM_PROVIDER, 'gemini-2.0-flash-exp')
    )

    settings.AI_ENGINE_LLM_TEMPERATURE = settings.ENV_TOKENS.get(
        'AI_ENGINE_LLM_TEMPERATURE',
        0.7
    )

    settings.AI_ENGINE_LLM_MAX_TOKENS = settings.ENV_TOKENS.get(
        'AI_ENGINE_LLM_MAX_TOKENS',
        2048
    )

    # API Keys for LLM providers
    settings.GOOGLE_AI_API_KEY = settings.AUTH_TOKENS.get(
        'GOOGLE_AI_API_KEY',
        ''
    )

    settings.ANTHROPIC_API_KEY = settings.AUTH_TOKENS.get(
        'ANTHROPIC_API_KEY',
        ''
    )

    settings.OPENAI_API_KEY = settings.AUTH_TOKENS.get(
        'OPENAI_API_KEY',
        ''
    )

    # Vector Database Configuration
    settings.AI_ENGINE_VECTOR_DB_URL = settings.ENV_TOKENS.get(
        'AI_ENGINE_VECTOR_DB_URL',
        ''  # Empty means no vector DB
    )

    settings.AI_ENGINE_VECTOR_DB_COLLECTION = settings.ENV_TOKENS.get(
        'AI_ENGINE_VECTOR_DB_COLLECTION',
        'learning_content'
    )

    # Course Generation Settings
    settings.AI_ENGINE_MAX_MODULES_PER_COURSE = settings.ENV_TOKENS.get(
        'AI_ENGINE_MAX_MODULES_PER_COURSE',
        12
    )

    settings.AI_ENGINE_MAX_LESSONS_PER_MODULE = settings.ENV_TOKENS.get(
        'AI_ENGINE_MAX_LESSONS_PER_MODULE',
        10
    )

    # Content Generation Settings
    settings.AI_ENGINE_GENERATE_IMAGES = settings.ENV_TOKENS.get(
        'AI_ENGINE_GENERATE_IMAGES',
        False  # Requires image generation API
    )

    settings.AI_ENGINE_IMAGE_MODEL = settings.ENV_TOKENS.get(
        'AI_ENGINE_IMAGE_MODEL',
        'dall-e-3'
    )

    # Student Modeling Settings
    settings.AI_ENGINE_LEARNING_STYLE_THRESHOLD = settings.ENV_TOKENS.get(
        'AI_ENGINE_LEARNING_STYLE_THRESHOLD',
        5  # Minimum interactions before identifying learning style
    )

    settings.AI_ENGINE_MASTERY_THRESHOLD = settings.ENV_TOKENS.get(
        'AI_ENGINE_MASTERY_THRESHOLD',
        0.85  # 85% correct to consider concept mastered
    )

    settings.AI_ENGINE_STRUGGLE_THRESHOLD = settings.ENV_TOKENS.get(
        'AI_ENGINE_STRUGGLE_THRESHOLD',
        0.50  # Below 50% indicates struggling
    )

    # Adaptation Settings
    settings.AI_ENGINE_ADAPTATION_ENABLED = settings.ENV_TOKENS.get(
        'AI_ENGINE_ADAPTATION_ENABLED',
        True
    )

    settings.AI_ENGINE_MIN_INTERACTIONS_FOR_ADAPTATION = settings.ENV_TOKENS.get(
        'AI_ENGINE_MIN_INTERACTIONS_FOR_ADAPTATION',
        3  # Need at least 3 interactions before adapting
    )

    # Caching
    settings.AI_ENGINE_CACHE_TTL = settings.ENV_TOKENS.get(
        'AI_ENGINE_CACHE_TTL',
        3600  # 1 hour cache for generated content
    )

    # Rate Limiting
    settings.AI_ENGINE_LLM_RATE_LIMIT_PER_MINUTE = settings.ENV_TOKENS.get(
        'AI_ENGINE_LLM_RATE_LIMIT_PER_MINUTE',
        60
    )

    # Celery Task Settings
    settings.AI_ENGINE_CELERY_TASK_TIME_LIMIT = settings.ENV_TOKENS.get(
        'AI_ENGINE_CELERY_TASK_TIME_LIMIT',
        600  # 10 minutes
    )
