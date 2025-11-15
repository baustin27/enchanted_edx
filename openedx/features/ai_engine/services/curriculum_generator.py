"""
Curriculum Generator Service.

Generates structured course curricula from natural language prompts.
"""

import json
import logging
from typing import Dict, List, Optional

from django.conf import settings

from ..llm.providers import get_llm_provider
from ..llm.prompts import (
    CURRICULUM_GENERATION_PROMPT,
    MODULE_GENERATION_PROMPT,
    LESSON_PLANNING_PROMPT,
)

log = logging.getLogger(__name__)


class CurriculumGeneratorService:
    """
    Service for generating course curricula using LLMs.
    """

    def __init__(self):
        """Initialize the curriculum generator."""
        self.llm = get_llm_provider()
        self.max_modules = settings.AI_ENGINE_MAX_MODULES_PER_COURSE
        self.max_lessons = settings.AI_ENGINE_MAX_LESSONS_PER_MODULE

    def generate_curriculum(
        self,
        prompt: str,
        course_key: str,
        user_id: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a complete course curriculum from a natural language prompt.

        Args:
            prompt: Natural language description of the desired course
            course_key: Open edX course key
            user_id: User ID of course creator
            metadata: Additional metadata (level, duration, prerequisites, etc.)

        Returns:
            Dictionary containing structured curriculum data

        Example:
            >>> generator = CurriculumGeneratorService()
            >>> curriculum = generator.generate_curriculum(
            ...     prompt="Create a comprehensive undergraduate course on Machine Learning",
            ...     course_key="course-v1:MIT+6.867+2025",
            ...     user_id=123,
            ...     metadata={"level": "undergraduate", "duration_weeks": 12}
            ... )
        """
        log.info(f"Generating curriculum for course {course_key}")

        metadata = metadata or {}

        # Step 1: Generate overall course structure
        course_structure = self._generate_course_structure(prompt, metadata)

        # Step 2: Generate detailed modules
        modules = self._generate_modules(course_structure, metadata)

        # Step 3: Generate lessons for each module
        for module in modules:
            module['lessons'] = self._generate_lessons(
                module,
                course_structure,
                metadata
            )

        curriculum = {
            'course_key': course_key,
            'title': course_structure.get('title', 'Untitled Course'),
            'description': course_structure.get('description', ''),
            'learning_objectives': course_structure.get('learning_objectives', []),
            'prerequisites': course_structure.get('prerequisites', []),
            'difficulty_level': metadata.get('level', 'intermediate'),
            'estimated_duration_weeks': metadata.get('duration_weeks', 8),
            'modules': modules,
            'metadata': metadata,
        }

        log.info(
            f"Generated curriculum for {course_key}: "
            f"{len(modules)} modules, "
            f"{sum(len(m['lessons']) for m in modules)} total lessons"
        )

        return curriculum

    def _generate_course_structure(self, prompt: str, metadata: Dict) -> Dict:
        """
        Generate high-level course structure.

        Returns a dictionary with:
        - title: Course title
        - description: Course description
        - learning_objectives: List of learning objectives
        - prerequisites: List of prerequisites
        - module_topics: List of major topics (modules)
        """
        level = metadata.get('level', 'intermediate')
        duration = metadata.get('duration_weeks', 8)
        prerequisites = metadata.get('prerequisites', [])

        llm_prompt = CURRICULUM_GENERATION_PROMPT.format(
            course_prompt=prompt,
            level=level,
            duration_weeks=duration,
            prerequisites=', '.join(prerequisites) if prerequisites else 'None',
            max_modules=self.max_modules
        )

        log.debug(f"Requesting course structure from LLM")
        response = self.llm.generate(llm_prompt, response_format='json')

        try:
            structure = json.loads(response)
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback structure
            structure = {
                'title': 'Generated Course',
                'description': prompt,
                'learning_objectives': ['To be defined'],
                'prerequisites': prerequisites,
                'module_topics': ['Introduction', 'Core Concepts', 'Advanced Topics']
            }

        return structure

    def _generate_modules(self, course_structure: Dict, metadata: Dict) -> List[Dict]:
        """
        Generate detailed module information.

        For each module topic, generates:
        - module_id: Unique identifier
        - title: Module title
        - description: Module description
        - learning_objectives: Module-specific objectives
        - estimated_hours: Time estimate
        - order: Sequential order
        """
        modules = []
        module_topics = course_structure.get('module_topics', [])[:self.max_modules]

        for idx, topic in enumerate(module_topics, 1):
            llm_prompt = MODULE_GENERATION_PROMPT.format(
                course_title=course_structure.get('title', 'Course'),
                module_topic=topic,
                module_number=idx,
                total_modules=len(module_topics),
                level=metadata.get('level', 'intermediate')
            )

            log.debug(f"Generating module {idx}: {topic}")
            response = self.llm.generate(llm_prompt, response_format='json')

            try:
                module_data = json.loads(response)
            except json.JSONDecodeError:
                log.warning(f"Failed to parse module data for {topic}, using defaults")
                module_data = {
                    'title': topic,
                    'description': f'Module covering {topic}',
                    'learning_objectives': [f'Understand {topic}'],
                    'estimated_hours': 8
                }

            module = {
                'module_id': f'module_{idx}',
                'title': module_data.get('title', topic),
                'description': module_data.get('description', ''),
                'learning_objectives': module_data.get('learning_objectives', []),
                'estimated_hours': module_data.get('estimated_hours', 8),
                'order': idx,
                'lessons': []  # Will be populated later
            }

            modules.append(module)

        return modules

    def _generate_lessons(
        self,
        module: Dict,
        course_structure: Dict,
        metadata: Dict
    ) -> List[Dict]:
        """
        Generate lessons for a module.

        For each lesson, generates:
        - lesson_id: Unique identifier
        - title: Lesson title
        - description: Brief description
        - learning_objectives: Lesson-specific objectives
        - content_type: Type of lesson (lecture, lab, assessment, etc.)
        - estimated_minutes: Time estimate
        - order: Sequential order within module
        """
        llm_prompt = LESSON_PLANNING_PROMPT.format(
            course_title=course_structure.get('title', 'Course'),
            module_title=module.get('title', 'Module'),
            module_objectives='\n'.join(f"- {obj}" for obj in module.get('learning_objectives', [])),
            max_lessons=self.max_lessons,
            level=metadata.get('level', 'intermediate')
        )

        log.debug(f"Generating lessons for module: {module.get('title')}")
        response = self.llm.generate(llm_prompt, response_format='json')

        try:
            lessons_data = json.loads(response)
            lesson_list = lessons_data.get('lessons', [])[:self.max_lessons]
        except json.JSONDecodeError:
            log.warning(f"Failed to parse lessons for module {module.get('title')}, using defaults")
            lesson_list = [
                {
                    'title': f"Lesson on {module.get('title')}",
                    'description': 'Introduction to the topic',
                    'content_type': 'lecture',
                    'estimated_minutes': 45
                }
            ]

        lessons = []
        for idx, lesson_data in enumerate(lesson_list, 1):
            lesson = {
                'lesson_id': f"{module.get('module_id')}_lesson_{idx}",
                'title': lesson_data.get('title', f'Lesson {idx}'),
                'description': lesson_data.get('description', ''),
                'learning_objectives': lesson_data.get('learning_objectives', []),
                'content_type': lesson_data.get('content_type', 'lecture'),
                'estimated_minutes': lesson_data.get('estimated_minutes', 45),
                'order': idx,
            }
            lessons.append(lesson)

        return lessons

    def validate_curriculum(self, curriculum: Dict) -> bool:
        """
        Validate that a curriculum has all required fields.

        Args:
            curriculum: Curriculum dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['course_key', 'title', 'modules']

        if not all(field in curriculum for field in required_fields):
            return False

        if not curriculum['modules']:
            return False

        for module in curriculum['modules']:
            if not all(field in module for field in ['module_id', 'title', 'lessons']):
                return False

            if not module['lessons']:
                return False

        return True
