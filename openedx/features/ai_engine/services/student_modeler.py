"""
Student Modeler Service.

Tracks and analyzes student learning patterns, identifies learning styles,
and maintains student profiles for personalization.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model

from openedx.features.ai_learning.models import AdaptiveInteraction, StudentLearningProfile

User = get_user_model()
log = logging.getLogger(__name__)


class StudentModelerService:
    """
    Service for modeling student learning patterns and preferences.
    """

    def __init__(self):
        """Initialize the student modeler."""
        self.mastery_threshold = settings.AI_ENGINE_MASTERY_THRESHOLD
        self.struggle_threshold = settings.AI_ENGINE_STRUGGLE_THRESHOLD
        self.min_interactions = settings.AI_ENGINE_LEARNING_STYLE_THRESHOLD

    def analyze_student(self, user_id: int) -> Dict:
        """
        Perform comprehensive analysis of a student's learning patterns.

        Args:
            user_id: Student user ID

        Returns:
            Dictionary containing analysis results
        """
        log.info(f"Analyzing student {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            log.error(f"User {user_id} not found")
            return {}

        # Get or create profile
        profile, created = StudentLearningProfile.objects.get_or_create(
            user=user,
            defaults={'ai_engine_profile_id': f"user_{user_id}"}
        )

        # Get recent interactions
        interactions = AdaptiveInteraction.objects.filter(
            user=user
        ).order_by('-created')[:100]

        if not interactions:
            log.info(f"No interactions found for user {user_id}")
            return {
                'user_id': user_id,
                'profile_exists': not created,
                'total_interactions': 0,
                'learning_style': 'unknown',
            }

        # Analyze various aspects
        analysis = {
            'user_id': user_id,
            'profile_exists': not created,
            'total_interactions': interactions.count(),
            'learning_style': self._identify_learning_style(interactions),
            'mastered_concepts': self._identify_mastered_concepts(interactions),
            'struggling_concepts': self._identify_struggling_concepts(interactions),
            'performance_metrics': self._calculate_performance_metrics(interactions),
            'engagement_metrics': self._calculate_engagement_metrics(interactions),
            'preferences': self._infer_preferences(interactions),
        }

        # Update profile
        profile.learning_style = analysis['learning_style']
        profile.mastered_concepts = analysis['mastered_concepts']
        profile.struggling_concepts = analysis['struggling_concepts']
        profile.preferences = analysis['preferences']
        profile.save()

        log.info(
            f"Completed analysis for user {user_id}: "
            f"{len(analysis['mastered_concepts'])} mastered, "
            f"{len(analysis['struggling_concepts'])} struggling"
        )

        return analysis

    def _identify_learning_style(self, interactions) -> str:
        """
        Identify the student's learning style based on interaction patterns.

        Analyzes:
        - Time spent on different content types
        - Performance on different question types
        - Engagement with different media

        Returns:
            Learning style: visual, auditory, kinesthetic, reading_writing, or mixed
        """
        if len(interactions) < self.min_interactions:
            return 'unknown'

        # Analyze interaction patterns
        content_preferences = defaultdict(int)
        response_times = defaultdict(list)

        for interaction in interactions:
            data = interaction.interaction_data or {}
            content_type = data.get('content_type', 'text')
            time_spent = data.get('time_spent', 0)

            content_preferences[content_type] += 1
            if time_spent > 0:
                response_times[content_type].append(time_spent)

        # Simple heuristic: most engaged content type
        if not content_preferences:
            return 'unknown'

        most_engaged = max(content_preferences, key=content_preferences.get)

        style_mapping = {
            'video': 'visual',
            'audio': 'auditory',
            'interactive': 'kinesthetic',
            'text': 'reading_writing',
            'diagram': 'visual',
            'simulation': 'kinesthetic',
        }

        return style_mapping.get(most_engaged, 'mixed')

    def _identify_mastered_concepts(self, interactions) -> List[str]:
        """
        Identify concepts the student has mastered.

        A concept is considered mastered if:
        - Average score >= mastery_threshold (e.g., 85%)
        - At least 3 successful interactions
        """
        concept_performance = defaultdict(lambda: {'scores': [], 'attempts': 0})

        for interaction in interactions:
            if interaction.interaction_type != 'assessment':
                continue

            data = interaction.interaction_data or {}
            concept = data.get('concept') or data.get('topic', 'unknown')
            score = data.get('score_percentage', 0)

            if score > 0:
                concept_performance[concept]['scores'].append(score)
                concept_performance[concept]['attempts'] += 1

        mastered = []
        for concept, perf in concept_performance.items():
            if (perf['attempts'] >= 3 and
                sum(perf['scores']) / len(perf['scores']) >= self.mastery_threshold * 100):
                mastered.append(concept)

        return mastered

    def _identify_struggling_concepts(self, interactions) -> List[str]:
        """
        Identify concepts the student is struggling with.

        A concept is marked as struggling if:
        - Average score < struggle_threshold (e.g., 50%)
        - At least 2 attempts
        """
        concept_performance = defaultdict(lambda: {'scores': [], 'attempts': 0})

        for interaction in interactions:
            if interaction.interaction_type != 'assessment':
                continue

            data = interaction.interaction_data or {}
            concept = data.get('concept') or data.get('topic', 'unknown')
            score = data.get('score_percentage', 0)

            if score >= 0:  # Include zero scores
                concept_performance[concept]['scores'].append(score)
                concept_performance[concept]['attempts'] += 1

        struggling = []
        for concept, perf in concept_performance.items():
            if (perf['attempts'] >= 2 and
                sum(perf['scores']) / len(perf['scores']) < self.struggle_threshold * 100):
                struggling.append(concept)

        return struggling

    def _calculate_performance_metrics(self, interactions) -> Dict:
        """
        Calculate various performance metrics.

        Returns:
            Dictionary with metrics like overall_score, completion_rate, etc.
        """
        assessment_interactions = [
            i for i in interactions if i.interaction_type == 'assessment'
        ]

        if not assessment_interactions:
            return {
                'overall_score': 0,
                'total_assessments': 0,
                'average_attempts': 0,
                'improvement_trend': 'neutral',
            }

        scores = []
        attempts = []

        for interaction in assessment_interactions:
            data = interaction.interaction_data or {}
            score = data.get('score_percentage', 0)
            attempt = data.get('attempts', 1)

            if score > 0:
                scores.append(score)
            attempts.append(attempt)

        overall_score = sum(scores) / len(scores) if scores else 0
        avg_attempts = sum(attempts) / len(attempts) if attempts else 0

        # Calculate trend (comparing first half vs second half)
        trend = 'neutral'
        if len(scores) >= 6:
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

            if second_half_avg > first_half_avg + 5:
                trend = 'improving'
            elif second_half_avg < first_half_avg - 5:
                trend = 'declining'

        return {
            'overall_score': round(overall_score, 2),
            'total_assessments': len(assessment_interactions),
            'average_attempts': round(avg_attempts, 2),
            'improvement_trend': trend,
            'recent_score': scores[-1] if scores else 0,
        }

    def _calculate_engagement_metrics(self, interactions) -> Dict:
        """
        Calculate engagement metrics.

        Returns:
            Dictionary with metrics like session_frequency, average_session_time, etc.
        """
        if not interactions:
            return {
                'total_interactions': 0,
                'days_active': 0,
                'average_daily_interactions': 0,
            }

        # Calculate days active
        dates = set()
        total_time = 0

        for interaction in interactions:
            dates.add(interaction.created.date())
            data = interaction.interaction_data or {}
            total_time += data.get('time_spent', 0)

        days_active = len(dates)
        avg_daily = len(interactions) / days_active if days_active > 0 else 0

        return {
            'total_interactions': len(interactions),
            'days_active': days_active,
            'average_daily_interactions': round(avg_daily, 2),
            'total_time_minutes': round(total_time / 60, 2) if total_time else 0,
        }

    def _infer_preferences(self, interactions) -> Dict:
        """
        Infer student learning preferences from interaction patterns.

        Returns:
            Dictionary of inferred preferences
        """
        tutor_interactions = [
            i for i in interactions if i.interaction_type == 'tutor_chat'
        ]

        # Calculate average time of day for interactions
        interaction_hours = [i.created.hour for i in interactions]
        avg_hour = sum(interaction_hours) / len(interaction_hours) if interaction_hours else 12

        # Determine preferred time period
        if 5 <= avg_hour < 12:
            preferred_time = 'morning'
        elif 12 <= avg_hour < 17:
            preferred_time = 'afternoon'
        elif 17 <= avg_hour < 21:
            preferred_time = 'evening'
        else:
            preferred_time = 'night'

        return {
            'prefers_ai_tutor': len(tutor_interactions) > len(interactions) * 0.2,
            'preferred_study_time': preferred_time,
            'prefers_detailed_feedback': True,  # Could be inferred from feedback interactions
        }

    def predict_performance(self, user_id: int, concept: str) -> float:
        """
        Predict how a student will perform on a concept.

        Args:
            user_id: Student user ID
            concept: Concept to predict performance on

        Returns:
            Predicted score (0.0 to 1.0)
        """
        log.info(f"Predicting performance for user {user_id} on concept: {concept}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return 0.5  # Default neutral prediction

        # Get profile
        try:
            profile = StudentLearningProfile.objects.get(user=user)
        except StudentLearningProfile.DoesNotExist:
            return 0.5

        # Check if mastered or struggling
        if concept in profile.mastered_concepts:
            return 0.9  # High confidence of success

        if concept in profile.struggling_concepts:
            return 0.3  # Low prediction

        # Get historical performance on similar concepts
        interactions = AdaptiveInteraction.objects.filter(
            user=user,
            interaction_type='assessment'
        ).order_by('-created')[:20]

        if not interactions:
            return 0.5

        # Calculate average recent performance
        scores = []
        for interaction in interactions:
            data = interaction.interaction_data or {}
            score = data.get('score_percentage', 0)
            if score > 0:
                scores.append(score / 100.0)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)
