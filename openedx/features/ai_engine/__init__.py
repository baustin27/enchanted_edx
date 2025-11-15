"""
AI Engine for adaptive learning - integrated into edx-platform.

This Django application provides the AI intelligence layer that powers
adaptive learning, including:
- Curriculum generation from natural language
- Automated content creation using LLMs
- Student learning profile modeling
- Real-time adaptation decisions
"""

default_app_config = 'openedx.features.ai_engine.apps.AIEngineConfig'
