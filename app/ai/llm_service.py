import json
import os
from typing import Dict, List, Optional
import google.generativeai as genai

class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        if api_key:
            self.configure_api(api_key)

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self.configure_api(api_key)

    def configure_api(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def calculate_flashcard_count(self, text: str) -> int:
        """
        Calculate the number of flashcards based on text length.
        - Short text (< 200 words): 2 flashcards
        - Medium text (200-500 words): 4 flashcards
        - Long text (500-1000 words): 6 flashcards
        - Very long text (> 1000 words): 8 flashcards
        """
        word_count = len(text.split())
        
        if word_count < 200:
            return 2
        elif word_count < 500:
            return 4
        elif word_count < 1000:
            return 6
        else:
            return 8

    def generate_more_flashcards(self, summary: str, key_points: List[str], count: int = 4) -> List[Dict]:
        """
        Generate additional flashcards based on existing summary and key points.
        """
        if not self.model:
            return []
        
        try:
            # Create context from summary and key points
            context = f"Summary: {summary}\n\nKey Points:\n"
            for point in key_points:
                context += f"- {point}\n"
            
            prompt = f"""Based on the following content, generate {count} NEW flashcard questions that are different from any previous questions.
Focus on testing understanding, application, and critical thinking.

{context}

Return ONLY a JSON array of flashcards in this exact format:
[
  {{"q": "question here", "a": "answer here"}},
  {{"q": "question here", "a": "answer here"}}
]"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            flashcards = json.loads(result_text)
            
            return flashcards
        except Exception as e:
            print(f"Error generating more flashcards: {e}")
            return []

    def process_text(self, text: str, current_subject: Optional[str] = None, existing_subjects: List[str] = None) -> Dict:
        if not self.model:
            return {"subject": "Error", "summary": "API key not configured.", "action": "error"}

        try:
            # Calculate dynamic flashcard count
            flashcard_count = self.calculate_flashcard_count(text)
            
            existing_subjects_str = ", ".join(existing_subjects) if existing_subjects else "None"
            current_subject_str = current_subject if current_subject else "None"

            prompt = f"""Analyze the following text.
Current Subject Context: "{current_subject_str}"
Existing Subjects: {existing_subjects_str}

Tasks:
1. Determine if the text belongs to the Current Subject.
2. If NOT, determine if it belongs to one of the Existing Subjects.
3. If NOT, suggest a new concise Subject Name.
4. Provide a concise summary.
5. Extract key points.
6. Generate {flashcard_count} flashcards.

Text:
{text}

Return JSON:
{{
  "action": "keep" (if matches current) OR "move" (if matches existing) OR "create" (if new),
  "subject": "The determined subject name",
  "reason": "Short reason for the action (e.g. 'Matches current topic', 'Better fits History', 'New topic detected')",
  "summary": "summary here",
  "keyPoints": ["point1", ...],
  "flashcards": [{{"q": "...", "a": "..."}}, ...]
}}
"""
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Sometimes the model wraps JSON in markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            result = json.loads(result_text)
            return result
        except Exception as e:
            print(f"Error processing text: {e}")
            return {
                "subject": "Error",
                "summary": f"Failed to process: {str(e)}",
                "keyPoints": [],
                "flashcards": [],
                "action": "error"
            }
