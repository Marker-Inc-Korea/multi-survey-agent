# schema.py

from dataclasses import dataclass, field
from typing import List, Optional, Literal


@dataclass
class QuestionRecord:
    id: str
    text: str
    type: Optional[str] = None
    options: Optional[List[str]] = None
    condition: Optional[dict] = None
    answer: Optional[str] = None
    status: Literal["unasked", "answered", "skipped"] = "unasked"


@dataclass
class SurveyState:
    questions: List[QuestionRecord] = field(default_factory=list)
    current_index: int = 0

    def get_current_question(self) -> Optional[QuestionRecord]:
        # 조건이 불충족된 질문은 자동 건너뜀
        while self.current_index < len(self.questions):
            q = self.questions[self.current_index]
            if self._is_question_applicable(q):
                return q
            else:
                q.status = "skipped"
                self.current_index += 1
        return None

    def _is_question_applicable(self, question: QuestionRecord) -> bool:
        if not question.condition:
            return True
        target_id = question.condition.get("question")
        expected_answer = question.condition.get("equals")

        if target_id and expected_answer is not None:
            for q in self.questions:
                if q.id == target_id:
                    return q.answer == expected_answer
        return True  # fallback to asking if condition malformed

    def record_answer(self, answer: str):
        question = self.get_current_question()
        if question:
            question.answer = answer
            question.status = "answered"
            self.current_index += 1

    def skip_question(self):
        question = self.get_current_question()
        if question:
            question.status = "skipped"
            self.current_index += 1

    def summarize(self) -> str:
        answered = []
        skipped = []
        unasked = []

        for q in self.questions:
            line = f"- {q.id} ({q.text})"
            if q.options:
                line += f"\n  Options: {q.options}"

            if q.status == "answered":
                answered.append(f"{line}\n  Answer: {q.answer}")
            elif q.status == "skipped":
                skipped.append(line)
            elif q.status == "unasked":
                unasked.append(line)

        summary = ["Survey Progress Summary:"]

        if answered:
            summary.append("\nAnswered:")
            summary.extend(answered)
        if skipped:
            summary.append("\nSkipped:")
            summary.extend(skipped)

        current = self.get_current_question()
        if current:
            summary.append(
                f"\nAsk the following question:\n- {current.id} ({current.text})"
            )
            if current.options:
                summary.append(f"  Options: {current.options}")

        if not answered and not skipped:
            summary.append("\nNo responses yet.")

        return "\n".join(summary)
