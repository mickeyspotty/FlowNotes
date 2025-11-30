import json
import os
import shutil
from datetime import datetime
from typing import Dict, List

class NoteStorage:
    def __init__(self, base_dir: str = "notes_data"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_note(self, note_data: Dict) -> str:
        """
        Saves a note to a JSON file organized by subject.
        Returns the path to the saved file.
        """
        subject = note_data.get("subject", "Uncategorized")
        subject_dir = os.path.join(self.base_dir, subject)
        
        if not os.path.exists(subject_dir):
            os.makedirs(subject_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"note_{timestamp}.json"
        filepath = os.path.join(subject_dir, filename)

        # Add timestamp to note data if not present
        if "timestamp" not in note_data:
            note_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(note_data, f, indent=4, ensure_ascii=False)

        return filepath

    def get_subjects(self) -> List[str]:
        """Returns a list of all subjects (directories)."""
        if not os.path.exists(self.base_dir):
            return []
        return [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]

    def get_notes_for_subject(self, subject: str) -> List[Dict]:
        """Returns all notes for a given subject."""
        subject_dir = os.path.join(self.base_dir, subject)
        if not os.path.exists(subject_dir):
            return []

        notes = []
        for filename in os.listdir(subject_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(subject_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        note = json.load(f)
                        notes.append(note)
                except Exception as e:
                    print(f"Error loading note {filepath}: {e}")
        
        # Sort by timestamp descending (newest first)
        # Assuming timestamp format is consistent, otherwise might need parsing
        notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return notes

    def clear_all_notes(self):
        """Deletes all notes by removing the entire notes directory."""
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            os.makedirs(self.base_dir)

    def export_all_to_markdown(self, output_file: str):
        """Exports all notes to a single Markdown file."""
        subjects = self.get_subjects()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# FlowNotes\n\n")
            
            for subject in subjects:
                f.write(f"## {subject}\n\n")
                notes = self.get_notes_for_subject(subject)
                for note in notes:
                    f.write(f"### Note - {note.get('timestamp')}\n")
                    f.write(f"**Summary:**\n{note.get('summary')}\n\n")
                    f.write("**Key Points:**\n")
                    for point in note.get('keyPoints', []):
                        f.write(f"- {point}\n")
                    f.write("\n**Flashcards:**\n")
                    for card in note.get('flashcards', []):
                        f.write(f"- Q: {card.get('q')}\n  A: {card.get('a')}\n")
                    f.write("\n---\n\n")
