"""
Django app configuration for AI Engine.
"""

from django.apps import AppConfig


class AIEngineConfig(AppConfig):
    """
    Configuration for the AI Engine app.
    """
    name = 'openedx.features.ai_engine'
    verbose_name = 'AI Learning Engine'

    plugin_app = {
        'settings_config': {
            'lms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'production': {'relative_path': 'settings.production'},
            },
            'cms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'production': {'relative_path': 'settings.production'},
            },
        },
    }

    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        pass  # No signals needed for now
