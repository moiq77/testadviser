from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
import statistics

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="RIASEC Career Test API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
ADMIN_TOKEN = "admin123"  # Simple token for admin panel

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return credentials

# Pydantic Models
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

# Sample data initialization
SAMPLE_QUESTIONS = [
    {"text_ar": "أستمتع بإصلاح أو تركيب الأشياء الميكانيكية", "axis": "R"},
    {"text_ar": "أفضل العمل العملي باستخدام الأدوات", "axis": "R"},
    {"text_ar": "أحب العمل في الورش والمختبرات", "axis": "R"},
    {"text_ar": "أستمتع بالأعمال اليدوية والحرفية", "axis": "R"},
    {"text_ar": "أفضل العمل في البيئة الخارجية", "axis": "R"},
    {"text_ar": "أستمتع بحل المسائل المعقدة والمنطقية", "axis": "I"},
    {"text_ar": "أحب إجراء التجارب العلمية", "axis": "I"},
    {"text_ar": "أستمتع بتحليل البيانات والمعلومات", "axis": "I"},
    {"text_ar": "أحب البحث والدراسة المتعمقة", "axis": "I"},
    {"text_ar": "أستمتع بفهم كيفية عمل الأشياء", "axis": "I"},
    {"text_ar": "أحب الرسم والتصميم الفني", "axis": "A"},
    {"text_ar": "أستمتع بالكتابة الإبداعية", "axis": "A"},
    {"text_ar": "أحب الموسيقى والفنون الأدائية", "axis": "A"},
    {"text_ar": "أستمتع بابتكار أفكار جديدة وأصيلة", "axis": "A"},
    {"text_ar": "أحب التعبير عن نفسي بطرق إبداعية", "axis": "A"},
    {"text_ar": "أستمد طاقتي من مساعدة الآخرين", "axis": "S"},
    {"text_ar": "أحب التدريس والإرشاد", "axis": "S"},
    {"text_ar": "أستمتع بالعمل مع الأطفال", "axis": "S"},
    {"text_ar": "أحب المشاركة في الأعمال التطوعية", "axis": "S"},
    {"text_ar": "أستمتع بحل مشاكل الناس", "axis": "S"},
    {"text_ar": "أحب قيادة الفرق واتخاذ القرارات", "axis": "E"},
    {"text_ar": "أستمتع بالتفاوض والإقناع", "axis": "E"},
    {"text_ar": "أحب تنظيم الفعاليات والمشاريع", "axis": "E"},
    {"text_ar": "أستمتع بإدارة الأعمال", "axis": "E"},
    {"text_ar": "أحب المخاطرة المحسوبة في العمل", "axis": "E"},
    {"text_ar": "أفضل الأعمال المنظمة والروتينية", "axis": "C"},
    {"text_ar": "أستمتع بترتيب البيانات والجداول", "axis": "C"},
    {"text_ar": "أحب العمل بالأرقام والحسابات", "axis": "C"},
    {"text_ar": "أستمتع بالأعمال المكتبية والإدارية", "axis": "C"},
    {"text_ar": "أحب اتباع القواعد والإجراءات", "axis": "C"}
]

SAMPLE_INSTITUTIONS = [
    {"name_ar": "جامعة بغداد", "city": "بغداد", "governorate": "بغداد", "type": "university"},
    {"name_ar": "جامعة البصرة", "city": "البصرة", "governorate": "البصرة", "type": "university"},
    {"name_ar": "جامعة الموصل", "city": "الموصل", "governorate": "نينوى", "type": "university"},
    {"name_ar": "الجامعة التكنولوجية", "city": "بغداد", "governorate": "بغداد", "type": "university"},
    {"name_ar": "معهد التدريب النفطي", "city": "كركوك", "governorate": "كركوك", "type": "institute"}
]

SAMPLE_MAJORS = [
    {"college_name_ar": "كلية الهندسة", "major_name_ar": "هندسة ميكانيكية", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["R", "I"]},
    {"college_name_ar": "كلية الهندسة", "major_name_ar": "هندسة مدنية", "branch_eligibility": ["scientific"], "study_mode": "both", "riasec_match": ["R", "I"]},
    {"college_name_ar": "كلية الطب", "major_name_ar": "الطب العام", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["I", "S"]},
    {"college_name_ar": "كلية الصيدلة", "major_name_ar": "الصيدلة", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["I", "S"]},
    {"college_name_ar": "كلية علوم الحاسوب", "major_name_ar": "علوم الحاسوب", "branch_eligibility": ["scientific"], "study_mode": "both", "riasec_match": ["I", "C"]},
    {"college_name_ar": "كلية الفنون الجميلة", "major_name_ar": "التصميم", "branch_eligibility": ["arts", "literary"], "study_mode": "morning", "riasec_match": ["A"]},
    {"college_name_ar": "كلية التربية", "major_name_ar": "التربية", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["S"]},
    {"college_name_ar": "كلية الإدارة والاقتصاد", "major_name_ar": "إدارة الأعمال", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["E", "C"]},
    {"college_name_ar": "كلية الإدارة والاقتصاد", "major_name_ar": "المحاسبة", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["C"]},
    {"college_name_ar": "كلية الآداب", "major_name_ar": "اللغة العربية", "branch_eligibility": ["literary"], "study_mode": "both", "riasec_match": ["A", "S"]},
    {"college_name_ar": "كلية الإعلام", "major_name_ar": "الصحافة", "branch_eligibility": ["literary"], "study_mode": "morning", "riasec_match": ["A", "E"]},
    {"college_name_ar": "كلية التمريض", "major_name_ar": "التمريض", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["S", "I"]}
]

# Startup event to initialize sample data
@app.on_event("startup")
async def startup_event():
    # Initialize questions if collection is empty
    if await db.questions.count_documents({}) == 0:
        questions = [Question(**q).dict() for q in SAMPLE_QUESTIONS]
        await db.questions.insert_many(questions)
        logger.info("Initialized sample questions")
    
    # Initialize institutions
    if await db.institutions.count_documents({}) == 0:
        institutions = [Institution(**inst).dict() for inst in SAMPLE_INSTITUTIONS]
        await db.institutions.insert_many(institutions)
        logger.info("Initialized sample institutions")
    
    # Initialize majors with institution references
    if await db.majors.count_documents({}) == 0:
        institutions = await db.institutions.find().to_list(1000)
        majors = []
        for major_data in SAMPLE_MAJORS:
            # Assign to Baghdad University by default, or first available
            institution = next((inst for inst in institutions if "بغداد" in inst["name_ar"]), institutions[0])
            major = Major(institution_id=institution["id"], **major_data)
            majors.append(major.dict())
        await db.majors.insert_many(majors)
        logger.info("Initialized sample majors")

# RIASEC calculation functions
def calculate_riasec_scores(answers: List[Answer], questions: List[Question]) -> Dict[str, float]:
    """Calculate RIASEC scores from answers"""
    axis_scores = {"R": [], "I": [], "A": [], "S": [], "E": [], "C": []}
    question_map = {q["id"]: q for q in questions}
    
    for answer in answers:
        if answer.question_id in question_map:
            axis = question_map[answer.question_id]["axis"]
            axis_scores[axis].append(answer.value)
    
    # Calculate normalized scores (0-100)
    normalized_scores = {}
    for axis, scores in axis_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            normalized_scores[axis] = round((avg_score - 1) / 4 * 100, 1)
        else:
            normalized_scores[axis] = 0.0
    
    return normalized_scores

def get_top_axes(scores: Dict[str, float]) -> List[str]:
    """Get top 3 RIASEC axes"""
    sorted_axes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [axis for axis, score in sorted_axes[:3]]

def get_recommendations(top_axes: List[str], student_branch: str) -> List[Dict[str, Any]]:
    """Get major recommendations based on RIASEC scores and student branch"""
    # Query majors that match the student's branch and RIASEC profile
    return []  # Will be implemented with actual database query

# API Routes
@api_router.get("/")
async def root():
    return {"message": "RIASEC Career Test API", "version": "1.0.0"}

@api_router.get("/questions", response_model=List[Question])
async def get_questions():
    """Get all active questions for the test"""
    questions = await db.questions.find({"is_active": True}).to_list(1000)
    return [Question(**q) for q in questions]

@api_router.post("/attempt", response_model=AttemptResult)
async def submit_attempt(attempt: AttemptCreate):
    """Submit test attempt and get results"""
    # Get questions for calculation
    questions = await db.questions.find({"is_active": True}).to_list(1000)
    
    # Calculate RIASEC scores
    scores = calculate_riasec_scores(attempt.answers, questions)
    top_axes = get_top_axes(scores)
    
    # Get recommendations based on student branch and top axes
    query = {
        "branch_eligibility": {"$in": [attempt.student.branch]},
        "riasec_match": {"$in": top_axes[:2]}  # Match top 2 axes
    }
    
    majors = await db.majors.find(query).to_list(50)
    institutions = await db.institutions.find().to_list(1000)
    
    # Build institution map for lookup
    inst_map = {inst["id"]: inst for inst in institutions}
    
    recommendations = []
    for major in majors:
        if major["institution_id"] in inst_map:
            institution = inst_map[major["institution_id"]]
            recommendations.append({
                "major": major["major_name_ar"],
                "college": major["college_name_ar"],
                "institution": institution["name_ar"],
                "city": institution["city"],
                "governorate": institution["governorate"],
                "study_mode": major["study_mode"],
                "match_score": len([axis for axis in major["riasec_match"] if axis in top_axes])
            })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Create result
    result = AttemptResult(
        student=attempt.student,
        scores=scores,
        top_axes=top_axes,
        recommendations=recommendations[:20],  # Top 20 recommendations
        completed_at=datetime.now(timezone.utc)
    )
    
    # Save to database
    await db.attempts.insert_one(result.dict())
    
    return result

@api_router.get("/attempt/{attempt_id}", response_model=AttemptResult)
async def get_attempt(attempt_id: str):
    """Get attempt results by ID"""
    attempt = await db.attempts.find_one({"id": attempt_id})
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return AttemptResult(**attempt)

# Admin routes
@api_router.get("/admin/stats", response_model=AdminStats, dependencies=[Depends(verify_admin_token)])
async def get_admin_stats():
    """Get admin statistics"""
    total_attempts = await db.attempts.count_documents({})
    
    # Get unique students count
    student_ids = await db.attempts.distinct("student.id")
    total_students = len(student_ids)
    
    # Branch distribution
    pipeline = [
        {"$group": {"_id": "$student.branch", "count": {"$sum": 1}}}
    ]
    branch_results = await db.attempts.aggregate(pipeline).to_list(10)
    branch_distribution = {result["_id"]: result["count"] for result in branch_results}
    
    # Popular axes (simplified)
    popular_axes = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}  # Placeholder
    
    return AdminStats(
        total_attempts=total_attempts,
        total_students=total_students,
        branch_distribution=branch_distribution,
        popular_axes=popular_axes
    )

@api_router.get("/admin/questions", response_model=List[Question], dependencies=[Depends(verify_admin_token)])
async def get_admin_questions():
    """Get all questions for admin"""
    questions = await db.questions.find().to_list(1000)
    return [Question(**q) for q in questions]

@api_router.post("/admin/questions", response_model=Question, dependencies=[Depends(verify_admin_token)])
async def create_question(question: Question):
    """Create new question"""
    await db.questions.insert_one(question.dict())
    return question

@api_router.get("/institutions", response_model=List[Institution])
async def get_institutions():
    """Get all institutions"""
    institutions = await db.institutions.find().to_list(1000)
    return [Institution(**inst) for inst in institutions]

@api_router.get("/majors", response_model=List[Major])
async def get_majors(branch: Optional[str] = None, city: Optional[str] = None):
    """Get majors with optional filtering"""
    query = {}
    if branch:
        query["branch_eligibility"] = {"$in": [branch]}
    
    majors = await db.majors.find(query).to_list(1000)
    
    # If city filter is provided, also filter by institution city
    if city:
        institutions = await db.institutions.find({"city": city}).to_list(1000)
        inst_ids = [inst["id"] for inst in institutions]
        majors = [major for major in majors if major["institution_id"] in inst_ids]
    
    return [Major(**major) for major in majors]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()