"""
Content Creator Service.

Generates learning content including lessons, assessments, and examples using LLMs.
"""

import json
import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from ..llm.providers import get_llm_provider
from ..llm.prompts import (
    LESSON_CONTENT_PROMPT,
    ASSESSMENT_GENERATION_PROMPT,
    EXAMPLE_GENERATION_PROMPT,
    HINT_GENERATION_PROMPT,
)

log = logging.getLogger(__name__)


class ContentCreatorService:
    """
    Service for generating learning content using LLMs.
    """

    def __init__(self):
        """Initialize the content creator."""
        self.llm = get_llm_provider()
        self.cache_ttl = settings.AI_ENGINE_CACHE_TTL

    def generate_lesson_content(
        self,
        lesson: Dict,
        module: Dict,
        course: Dict,
        difficulty_level: str = 'intermediate'
    ) -> Dict:
        """
        Generate comprehensive lesson content.

        Args:
            lesson: Lesson metadata
            module: Parent module metadata
            course: Parent course metadata
            difficulty_level: Target difficulty level

        Returns:
            Dictionary containing lesson content
        """
        cache_key = f"lesson_content_{lesson.get('lesson_id')}"
        cached_content = cache.get(cache_key)
        if cached_content:
            log.debug(f"Returning cached content for lesson {lesson.get('lesson_id')}")
            return cached_content

        log.info(f"Generating content for lesson: {lesson.get('title')}")

        llm_prompt = LESSON_CONTENT_PROMPT.format(
            course_title=course.get('title', 'Course'),
            module_title=module.get('title', 'Module'),
            lesson_title=lesson.get('title', 'Lesson'),
            lesson_objectives='\n'.join(f"- {obj}" for obj in lesson.get('learning_objectives', [])),
            difficulty_level=difficulty_level,
            estimated_minutes=lesson.get('estimated_minutes', 45)
        )

        response = self.llm.generate(llm_prompt, max_tokens=3000)

        content = {
            'lesson_id': lesson.get('lesson_id'),
            'title': lesson.get('title'),
            'introduction': self._extract_section(response, 'introduction'),
            'main_content': self._extract_section(response, 'main_content') or response,
            'examples': self._extract_section(response, 'examples'),
            'summary': self._extract_section(response, 'summary'),
            'key_takeaways': self._extract_list(response, 'key_takeaways'),
            'raw_content': response,
        }

        # Cache the generated content
        cache.set(cache_key, content, self.cache_ttl)

        log.info(f"Generated {len(response)} characters of content for {lesson.get('title')}")

        return content

    def generate_assessment(
        self,
        lesson: Dict,
        question_type: str,
        difficulty: str = 'medium',
        num_questions: int = 1
    ) -> List[Dict]:
        """
        Generate assessment questions for a lesson.

        Args:
            lesson: Lesson metadata
            question_type: Type of question (multiple_choice, short_answer, numeric, code, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to generate

        Returns:
            List of question dictionaries
        """
        log.info(
            f"Generating {num_questions} {question_type} question(s) "
            f"for lesson {lesson.get('title')}"
        )

        llm_prompt = ASSESSMENT_GENERATION_PROMPT.format(
            lesson_title=lesson.get('title'),
            lesson_objectives='\n'.join(f"- {obj}" for obj in lesson.get('learning_objectives', [])),
            question_type=question_type,
            difficulty=difficulty,
            num_questions=num_questions
        )

        response = self.llm.generate(llm_prompt, response_format='json')

        try:
            questions_data = json.loads(response)
            questions = questions_data.get('questions', [])[:num_questions]
        except json.JSONDecodeError:
            log.error(f"Failed to parse assessment JSON for {lesson.get('title')}")
            questions = []

        # Ensure each question has required fields
        for idx, question in enumerate(questions):
            question.setdefault('question_id', f"{lesson.get('lesson_id')}_q{idx+1}")
            question.setdefault('type', question_type)
            question.setdefault('difficulty', difficulty)
            question.setdefault('points', 1)

        log.info(f"Generated {len(questions)} questions")

        return questions

    def generate_examples(
        self,
        topic: str,
        context: str,
        num_examples: int = 3,
        include_code: bool = False
    ) -> List[Dict]:
        """
        Generate examples to illustrate a concept.

        Args:
            topic: Topic or concept to illustrate
            context: Additional context about the topic
            num_examples: Number of examples to generate
            include_code: Whether to include code examples

        Returns:
            List of example dictionaries
        """
        log.info(f"Generating {num_examples} examples for topic: {topic}")

        llm_prompt = EXAMPLE_GENERATION_PROMPT.format(
            topic=topic,
            context=context,
            num_examples=num_examples,
            include_code='yes' if include_code else 'no'
        )

        response = self.llm.generate(llm_prompt, response_format='json')

        try:
            examples_data = json.loads(response)
            examples = examples_data.get('examples', [])[:num_examples]
        except json.JSONDecodeError:
            log.error(f"Failed to parse examples JSON for {topic}")
            examples = []

        log.info(f"Generated {len(examples)} examples")

        return examples

    def generate_hint(
        self,
        question: Dict,
        student_answer: Optional[str] = None,
        hint_level: int = 1
    ) -> str:
        """
        Generate a hint for a question.

        Args:
            question: Question dictionary
            student_answer: Student's attempted answer (optional)
            hint_level: Level of hint (1=subtle, 2=moderate, 3=direct)

        Returns:
            Hint string
        """
        log.info(f"Generating level {hint_level} hint for question")

        llm_prompt = HINT_GENERATION_PROMPT.format(
            question_text=question.get('text', ''),
            question_type=question.get('type', 'unknown'),
            student_answer=student_answer or 'No answer yet',
            hint_level=hint_level
        )

        hint = self.llm.generate(llm_prompt, max_tokens=200)

        return hint.strip()

    def generate_feedback(
        self,
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
        log.info(f"Generating feedback for {'correct' if is_correct else 'incorrect'} answer")

        context = context or {}

        prompt = f"""Generate personalized feedback for a student's answer.

Question: {question.get('text', '')}
Type: {question.get('type', 'unknown')}
Correct Answer: {question.get('correct_answer', 'See explanation')}

Student's Answer: {student_answer}
Is Correct: {is_correct}

Previous Attempts: {context.get('attempts', 0)}
Student Learning Style: {context.get('learning_style', 'unknown')}

Provide encouraging, constructive feedback that:
1. Confirms correctness or explains the mistake
2. Provides insight into why the answer is right/wrong
3. Suggests next steps or areas to review
4. Adapts tone to the student's learning style

Keep feedback concise (2-4 sentences) and supportive.
"""

        feedback = self.llm.generate(prompt, max_tokens=300)

        return feedback.strip()

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """
        Extract a named section from markdown-style content.

        Looks for patterns like:
        ## Introduction
        Content here...

        ## Main Content
        More content...
        """
        import re

        # Try to find section headers
        pattern = rf"##\s*{section_name.replace('_', ' ').title()}\s*\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return None

    def _extract_list(self, content: str, list_name: str) -> List[str]:
        """
        Extract a bulleted list from content.
        """
        import re

        section = self._extract_section(content, list_name)
        if not section:
            return []

        # Find bullet points
        pattern = r'^[*\-•]\s+(.+)$'
        matches = re.findall(pattern, section, re.MULTILINE)

        return [match.strip() for match in matches]
