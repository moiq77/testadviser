from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import timedelta, timezone
import statistics
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import (
    Student, Question, Answer, AttemptCreate, AttemptResult,
    Institution, Major, AdminStats, Token
)
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")  # Store hashed password in env

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="RIASEC Career Test API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

# --- Security Functions ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Pydantic Models are now in models.py

from initial_data import SAMPLE_QUESTIONS, SAMPLE_INSTITUTIONS, SAMPLE_MAJORS

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

from utils import calculate_riasec_scores, get_top_axes

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
    question_docs = await db.questions.find({"is_active": True}).to_list(1000)
    questions = [Question(**q) for q in question_docs]
    
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
# --- Admin Routes ---

@api_router.post("/admin/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real app, you'd look up the user in a database
    if not ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=500, detail="Admin account is not configured")

    if form_data.username == ADMIN_USERNAME and verify_password(form_data.password, ADMIN_PASSWORD_HASH):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": ADMIN_USERNAME}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@api_router.get("/admin/stats", response_model=AdminStats, dependencies=[Depends(get_current_admin_user)])
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

@api_router.get("/admin/questions", response_model=List[Question], dependencies=[Depends(get_current_admin_user)])
async def get_admin_questions():
    """Get all questions for admin"""
    questions = await db.questions.find().to_list(1000)
    return [Question(**q) for q in questions]

@api_router.post("/admin/questions", response_model=Question, dependencies=[Depends(get_current_admin_user)])
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