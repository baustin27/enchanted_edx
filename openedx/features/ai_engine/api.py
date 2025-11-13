"""
Public API for AI Engine.

This module provides the interface for other apps (especially ai_learning)
to interact with the AI Engine services.
"""

import logging
from typing import Dict, List, Optional

from .services.curriculum_generator import CurriculumGeneratorService
from .services.content_creator import ContentCreatorService
from .services.student_modeler import StudentModelerService
from .services.adaptation_engine import AdaptationEngineService

log = logging.getLogger(__name__)


# ==================== Curriculum Generation ====================

def generate_curriculum(
    prompt: str,
    course_key: str,
    user_id: int,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Generate a course curriculum from a natural language prompt.

    Args:
        prompt: Natural language description of the desired course
        course_key: Open edX course key
        user_id: User ID of course creator
        metadata: Additional metadata (level, duration, prerequisites, etc.)

    Returns:
        Dictionary containing structured curriculum data

    Example:
        >>> curriculum = generate_curriculum(
        ...     prompt="Create a comprehensive undergraduate course on Machine Learning",
        ...     course_key="course-v1:MIT+6.867+2025",
        ...     user_id=123,
        ...     metadata={"level": "undergraduate", "duration_weeks": 12}
        ... )
    """
    service = CurriculumGeneratorService()
    return service.generate_curriculum(prompt, course_key, user_id, metadata)


# ==================== Content Creation ====================

def generate_lesson_content(
    lesson: Dict,
    module: Dict,
    course: Dict,
    difficulty_level: str = 'intermediate'
) -> Dict:
    """
    Generate comprehensive content for a lesson.

    Args:
        lesson: Lesson metadata
        module: Parent module metadata
        course: Parent course metadata
        difficulty_level: Target difficulty level

    Returns:
        Dictionary containing lesson content
    """
    service = ContentCreatorService()
    return service.generate_lesson_content(lesson, module, course, difficulty_level)


def generate_assessment(
    lesson: Dict,
    question_type: str,
    difficulty: str = 'medium',
    num_questions: int = 1
) -> List[Dict]:
    """
    Generate assessment questions for a lesson.

    Args:
        lesson: Lesson metadata
        question_type: Type of question (multiple_choice, short_answer, etc.)
        difficulty: Difficulty level (easy, medium, hard)
        num_questions: Number of questions to generate

    Returns:
        List of question dictionaries
    """
    service = ContentCreatorService()
    return service.generate_assessment(lesson, question_type, difficulty, num_questions)


def generate_feedback(
    question: Dict,
    student_answer: str,
    is_correct: bool,
    context: Optional[Dict] = None
) -> str:
    """
    Generate personalized feedback for a student's answer.

    Args:
        question: Question dictionary
        student_answer: Student's answer
        is_correct: Whether the answer is correct
        context: Additional context (student profile, previous attempts, etc.)

    Returns:
        Feedback string
    """
    service = ContentCreatorService()
    return service.generate_feedback(question, student_answer, is_correct, context)


# ==================== Student Modeling ====================

def analyze_student(user_id: int) -> Dict:
    """
    Perform comprehensive analysis of a student's learning patterns.

    Args:
        user_id: Student user ID

    Returns:
        Dictionary containing analysis results including:
        - learning_style
        - mastered_concepts
        - struggling_concepts
        - performance_metrics
        - engagement_metrics
    """
    service = StudentModelerService()
    return service.analyze_student(user_id)


def predict_student_performance(user_id: int, concept: str) -> float:
    """
    Predict how a student will perform on a concept.

    Args:
        user_id: Student user ID
        concept: Concept to predict performance on

    Returns:
        Predicted score (0.0 to 1.0)
    """
    service = StudentModelerService()
    return service.predict_performance(user_id, concept)


# ==================== Adaptation ====================

def analyze_interaction(user_id: int, interaction_data: Dict) -> Dict:
    """
    Analyze an interaction and determine adaptations.

    Args:
        user_id: Student user ID
        interaction_data: Data about the interaction

    Returns:
        Dictionary containing analysis and adaptation recommendations
    """
    service = AdaptationEngineService()
    return service.analyze_interaction(user_id, interaction_data)


def should_adapt(user_id: int) -> bool:
    """
    Determine if adaptation should be applied for a student.

    Args:
        user_id: Student user ID

    Returns:
        True if adaptation should be applied
    """
    service = AdaptationEngineService()
    return service.should_adapt(user_id)


# ==================== AI Tutor ====================

def get_tutor_response(
    user_id: int,
    message: str,
    context: Dict,
    conversation_history: Optional[List[Dict]] = None
) -> Dict:
    """
    Get AI tutor response to a student message.

    Args:
        user_id: Student user ID
        message: Student's message
        context: Context information (course, topic, etc.)
        conversation_history: Previous messages in conversation

    Returns:
        Dictionary with tutor response and metadata
    """
    from .llm.providers import get_llm_provider
    from .llm.prompts import AI_TUTOR_SYSTEM_PROMPT, AI_TUTOR_RESPONSE_PROMPT

    llm = get_llm_provider()

    # Build conversation history string
    history_text = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg.get('role', 'unknown')
            content = msg.get('message', '')
            history_text += f"{role}: {content}\n"

    # Build system context
    system_context = AI_TUTOR_SYSTEM_PROMPT.format(
        course_title=context.get('course_title', 'Unknown Course'),
        current_topic=context.get('current_topic', 'General'),
        student_level=context.get('student_level', 'intermediate'),
        learning_style=context.get('learning_style', 'mixed')
    )

    # Build full prompt
    full_prompt = f"{system_context}\n\n{AI_TUTOR_RESPONSE_PROMPT.format(student_message=message, conversation_history=history_text)}"

    # Generate response
    try:
        response_text = llm.generate(full_prompt, max_tokens=500)

        return {
            'response': response_text,
            'success': True,
            'confidence': 0.8,  # Could be calculated based on various factors
            'sources': []  # Could include references to course materials
        }
    except Exception as e:
        log.error(f"Error generating tutor response: {e}", exc_info=True)
        return {
            'response': "I'm having trouble responding right now. Please try again in a moment.",
            'success': False,
            'error': str(e)
        }
