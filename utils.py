import os
import yaml
from typing import List
from schema import QuestionRecord


def load_prompt(filename):
    """Load a prompt from a YAML file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "prompts", filename)

    try:
        with open(prompt_path, "r") as file:
            prompt_data = yaml.safe_load(file)
            return prompt_data.get("instructions", "")
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading prompt file {filename}: {e}")
        return ""


def load_questions(filename) -> List[QuestionRecord]:
    import yaml

    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "questions", filename)

    try:
        with open(questions_path, "r", encoding="utf-8") as f:
            raw_questions = yaml.safe_load(f).get("questions", [])
        return [QuestionRecord(**q) for q in raw_questions]
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading questions file {filename}: {e}")
        return ""
