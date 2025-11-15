"""
Adaptation Engine Service.

Makes real-time decisions about content adaptation based on student performance
and learning patterns.
"""

import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model

from .student_modeler import StudentModelerService

User = get_user_model()
log = logging.getLogger(__name__)


class AdaptationEngineService:
    """
    Service for making adaptive learning decisions.
    """

    def __init__(self):
        """Initialize the adaptation engine."""
        self.student_modeler = StudentModelerService()
        self.adaptation_enabled = settings.AI_ENGINE_ADAPTATION_ENABLED
        self.min_interactions = settings.AI_ENGINE_MIN_INTERACTIONS_FOR_ADAPTATION

    def analyze_interaction(
        self,
        user_id: int,
        interaction_data: Dict
    ) -> Dict:
        """
        Analyze an interaction and determine adaptations.

        Args:
            user_id: Student user ID
            interaction_data: Data about the interaction

        Returns:
            Dictionary containing analysis and adaptation recommendations
        """
        if not self.adaptation_enabled:
            log.debug("Adaptation is disabled")
            return {'adaptations': []}

        log.info(f"Analyzing interaction for user {user_id}")

        # Get student analysis
        student_analysis = self.student_modeler.analyze_student(user_id)

        # Determine adaptations based on interaction and student profile
        adaptations = []

        interaction_type = interaction_data.get('interaction_type', 'unknown')

        if interaction_type == 'assessment':
            adaptations.extend(
                self._adapt_for_assessment(interaction_data, student_analysis)
            )
        elif interaction_type == 'content_view':
            adaptations.extend(
                self._adapt_for_content_view(interaction_data, student_analysis)
            )

        # Add general adaptations
        adaptations.extend(
            self._general_adaptations(student_analysis)
        )

        result = {
            'user_id': user_id,
            'adaptations': adaptations,
            'student_profile_summary': {
                'learning_style': student_analysis.get('learning_style'),
                'overall_performance': student_analysis.get('performance_metrics', {}).get('overall_score'),
                'trend': student_analysis.get('performance_metrics', {}).get('improvement_trend'),
            },
            'confidence': self._calculate_confidence(student_analysis),
        }

        log.info(
            f"Generated {len(adaptations)} adaptations for user {user_id} "
            f"with confidence {result['confidence']:.2f}"
        )

        return result

    def _adapt_for_assessment(
        self,
        interaction_data: Dict,
        student_analysis: Dict
    ) -> List[Dict]:
        """
        Determine adaptations based on assessment performance.

        Returns:
            List of adaptation dictionaries
        """
        adaptations = []

        score = interaction_data.get('score_percentage', 0)
        attempts = interaction_data.get('attempts', 1)
        concept = interaction_data.get('concept', 'unknown')

        # High performance - unlock advanced content
        if score >= 90 and attempts == 1:
            adaptations.append({
                'type': 'unlock_content',
                'reason': 'Strong performance on first attempt',
                'action': 'unlock_advanced_content',
                'parameters': {
                    'concept': concept,
                    'difficulty_increase': 'moderate'
                }
            })

        # Excellent trend - skip ahead
        if (student_analysis.get('performance_metrics', {}).get('improvement_trend') == 'improving' and
            score >= 85):
            adaptations.append({
                'type': 'skip_ahead',
                'reason': 'Consistent high performance',
                'action': 'suggest_acceleration',
                'parameters': {
                    'modules_to_skip': 0,  # Just suggest, don't auto-skip
                    'suggestion_only': True
                }
            })

        # Low performance - add remedial content
        if score < 60:
            adaptations.append({
                'type': 'add_remedial',
                'reason': f'Score below threshold ({score}%)',
                'action': 'provide_remedial_content',
                'parameters': {
                    'concept': concept,
                    'focus_areas': [concept],
                    'difficulty_level': 'beginner'
                }
            })

        # Multiple attempts with low score - trigger tutor
        if attempts >= 3 and score < 70:
            adaptations.append({
                'type': 'trigger_tutor',
                'reason': 'Multiple attempts with continued struggle',
                'action': 'suggest_ai_tutor',
                'parameters': {
                    'concept': concept,
                    'message': f"Having trouble with {concept}? Let's chat about it!"
                }
            })

        # Struggling concept - adjust difficulty
        if concept in student_analysis.get('struggling_concepts', []):
            adaptations.append({
                'type': 'adjust_difficulty',
                'reason': 'Previously identified struggling concept',
                'action': 'reduce_difficulty',
                'parameters': {
                    'concept': concept,
                    'difficulty_adjustment': -1  # Reduce by one level
                }
            })

        return adaptations

    def _adapt_for_content_view(
        self,
        interaction_data: Dict,
        student_analysis: Dict
    ) -> List[Dict]:
        """
        Determine adaptations based on content viewing behavior.

        Returns:
            List of adaptation dictionaries
        """
        adaptations = []

        time_spent = interaction_data.get('time_spent', 0)
        expected_time = interaction_data.get('expected_time', 300)  # 5 minutes default

        # Spent very little time - suggest review
        if time_spent > 0 and time_spent < expected_time * 0.3:
            adaptations.append({
                'type': 'suggest_review',
                'reason': 'Quick navigation through content',
                'action': 'recommend_slower_pace',
                'parameters': {
                    'message': 'Take your time to fully understand the material'
                }
            })

        # Spent excessive time - might be struggling
        if time_spent > expected_time * 2:
            adaptations.append({
                'type': 'trigger_tutor',
                'reason': 'Extended time on content suggests difficulty',
                'action': 'offer_assistance',
                'parameters': {
                    'message': 'Need help understanding this material?'
                }
            })

        return adaptations

    def _general_adaptations(self, student_analysis: Dict) -> List[Dict]:
        """
        Generate general adaptations based on overall student profile.

        Returns:
            List of adaptation dictionaries
        """
        adaptations = []

        performance = student_analysis.get('performance_metrics', {})
        learning_style = student_analysis.get('learning_style', 'unknown')

        # Suggest learning style specific content
        if learning_style != 'unknown':
            adaptations.append({
                'type': 'content_preference',
                'reason': f'Identified {learning_style} learning style',
                'action': 'prioritize_content_type',
                'parameters': {
                    'learning_style': learning_style,
                    'content_types': self._get_preferred_content_types(learning_style)
                }
            })

        # Declining performance - intervention needed
        if performance.get('improvement_trend') == 'declining':
            adaptations.append({
                'type': 'intervention',
                'reason': 'Declining performance trend',
                'action': 'alert_instructor',
                'parameters': {
                    'severity': 'moderate',
                    'message': 'Student may benefit from additional support'
                }
            })

        return adaptations

    def _get_preferred_content_types(self, learning_style: str) -> List[str]:
        """
        Get preferred content types for a learning style.

        Args:
            learning_style: Student's learning style

        Returns:
            List of preferred content types
        """
        preferences = {
            'visual': ['video', 'diagram', 'infographic', 'animation'],
            'auditory': ['audio', 'lecture', 'podcast', 'discussion'],
            'kinesthetic': ['interactive', 'simulation', 'lab', 'hands-on'],
            'reading_writing': ['text', 'article', 'documentation', 'notes'],
            'mixed': ['video', 'text', 'interactive', 'examples'],
        }

        return preferences.get(learning_style, preferences['mixed'])

    def _calculate_confidence(self, student_analysis: Dict) -> float:
        """
        Calculate confidence in adaptation recommendations.

        Confidence is based on:
        - Number of interactions (more data = higher confidence)
        - Consistency of performance
        - Time span of data

        Args:
            student_analysis: Student analysis dictionary

        Returns:
            Confidence score (0.0 to 1.0)
        """
        total_interactions = student_analysis.get('total_interactions', 0)

        # Base confidence on number of interactions
        if total_interactions < 5:
            base_confidence = 0.3
        elif total_interactions < 10:
            base_confidence = 0.5
        elif total_interactions < 20:
            base_confidence = 0.7
        else:
            base_confidence = 0.9

        # Adjust for performance consistency
        performance = student_analysis.get('performance_metrics', {})
        trend = performance.get('improvement_trend', 'neutral')

        if trend == 'neutral':
            consistency_factor = 1.0  # Stable is good
        elif trend in ['improving', 'declining']:
            consistency_factor = 0.9  # Some variance

        confidence = base_confidence * consistency_factor

        return min(1.0, max(0.0, confidence))

    def should_adapt(self, user_id: int) -> bool:
        """
        Determine if adaptation should be applied for a student.

        Args:
            user_id: Student user ID

        Returns:
            True if adaptation should be applied
        """
        if not self.adaptation_enabled:
            return False

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return False

        # Check if student has enough interactions
        from openedx.features.ai_learning.models import AdaptiveInteraction

        interaction_count = AdaptiveInteraction.objects.filter(user=user).count()

        return interaction_count >= self.min_interactions
