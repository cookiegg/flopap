from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID

# --- Ingestion Schemas (Local -> Cloud) ---

class IngestionTranslationSchema(BaseModel):
    arxiv_id: str
    title_zh: Optional[str] = None
    summary_zh: Optional[str] = None
    model_name: str

class IngestionInterpretationSchema(BaseModel):
    arxiv_id: str
    interpretation: str
    language: str = "zh"
    model_name: str

class IngestionTTSSchema(BaseModel):
    arxiv_id: str
    file_path: str = Field(..., description="Relative path or filename of the audio file")
    file_size: int
    voice_model: str = "zh-CN-XiaoxiaoNeural"
    content_hash: Optional[str] = None

class IngestionPaperSchema(BaseModel):
    arxiv_id: str
    title: str
    summary: str
    authors: List[dict]
    categories: List[str]
    submitted_date: date
    updated_date: Optional[date] = None
    pdf_url: Optional[str] = None
    primary_category: Optional[str] = None
    source: str = "arxiv"

class IngestionRankingSchema(BaseModel):
    user_id: str
    pool_date: date
    source_key: str = "default"
    paper_ids: List[str] # arxiv_ids
    scores: List[float]

class IngestionEmbeddingSchema(BaseModel):
    arxiv_id: str
    model_name: str
    vector: List[float]

class IngestionBatchRequest(BaseModel):
    papers: List[IngestionPaperSchema] = []
    translations: List[IngestionTranslationSchema] = []
    interpretations: List[IngestionInterpretationSchema] = []
    tts_records: List[IngestionTTSSchema] = []
    rankings: List[IngestionRankingSchema] = []
    embeddings: List[IngestionEmbeddingSchema] = []

# --- Export Schemas (Cloud -> Local) ---

class UserProfileExport(BaseModel):
    user_id: str
    interested_categories: List[str]
    research_keywords: List[str]
    preference_description: Optional[str]
    onboarding_completed: bool

class UserFeedbackExport(BaseModel):
    user_id: str
    arxiv_id: str
    feedback_type: str

class ExportDataResponse(BaseModel):
    profiles: List[UserProfileExport]
    feedback: List[UserFeedbackExport]
    count_profiles: int
    count_feedback: int
