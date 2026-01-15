"""
论文内容API - 获取和保存论文相关内容
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_user_id
from app.models import Paper, PaperTranslation, PaperInterpretation, PaperInfographic, PaperTTS
from app.models.paper import PaperVisual
from app.services.user.content import save_user_infographic, save_user_visualization

router = APIRouter()


class PaperTranslationResponse(BaseModel):
    title_zh: str | None = None
    summary_zh: str | None = None


class PaperInterpretationResponse(BaseModel):
    interpretation: str
    language: str = "zh"


class PaperInfographicResponse(BaseModel):
    html_content: str


class PaperVisualResponse(BaseModel):
    image_data: str  # base64 data URL


class PaperTTSResponse(BaseModel):
    file_path: str
    file_size: int


# 新增请求模型
class InfographicSaveRequest(BaseModel):
    html_content: str
    checksum: Optional[str] = None


class VisualizationSaveRequest(BaseModel):
    image_data: str
    checksum: Optional[str] = None


@router.get("/{paper_id}/translation", response_model=PaperTranslationResponse)
def get_paper_translation(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文翻译"""
    translation = db.query(PaperTranslation).filter(
        PaperTranslation.paper_id == paper_id
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found"
        )
    
    return PaperTranslationResponse(
        title_zh=translation.title_zh,
        summary_zh=translation.summary_zh
    )


@router.get("/{paper_id}/interpretation", response_model=PaperInterpretationResponse)
def get_paper_interpretation(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文AI解读"""
    interpretation = db.query(PaperInterpretation).filter(
        PaperInterpretation.paper_id == paper_id
    ).first()
    
    if not interpretation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interpretation not found"
        )
    
    return PaperInterpretationResponse(
        interpretation=interpretation.interpretation,
        language=interpretation.language
    )


@router.get("/{paper_id}/infographic", response_model=PaperInfographicResponse)
def get_paper_infographic(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文信息图"""
    infographic = db.query(PaperInfographic).filter(
        PaperInfographic.paper_id == paper_id
    ).first()
    
    if not infographic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infographic not found"
        )
    
    return PaperInfographicResponse(
        html_content=infographic.html_content
    )


@router.get("/{paper_id}/visual", response_model=PaperVisualResponse)
def get_paper_visual(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文可视化图片"""
    visual = db.query(PaperVisual).filter(
        PaperVisual.paper_id == paper_id
    ).first()
    
    if not visual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visual not found"
        )
    
    return PaperVisualResponse(
        image_data=visual.image_data
    )


@router.get("/{paper_id}/tts", response_model=PaperTTSResponse)
def get_paper_tts(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文TTS音频"""
    tts = db.query(PaperTTS).filter(
        PaperTTS.paper_id == paper_id
    ).first()
    
    if not tts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TTS not found"
        )
    
    return PaperTTSResponse(
        file_path=tts.file_path,
        file_size=tts.file_size
    )


@router.get("/{paper_id}/content-status")
def get_paper_content_status(
    paper_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取论文内容生成状态"""
    # 检查各种内容是否存在
    translation_exists = db.query(PaperTranslation).filter(
        PaperTranslation.paper_id == paper_id
    ).first() is not None
    
    interpretation_exists = db.query(PaperInterpretation).filter(
        PaperInterpretation.paper_id == paper_id
    ).first() is not None
    
    infographic_exists = db.query(PaperInfographic).filter(
        PaperInfographic.paper_id == paper_id
    ).first() is not None
    
    visual_exists = db.query(PaperVisual).filter(
        PaperVisual.paper_id == paper_id
    ).first() is not None
    
    tts_exists = db.query(PaperTTS).filter(
        PaperTTS.paper_id == paper_id
    ).first() is not None
    
    return {
        "paper_id": str(paper_id),
        "content_status": {
            "translation": translation_exists,
            "interpretation": interpretation_exists,
            "infographic": infographic_exists,
            "visual": visual_exists,
            "tts": tts_exists
        }
    }


@router.post("/{paper_id}/infographic")
def save_infographic(
    paper_id: UUID,
    request: InfographicSaveRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """保存论文信息图"""
    # 验证论文存在
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    infographic_id = save_user_infographic(
        db=db,
        paper_id=paper_id,
        html_content=request.html_content,
        checksum=request.checksum
    )
    
    if not infographic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content or integrity check failed"
        )
    
    return {"id": str(infographic_id), "message": "Infographic saved successfully"}


@router.post("/{paper_id}/visual")
def save_visualization(
    paper_id: UUID,
    request: VisualizationSaveRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """保存论文可视化图"""
    # 验证论文存在
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    visual_id = save_user_visualization(
        db=db,
        paper_id=paper_id,
        image_data=request.image_data,
        checksum=request.checksum
    )
    
    if not visual_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content or integrity check failed"
        )
    
    return {"id": str(visual_id), "message": "Visualization saved successfully"}
