from typing import List, Dict, Any
from models import Answer, Question

def calculate_riasec_scores(answers: List[Answer], questions: List[Question]) -> Dict[str, float]:
    """Calculate RIASEC scores from answers"""
    axis_scores = {"R": [], "I": [], "A": [], "S": [], "E": [], "C": []}
    # Create a dictionary from the list of Question models for quick lookups
    question_map = {q.id: q for q in questions}

    for answer in answers:
        if answer.question_id in question_map:
            # Get the axis from the Question model
            axis = question_map[answer.question_id].axis
            axis_scores[axis].append(answer.value)

    # Calculate normalized scores (0-100)
    normalized_scores = {}
    for axis, scores in axis_scores.items():
        if scores:
            # Likert scale is 1-5. Normalizing to 0-100.
            # ((sum(scores) / len(scores)) - 1) / (5 - 1) * 100
            avg_score = sum(scores) / len(scores)
            normalized_scores[axis] = round((avg_score - 1) / 4 * 100, 1)
        else:
            normalized_scores[axis] = 0.0

    return normalized_scores

def get_top_axes(scores: Dict[str, float]) -> List[str]:
    """Get top 3 RIASEC axes from scores"""
    sorted_axes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [axis for axis, score in sorted_axes[:3]]