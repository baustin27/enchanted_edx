"""
Client for communicating with the AI Engine.

This module provides a unified interface for the ai_learning app to interact
with the AI Engine. The AI Engine is now integrated directly into edx-platform
as a Django app (openedx.features.ai_engine), so this client simply wraps
those local API calls.

Note: This maintains the same interface as the original HTTP client for
backward compatibility, but now calls local functions instead of making
HTTP requests.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings

log = logging.getLogger(__name__)


class AIEngineClientError(Exception):
    """Base exception for AI Engine client errors."""
    pass


class AIEngineClient:
    """
    Client for communicating with the AI Engine.

    This client now uses the local AI Engine Django app instead of
    making HTTP requests to an external service.
    """

    def __init__(
        self,
        timeout: Optional[int] = None
    ):
        """
        Initialize the AI Engine client.

        Args:
            timeout: Request timeout in seconds (maintained for compatibility)
        """
        self.timeout = timeout or settings.AI_ENGINE_TIMEOUT

        # Check if AI Engine features are enabled
        if not hasattr(settings, 'AI_ENGINE_LLM_PROVIDER'):
            log.warning("AI Engine settings not found. Make sure ai_engine app is installed.")

    def _call_engine(self, func, *args, **kwargs) -> Any:
        """
        Call an AI Engine function with error handling.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from the function

        Raises:
            AIEngineClientError: If the call fails
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"AI Engine call failed: {e}", exc_info=True)
            raise AIEngineClientError(f"Engine call failed: {e}") from e

    # Curriculum Generation API

    def generate_curriculum(
        self,
        prompt: str,
        course_key: str,
        user_id: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Request curriculum generation from AI Engine.

        Args:
            prompt: Natural language course description
            course_key: Open edX course key
            user_id: User ID of course creator
            metadata: Additional metadata

        Returns:
            Dictionary with course_id and curriculum data
        """
        from openedx.features.ai_engine import api as engine_api

        curriculum = self._call_engine(
            engine_api.generate_curriculum,
            prompt=prompt,
            course_key=course_key,
            user_id=user_id,
            metadata=metadata
        )

        # Return in expected format
        return {
            'course_id': curriculum.get('course_key'),
            'status': 'generating',
            'curriculum': curriculum
        }

    def get_curriculum_status(self, course_id: str) -> Dict:
        """Get the status of curriculum generation."""
        # With local engine, generation is synchronous, so it's always complete
        return {
            'course_id': course_id,
            'status': 'completed'
        }

    def get_curriculum_data(self, course_id: str) -> Dict:
        """Get the generated curriculum data."""
        # Data is returned immediately during generation
        return {
            'course_id': course_id,
            'status': 'completed'
        }

    # Content Creation API

    def generate_lesson_content(
        self,
        course_id: str,
        module_id: str,
        lesson_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate content for a specific lesson.

        Args:
            course_id: AI Engine course ID
            module_id: Module identifier
            lesson_id: Lesson identifier
            context: Additional context for content generation

        Returns:
            Dictionary with generated content
        """
        from openedx.features.ai_engine import api as engine_api

        # Build lesson/module/course metadata from context
        lesson = context.get('lesson', {}) if context else {}
        module = context.get('module', {}) if context else {}
        course = context.get('course', {}) if context else {}

        lesson.setdefault('lesson_id', lesson_id)
        module.setdefault('module_id', module_id)
        course.setdefault('course_id', course_id)

        content = self._call_engine(
            engine_api.generate_lesson_content,
            lesson=lesson,
            module=module,
            course=course,
            difficulty_level=context.get('difficulty_level', 'intermediate') if context else 'intermediate'
        )

        return content

    def generate_assessment(
        self,
        course_id: str,
        module_id: str,
        lesson_id: str,
        question_type: str,
        difficulty: str = 'medium',
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate an assessment question.

        Args:
            course_id: AI Engine course ID
            module_id: Module identifier
            lesson_id: Lesson identifier
            question_type: Type of question
            difficulty: Question difficulty level
            context: Additional context

        Returns:
            Dictionary with generated question
        """
        from openedx.features.ai_engine import api as engine_api

        lesson = context.get('lesson', {}) if context else {}
        lesson.setdefault('lesson_id', lesson_id)

        questions = self._call_engine(
            engine_api.generate_assessment,
            lesson=lesson,
            question_type=question_type,
            difficulty=difficulty,
            num_questions=1
        )

        return questions[0] if questions else {}

    # Student Profile API

    def create_student_profile(self, user_id: int, username: str) -> Dict:
        """Create a new student profile in AI Engine."""
        # Profile is created automatically by StudentModelerService
        return {
            'user_id': user_id,
            'username': username,
            'status': 'created'
        }

    def get_student_profile(self, user_id: int) -> Dict:
        """Get student profile data from AI Engine."""
        from openedx.features.ai_engine import api as engine_api

        analysis = self._call_engine(
            engine_api.analyze_student,
            user_id=user_id
        )

        return {
            'user_id': user_id,
            'learning_style': analysis.get('learning_style', 'unknown'),
            'mastered_concepts': analysis.get('mastered_concepts', []),
            'struggling_concepts': analysis.get('struggling_concepts', []),
            'preferences': analysis.get('preferences', {}),
            'performance_metrics': analysis.get('performance_metrics', {})
        }

    def update_student_profile(self, user_id: int, profile_data: Dict) -> Dict:
        """Update student profile data."""
        # Profile is updated automatically by StudentModelerService
        # when interactions are recorded
        return {
            'user_id': user_id,
            'status': 'updated'
        }

    # Interaction Recording API

    def record_interaction(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        interaction_type: str,
        data: Dict
    ) -> Dict:
        """
        Record a student interaction for analysis.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            interaction_type: Type of interaction
            data: Interaction data

        Returns:
            Analysis results from AI Engine
        """
        from openedx.features.ai_engine import api as engine_api

        start_time = time.time()

        # Analyze the interaction
        interaction_data = {
            'interaction_type': interaction_type,
            'course_key': course_key,
            'usage_key': usage_key,
            **data
        }

        analysis = self._call_engine(
            engine_api.analyze_interaction,
            user_id=user_id,
            interaction_data=interaction_data
        )

        response_time = int((time.time() - start_time) * 1000)

        return {
            'analysis': analysis.get('student_profile_summary', {}),
            'adaptations': analysis.get('adaptations', []),
            'response_time_ms': response_time
        }

    # Adaptive Feedback API

    def get_adaptive_feedback(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        question: Dict,
        answer: Dict
    ) -> Dict:
        """
        Get personalized feedback for a student's answer.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            question: Question data
            answer: Student's answer data

        Returns:
            Personalized feedback and adaptation instructions
        """
        from openedx.features.ai_engine import api as engine_api

        # Get student profile for context
        try:
            student_analysis = engine_api.analyze_student(user_id)
            context = {
                'attempts': answer.get('attempts', 1),
                'learning_style': student_analysis.get('learning_style', 'unknown'),
                'overall_performance': student_analysis.get('performance_metrics', {}).get('overall_score', 0)
            }
        except Exception as e:
            log.warning(f"Could not get student profile: {e}")
            context = {}

        # Generate feedback
        feedback_text = self._call_engine(
            engine_api.generate_feedback,
            question=question,
            student_answer=answer.get('value', ''),
            is_correct=answer.get('is_correct', False),
            context=context
        )

        # Analyze for adaptations
        interaction_data = {
            'interaction_type': 'assessment',
            'question': question,
            'answer': answer,
            'score_percentage': 100 if answer.get('is_correct') else 0,
            'attempts': answer.get('attempts', 1),
            'concept': question.get('concept', 'unknown')
        }

        adaptation_result = self._call_engine(
            engine_api.analyze_interaction,
            user_id=user_id,
            interaction_data=interaction_data
        )

        return {
            'feedback': feedback_text,
            'success': True,
            'hints': [],  # Could be generated if needed
            'adaptations': adaptation_result.get('adaptations', [])
        }

    # AI Tutor API

    def get_tutor_response(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        message: str,
        history: List[Dict]
    ) -> Dict:
        """
        Get AI tutor response to student message.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            message: Student's message
            history: Conversation history

        Returns:
            AI tutor response
        """
        from openedx.features.ai_engine import api as engine_api

        # Build context
        context = {
            'course_title': course_key,  # Could be enhanced with actual course title
            'current_topic': 'General',  # Could be derived from usage_key
            'student_level': 'intermediate',  # Could come from student profile
            'learning_style': 'mixed'  # Could come from student profile
        }

        # Get student profile to enhance context
        try:
            student_analysis = engine_api.analyze_student(user_id)
            context['learning_style'] = student_analysis.get('learning_style', 'mixed')
        except Exception as e:
            log.warning(f"Could not get student profile for tutor: {e}")

        response = self._call_engine(
            engine_api.get_tutor_response,
            user_id=user_id,
            message=message,
            context=context,
            conversation_history=history
        )

        return response

    # Health Check

    def health_check(self) -> Dict:
        """Check if AI Engine is healthy and accessible."""
        try:
            # Try to import the AI Engine
            from openedx.features.ai_engine import api as engine_api

            return {
                'status': 'healthy',
                'mode': 'local',
                'llm_provider': settings.AI_ENGINE_LLM_PROVIDER
            }
        except Exception as e:
            log.warning(f"AI Engine health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
