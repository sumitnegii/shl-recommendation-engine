from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging
from recommender import SHLRecommender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SHL Assessment Recommender AI",
    description="AI-powered recommendation engine for SHL assessments",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000",
    "https://shl-recommendation-engine-xnyz-o40477s1p-sumitnegiis-projects.vercel.app"],  # ports
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

#  recommender here initia
try:
    recommender = SHLRecommender(csv_path="assessments.csv")
    logger.info("Recommender system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize recommender: {e}")
    raise e

class UserRequest(BaseModel):
    job_role: str
    skills: str
    experience: Optional[int] = None
    goal: Optional[str] = None

    @validator('job_role')
    def job_role_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Job role cannot be empty')
        return v.strip()

    @validator('skills')
    def skills_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Skills cannot be empty')
        return v.strip()

    @validator('experience')
    def validate_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError('Experience should be between 0 and 50 years')
        return v

class RecommendationResponse(BaseModel):
    name: str
    description: str
    domain: str
    level: str
    score: float

class RecommendationResult(BaseModel):
    recommendations: List[RecommendationResponse]
    total_count: int

@app.get("/")
async def root():
    return {
        "message": "SHL Assessment Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "recommend": "POST /recommend - Get assessment recommendations"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SHL Recommender"}

@app.post("/recommend", response_model=RecommendationResult)
async def recommend(req: UserRequest):
    try:
        logger.info(f"Received recommendation request for job role: {req.job_role}")
        
        user_input = req.dict()
        results = recommender.recommend(user_input, top_k=5)
        
        logger.info(f"Generated {len(results)} recommendations")
        
        return {
            "recommendations": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )