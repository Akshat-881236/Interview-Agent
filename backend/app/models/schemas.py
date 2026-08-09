from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Authentication Schemas
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str

# Enhanced Emotion & Proctor Telemetry Schema
class PerceptionMetrics(BaseModel):
    eye_contact_score: float = Field(default=0.85, description="Score 0.0 to 1.0 based on camera gaze")
    confidence_index: float = Field(default=0.80, description="Score 0.0 to 1.0 based on voice pitch & pauses")
    speech_cadence: float = Field(default=130.0, description="Words per minute")
    face_count: int = Field(default=1, description="Number of detected faces in camera frame")
    looking_left: bool = Field(default=False, description="Candidate looking off-screen to the left")
    looking_right: bool = Field(default=False, description="Candidate looking off-screen to the right")
    looking_away: bool = Field(default=False, description="Flagged if candidate is looking away off-screen")
    unnecessary_emotion: bool = Field(default=False, description="Flagged if unnecessary smiling, crying, or emotional distraction detected")
    emotion_type: Optional[str] = Field(default="neutral", description="Detected emotion: neutral, smiling, crying, surprised, distracted")
    suspicious_flag: bool = Field(default=False, description="Flagged if suspicious cheating action detected")
    violation_count: int = Field(default=0, description="Cumulative proctoring violation count (0 to 2)")
    violation_reason: Optional[str] = Field(default=None, description="Reason for proctoring flag")

# Interview Schemas
class StartRequest(BaseModel):
    candidate_id: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str
    perception_metrics: Optional[PerceptionMetrics] = None
    debate_mode: bool = False

# Pass 1 LLM Summary Output Model
class Pass1SummaryModel(BaseModel):
    technical_summary: str
    key_entities_mentioned: List[str]
    concept_depth_rating: float  # 0.0 to 1.0
    detected_hedging_or_hesitation: bool

# Pass 2 LLM Final Spoken Response Model
class Pass2ResponseModel(BaseModel):
    internal_thought_process: str
    action: str  # ASK_NEW_TOPIC | ASK_FOLLOW_UP | DEBATE_CHALLENGE | CONCLUDE_INTERVIEW | WARN_PROCTOR_VIOLATION | CANCEL_INTERVIEW
    target_curriculum_day: int
    spoken_response: str
