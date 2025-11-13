"""
Prompt templates for LLM interactions.

All prompts used by the AI Engine services.
"""

# Curriculum Generation Prompts

CURRICULUM_GENERATION_PROMPT = """You are an expert curriculum designer. Generate a comprehensive curriculum for the following course:

Course Request: {course_prompt}

Course Parameters:
- Target Level: {level}
- Duration: {duration_weeks} weeks
- Prerequisites: {prerequisites}
- Maximum Modules: {max_modules}

Create a structured curriculum with:
1. Course title (concise and descriptive)
2. Course description (2-3 paragraphs)
3. Learning objectives (4-6 high-level objectives)
4. Prerequisites list
5. Module topics (list of {max_modules} major topics to cover)

Return your response as a JSON object with this exact structure:
{{
  "title": "Course Title Here",
  "description": "Detailed course description...",
  "learning_objectives": ["Objective 1", "Objective 2", ...],
  "prerequisites": ["Prerequisite 1", ...],
  "module_topics": ["Module 1 Topic", "Module 2 Topic", ...]
}}

Ensure the curriculum is appropriate for {level} level students and can realistically be completed in {duration_weeks} weeks.
"""

MODULE_GENERATION_PROMPT = """Generate detailed information for a course module.

Course: {course_title}
Module Topic: {module_topic}
Module Number: {module_number} of {total_modules}
Target Level: {level}

Provide:
1. Module title (concise, descriptive)
2. Module description (1-2 paragraphs explaining what students will learn)
3. Learning objectives (3-5 specific objectives for this module)
4. Estimated hours needed to complete this module

Return as JSON:
{{
  "title": "Module Title",
  "description": "Module description...",
  "learning_objectives": ["Objective 1", "Objective 2", ...],
  "estimated_hours": 8
}}
"""

LESSON_PLANNING_PROMPT = """Plan lessons for a course module.

Course: {course_title}
Module: {module_title}

Module Learning Objectives:
{module_objectives}

Generate {max_lessons} lessons that will help students achieve these objectives.

For each lesson, provide:
1. Title (specific and clear)
2. Description (1-2 sentences about what the lesson covers)
3. Learning objectives (1-3 specific things students will learn)
4. Content type (lecture, lab, discussion, assessment, project)
5. Estimated minutes to complete

Target level: {level}

Return as JSON:
{{
  "lessons": [
    {{
      "title": "Lesson Title",
      "description": "Brief description...",
      "learning_objectives": ["Objective 1", ...],
      "content_type": "lecture",
      "estimated_minutes": 45
    }},
    ...
  ]
}}

Ensure lessons build on each other logically and cover all module objectives.
"""

# Content Creation Prompts

LESSON_CONTENT_PROMPT = """Create engaging lesson content for an online course.

Course: {course_title}
Module: {module_title}
Lesson: {lesson_title}

Learning Objectives:
{lesson_objectives}

Target Audience: {difficulty_level} level students
Estimated Time: {estimated_minutes} minutes

Create comprehensive lesson content that includes:

## Introduction
- Hook to engage students
- Overview of what will be covered
- Why this topic matters

## Main Content
- Clear explanations with concrete examples
- Visual descriptions (describe diagrams or images that would help)
- Step-by-step explanations of complex concepts
- Real-world applications

## Examples
- 2-3 worked examples
- Practice problems for students to try

## Summary
- Recap of key points
- How this connects to broader course goals

## Key Takeaways
- Bulleted list of main points students should remember

Write in a clear, engaging style. Use analogies and examples to make complex concepts accessible.
"""

ASSESSMENT_GENERATION_PROMPT = """Generate assessment questions for a lesson.

Lesson: {lesson_title}

Learning Objectives:
{lesson_objectives}

Question Type: {question_type}
Difficulty: {difficulty}
Number of Questions: {num_questions}

For each question, provide:
1. Question text (clear and unambiguous)
2. Correct answer
3. For multiple choice: 4 options (including the correct one)
4. Explanation of the correct answer
5. Common misconceptions to address

Return as JSON:
{{
  "questions": [
    {{
      "text": "Question text here?",
      "type": "{question_type}",
      "difficulty": "{difficulty}",
      "correct_answer": "The correct answer",
      "options": ["Option A", "Option B", "Option C", "Option D"],  // for multiple choice
      "explanation": "Why this is the correct answer...",
      "misconceptions": ["Common mistake 1", "Common mistake 2"]
    }},
    ...
  ]
}}

Ensure questions:
- Directly assess the learning objectives
- Are at the appropriate {difficulty} level
- Have clear, unambiguous answers
- Avoid trick questions
- Test understanding, not just memorization
"""

EXAMPLE_GENERATION_PROMPT = """Generate {num_examples} examples to illustrate a concept.

Topic: {topic}
Context: {context}
Include Code Examples: {include_code}

For each example, provide:
1. Title/scenario
2. Description of the example
3. Key points it illustrates
4. Code snippet (if include_code is yes)

Return as JSON:
{{
  "examples": [
    {{
      "title": "Example Title",
      "description": "Detailed explanation of the example...",
      "key_points": ["Point 1", "Point 2"],
      "code": "code snippet here"  // only if include_code is yes
    }},
    ...
  ]
}}

Make examples:
- Concrete and relatable
- Build from simple to complex
- Include real-world scenarios
- Clear and easy to understand
"""

HINT_GENERATION_PROMPT = """Generate a hint for a student struggling with a question.

Question: {question_text}
Question Type: {question_type}
Student's Answer: {student_answer}
Hint Level: {hint_level} (1=subtle, 2=moderate, 3=direct)

Generate a {hint_level}-level hint that:
- Doesn't give away the answer directly (unless hint_level is 3)
- Guides the student's thinking
- Helps identify where they may have gone wrong
- Encourages them to try again

For hint level 1: Ask a leading question or point to a relevant concept
For hint level 2: Provide a partial explanation or break down the problem
For hint level 3: Give a more direct explanation while still encouraging independent thought

Write just the hint text (2-3 sentences), no JSON needed.
"""

# AI Tutor Prompts

AI_TUTOR_SYSTEM_PROMPT = """You are a helpful, patient AI tutor for an online learning platform.

Your role:
- Answer student questions clearly and concisely
- Adapt explanations to the student's level
- Encourage critical thinking rather than just giving answers
- Use analogies and examples to clarify concepts
- Be supportive and encouraging

Current context:
Course: {course_title}
Current Topic: {current_topic}
Student Level: {student_level}
Student Learning Style: {learning_style}

Guidelines:
- Keep responses concise (2-4 paragraphs unless more detail is requested)
- Use the Socratic method when appropriate
- Provide examples and analogies
- If you don't know something, be honest
- Encourage the student to think through problems
- Celebrate their progress and understanding

Respond to the student's question thoughtfully and helpfully.
"""

AI_TUTOR_RESPONSE_PROMPT = """Student Question: {student_message}

Conversation History:
{conversation_history}

Based on the context above, provide a helpful response to the student's question.

Remember to:
- Address their specific question
- Build on the previous conversation
- Provide clear explanations
- Use examples relevant to the course material
- Be encouraging and supportive

Response:"""

# Feedback Generation Prompts

ADAPTIVE_FEEDBACK_PROMPT = """Generate personalized feedback for a student's answer.

Question: {question_text}
Type: {question_type}
Correct Answer: {correct_answer}

Student's Answer: {student_answer}
Is Correct: {is_correct}
Attempt Number: {attempt_number}

Student Profile:
- Learning Style: {learning_style}
- Overall Performance: {overall_performance}%
- This Concept Status: {concept_status}

Generate encouraging, constructive feedback (2-4 sentences) that:
1. Acknowledges their effort
2. Confirms correctness or gently explains the mistake
3. Provides insight (not just "correct" or "incorrect")
4. Suggests next steps
5. Adapts tone to their learning style

For incorrect answers:
- If first attempt: Give a hint and encourage trying again
- If multiple attempts: Provide more detailed explanation
- Be supportive and focus on learning, not failure

For correct answers:
- Celebrate their success
- Reinforce the concept
- If they struggled: Acknowledge their persistence
- If they got it quickly: Suggest advancing

Write just the feedback text, no JSON needed.
"""
