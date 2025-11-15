# AI Engine for Open edX

The AI Engine is an integrated Django application that provides intelligent, adaptive learning capabilities for the Open edX platform. It uses Large Language Models (LLMs) to generate curricula, create content, model student learning patterns, and make real-time adaptation decisions.

## Overview

The AI Engine consists of four core services:

1. **Curriculum Generator** - Creates structured course curricula from natural language prompts
2. **Content Creator** - Generates lesson content, assessments, examples, and feedback
3. **Student Modeler** - Analyzes student learning patterns and builds comprehensive profiles
4. **Adaptation Engine** - Makes real-time decisions about curriculum adjustments

## Architecture

The AI Engine is integrated directly into edx-platform as a Django app (`openedx.features.ai_engine`), eliminating the need for a separate microservice. It communicates with the `openedx.features.ai_learning` app through a clean Python API.

```
openedx/features/ai_engine/
├── __init__.py
├── apps.py                    # Django app configuration
├── api.py                     # Public API for other apps
├── settings/                  # Plugin settings
│   ├── common.py             # Common settings
│   └── production.py         # Production overrides
├── services/                  # Core AI services
│   ├── curriculum_generator.py
│   ├── content_creator.py
│   ├── student_modeler.py
│   └── adaptation_engine.py
└── llm/                       # LLM integration layer
    ├── providers.py          # LLM provider implementations
    └── prompts.py            # Prompt templates
```

## Configuration

### Required Settings

Add these settings to your `lms.yml` or `cms.yml` configuration file:

```yaml
# LLM Provider Configuration
AI_ENGINE_LLM_PROVIDER: 'gemini'  # Options: 'gemini', 'claude', 'openai', 'mock'

# API Keys (required based on provider)
GOOGLE_AI_API_KEY: 'your-google-api-key'      # For Gemini
ANTHROPIC_API_KEY: 'your-anthropic-api-key'  # For Claude
OPENAI_API_KEY: 'your-openai-api-key'        # For OpenAI

# Optional: Override default models
AI_ENGINE_LLM_MODEL:
  gemini: 'gemini-2.0-flash-exp'
  claude: 'claude-3-5-haiku-20241022'
  openai: 'gpt-4o-mini'

# Optional: Tune LLM parameters
AI_ENGINE_LLM_TEMPERATURE: 0.7      # Default: 0.7 (range: 0.0-1.0)
AI_ENGINE_LLM_MAX_TOKENS: 2048      # Default: 2048

# Optional: Curriculum limits
AI_ENGINE_MAX_MODULES_PER_COURSE: 12   # Default: 12
AI_ENGINE_MAX_LESSONS_PER_MODULE: 10   # Default: 10

# Optional: Learning thresholds
AI_ENGINE_MASTERY_THRESHOLD: 0.85   # Default: 0.85 (85%)
AI_ENGINE_STRUGGLE_THRESHOLD: 0.50  # Default: 0.50 (50%)

# Optional: Caching
AI_ENGINE_CACHE_TTL: 3600          # Default: 3600 seconds (1 hour)
```

### Environment Variables

For development, you can also set API keys via environment variables:

```bash
export GOOGLE_AI_API_KEY='your-google-api-key'
export ANTHROPIC_API_KEY='your-anthropic-api-key'
export OPENAI_API_KEY='your-openai-api-key'
```

### Mock Provider for Testing

For testing and development without API keys, use the mock provider:

```yaml
AI_ENGINE_LLM_PROVIDER: 'mock'
```

The mock provider returns realistic-looking dummy responses without making actual LLM API calls.

## Dependencies

The AI Engine requires one or more of these Python packages depending on your chosen LLM provider:

```bash
# For Google Gemini
pip install google-generativeai

# For Anthropic Claude
pip install anthropic

# For OpenAI
pip install openai
```

These dependencies are optional - install only the package(s) for your chosen provider(s).

## Services

### 1. Curriculum Generator Service

Generates structured course curricula from natural language prompts.

**Features:**
- Parses high-level course goals and metadata
- Creates course structure with modules and lessons
- Generates learning objectives and prerequisites
- Supports any education level (K-12 through PhD)

**Example:**
```python
from openedx.features.ai_engine import api as ai_engine_api

curriculum = ai_engine_api.generate_curriculum(
    prompt="Create a comprehensive introduction to Python programming",
    course_key="course-v1:MyOrg+CS101+2024",
    user_id=123,
    metadata={
        'level': 'undergraduate',
        'duration_weeks': 12,
        'prerequisites': ['Basic computer literacy']
    }
)
```

**Response:**
```python
{
    'course_key': 'course-v1:MyOrg+CS101+2024',
    'title': 'Introduction to Python Programming',
    'description': '...',
    'level': 'undergraduate',
    'duration_weeks': 12,
    'learning_objectives': ['Understand Python syntax', ...],
    'modules': [
        {
            'module_id': 'module_1',
            'title': 'Python Basics',
            'description': '...',
            'lessons': [
                {
                    'lesson_id': 'lesson_1',
                    'title': 'Variables and Data Types',
                    'objectives': ['...'],
                    'duration_minutes': 45
                },
                ...
            ]
        },
        ...
    ]
}
```

### 2. Content Creator Service

Generates lesson content, assessments, examples, and feedback.

**Features:**
- Creates comprehensive lesson content with structured sections
- Generates assessment questions (multiple choice, short answer, essay, code)
- Produces worked examples with explanations
- Creates personalized feedback based on student context

**Example: Generate Lesson Content**
```python
content = ai_engine_api.generate_lesson_content(
    lesson={'lesson_id': 'lesson_1', 'title': 'Variables and Data Types'},
    module={'module_id': 'module_1', 'title': 'Python Basics'},
    course={'course_id': 'course-v1:MyOrg+CS101+2024', 'title': 'Intro to Python'},
    difficulty_level='intermediate'
)
```

**Response:**
```python
{
    'introduction': 'In this lesson, you will learn about...',
    'main_content': 'Variables are containers for storing data...',
    'examples': ['Example 1: Creating a variable...', ...],
    'summary': 'In this lesson, we covered...',
    'key_takeaways': ['Variables store data', ...],
    'practice_exercises': ['Exercise 1: Create a variable...']
}
```

**Example: Generate Assessment**
```python
questions = ai_engine_api.generate_assessment(
    lesson={'lesson_id': 'lesson_1', 'title': 'Variables and Data Types'},
    question_type='multiple_choice',
    difficulty='medium',
    num_questions=5
)
```

**Example: Generate Feedback**
```python
feedback = ai_engine_api.generate_feedback(
    question={'text': 'What is a variable?', 'type': 'short_answer'},
    student_answer='A container that holds data',
    is_correct=True,
    context={
        'attempts': 1,
        'learning_style': 'visual',
        'overall_performance': 0.85
    }
)
```

### 3. Student Modeler Service

Analyzes student interactions to build comprehensive learning profiles.

**Features:**
- Identifies learning styles (visual, auditory, kinesthetic, reading/writing, mixed)
- Tracks mastered and struggling concepts
- Calculates performance metrics
- Predicts future performance on concepts

**Example: Analyze Student**
```python
analysis = ai_engine_api.analyze_student(user_id=123)
```

**Response:**
```python
{
    'user_id': 123,
    'learning_style': 'visual',
    'mastered_concepts': ['variables', 'loops', 'functions'],
    'struggling_concepts': ['recursion', 'decorators'],
    'performance_metrics': {
        'overall_score': 0.82,
        'completion_rate': 0.75,
        'average_attempts': 1.8,
        'time_efficiency': 0.90
    },
    'engagement_metrics': {
        'total_interactions': 145,
        'active_days': 28,
        'avg_session_duration': 45.5
    },
    'preferences': {
        'prefers_video': True,
        'prefers_interactive': True
    }
}
```

**Example: Predict Performance**
```python
prediction = ai_engine_api.predict_student_performance(
    user_id=123,
    concept='object-oriented-programming'
)
# Returns: 0.65 (predicted performance score)
```

### 4. Adaptation Engine Service

Makes real-time decisions about curriculum adjustments based on student interactions.

**Features:**
- Analyzes assessment results for adaptation opportunities
- Monitors content engagement patterns
- Generates actionable adaptations (unlock content, add remedial work, trigger tutor)
- Calculates confidence scores for adaptation decisions

**Example: Analyze Interaction**
```python
result = ai_engine_api.analyze_interaction(
    user_id=123,
    interaction_data={
        'interaction_type': 'assessment',
        'course_key': 'course-v1:MyOrg+CS101+2024',
        'usage_key': 'block-v1:MyOrg+CS101+2024+type@problem+block@quiz1',
        'score_percentage': 55,
        'attempts': 3,
        'time_spent_seconds': 480,
        'concept': 'loops'
    }
)
```

**Response:**
```python
{
    'user_id': 123,
    'adaptations': [
        {
            'type': 'add_remedial',
            'action': 'provide_remedial_content',
            'target': 'loops',
            'reason': 'Score below 60% indicates struggle',
            'priority': 'high'
        },
        {
            'type': 'trigger_tutor',
            'action': 'suggest_ai_tutor',
            'reason': 'Multiple attempts without success',
            'priority': 'medium'
        }
    ],
    'student_profile_summary': {
        'learning_style': 'visual',
        'overall_performance': 0.72,
        'recent_trend': 'declining'
    },
    'confidence': 0.85
}
```

**Example: Check if Adaptation Needed**
```python
should_adapt = ai_engine_api.should_adapt(
    user_id=123,
    interaction_type='assessment',
    context={'score': 55, 'attempts': 3}
)
# Returns: True
```

### 5. AI Tutor

Provides conversational tutoring with context awareness.

**Example:**
```python
response = ai_engine_api.get_tutor_response(
    user_id=123,
    message="I don't understand how loops work in Python",
    context={
        'course_title': 'Introduction to Python',
        'current_topic': 'Control Flow',
        'student_level': 'beginner',
        'learning_style': 'visual'
    },
    conversation_history=[
        {'role': 'user', 'message': 'Hi!'},
        {'role': 'assistant', 'message': 'Hello! How can I help you today?'}
    ]
)
```

**Response:**
```python
{
    'response': "I'd be happy to help you understand loops! Let me explain with a visual example...",
    'success': True,
    'suggestions': ['Try this interactive exercise', 'Watch this video tutorial']
}
```

## API Reference

All API functions are available through `openedx.features.ai_engine.api`:

### Curriculum Generation
- `generate_curriculum(prompt, course_key, user_id, metadata=None)` - Generate course curriculum

### Content Creation
- `generate_lesson_content(lesson, module, course, difficulty_level='intermediate')` - Generate lesson content
- `generate_assessment(lesson, question_type, difficulty='medium', num_questions=1)` - Generate assessment questions
- `generate_feedback(question, student_answer, is_correct, context=None)` - Generate personalized feedback

### Student Modeling
- `analyze_student(user_id)` - Comprehensive student analysis
- `predict_student_performance(user_id, concept)` - Predict performance on a concept

### Adaptation
- `analyze_interaction(user_id, interaction_data)` - Analyze interaction and generate adaptations
- `should_adapt(user_id, interaction_type, context)` - Check if adaptation is needed

### AI Tutor
- `get_tutor_response(user_id, message, context, conversation_history=None)` - Get AI tutor response

## Integration with ai_learning

The AI Engine is designed to be used by the `openedx.features.ai_learning` app, which provides:

- REST API endpoints for external access
- Database models for storing AI-generated data
- XBlocks for in-course AI features (Adaptive Assessments, AI Tutor)
- Django admin interface
- Webhook handling

The `ai_learning` app uses the AI Engine through its client interface (`openedx.features.ai_learning.client.AIEngineClient`), which wraps the AI Engine API.

## Performance and Caching

The AI Engine includes intelligent caching to reduce API costs:

- **Deterministic responses** (temperature=0) are cached automatically
- **Cache TTL** is configurable via `AI_ENGINE_CACHE_TTL`
- **Cache keys** are based on prompt hash, tokens, and format
- **Non-deterministic responses** (temperature>0) are never cached

To clear the cache:
```python
from django.core.cache import cache
cache.delete_pattern('llm_response_*')
```

## Cost Optimization

Tips for minimizing LLM API costs:

1. **Use appropriate models**: Gemini Flash and Claude Haiku are cost-effective for most tasks
2. **Set reasonable token limits**: Default is 2048, adjust based on use case
3. **Enable caching**: Deterministic responses are cached automatically
4. **Use mock provider**: For development and testing
5. **Batch operations**: Generate multiple questions or lessons in one call when possible

## Error Handling

All AI Engine functions use consistent error handling:

```python
try:
    result = ai_engine_api.generate_curriculum(...)
except Exception as e:
    logger.error(f"AI Engine error: {e}")
    # Handle error appropriately
```

Common errors:
- **API key missing**: Check your configuration
- **Rate limit exceeded**: Implement backoff/retry logic
- **Invalid response**: LLM returned unexpected format
- **Network timeout**: Check connectivity to LLM provider

## Testing

### Unit Tests

Test individual services with the mock provider:

```python
from django.test import TestCase, override_settings

@override_settings(AI_ENGINE_LLM_PROVIDER='mock')
class TestCurriculumGenerator(TestCase):
    def test_generate_curriculum(self):
        from openedx.features.ai_engine import api
        result = api.generate_curriculum(
            prompt="Test course",
            course_key="test-course",
            user_id=1
        )
        self.assertIn('title', result)
```

### Integration Tests

Test with real LLM providers (requires API keys):

```python
@override_settings(
    AI_ENGINE_LLM_PROVIDER='gemini',
    GOOGLE_AI_API_KEY='your-test-key'
)
class TestLLMIntegration(TestCase):
    def test_real_curriculum_generation(self):
        # Test with real API
        pass
```

## Monitoring and Logging

The AI Engine logs all operations:

```python
import logging

# Enable debug logging
logging.getLogger('openedx.features.ai_engine').setLevel(logging.DEBUG)
```

Key log messages:
- `Generating curriculum for course: {course_key}`
- `LLM generation completed in {duration}ms`
- `Cache hit for LLM prompt (hash: {hash})`
- `MockLLM received prompt ({length} chars)`

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **Rate Limiting**: Implement rate limiting on public endpoints
- **Input Validation**: All user inputs are validated before passing to LLMs
- **Content Filtering**: Consider implementing content safety checks on LLM outputs
- **PII Protection**: Student data is handled according to Open edX privacy policies

## Future Enhancements

Potential improvements:

1. **Multi-modal content**: Generate images, videos, and interactive simulations
2. **Real-time collaboration**: Enable AI-assisted group learning
3. **Advanced analytics**: Deeper insights into learning patterns
4. **Custom models**: Support for fine-tuned or specialized models
5. **Multilingual support**: Generate content in multiple languages
6. **Accessibility features**: Optimize content for screen readers and assistive technologies

## Support and Contributing

For questions, issues, or contributions:

- **Documentation**: See `docs/decisions/0024-ai-adaptive-learning-engine.rst`
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join the Open edX community forums

## License

This code is part of the Open edX platform and is released under the AGPL v3 license.
