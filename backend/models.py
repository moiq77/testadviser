from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime

# --- Pydantic Models ---

class Token(BaseModel):
    access_token: str
    token_type: str

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    branch: str  # scientific, literary, arts
    governorate: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text_ar: str
    axis: str  # R, I, A, S, E, C
    is_active: bool = True

class Answer(BaseModel):
    question_id: str
    value: int  # 1-5 Likert scale

class AttemptCreate(BaseModel):
    student: Student
    answers: List[Answer]

class AttemptResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student: Student
    scores: Dict[str, float]  # R, I, A, S, E, C percentages
    top_axes: List[str]  # Top 3 axes
    recommendations: List[Dict[str, Any]]
    completed_at: datetime

class Institution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name_ar: str
    city: str
    governorate: str
    type: str  # university, institute, polytechnic

class Major(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    institution_id: str
    college_name_ar: str
    major_name_ar: str
    branch_eligibility: List[str]  # scientific, literary, arts
    study_mode: str  # morning, evening, both
    riasec_match: List[str]  # Primary RIASEC axes

class AdminStats(BaseModel):
    total_attempts: int
    total_students: int
    branch_distribution: Dict[str, int]
    popular_axes: Dict[str, int]