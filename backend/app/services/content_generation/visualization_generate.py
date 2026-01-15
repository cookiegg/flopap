"""Visual explanation generation using Google Gemini"""
from __future__ import annotations

import os
import base64
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.models import Paper
from app.models.paper import PaperVisual


def get_cached_visual(db: Session, paper_id) -> Optional[str]:
    """Get cached visual from database"""
    visual = db.query(PaperVisual).filter(PaperVisual.paper_id == paper_id).first()
    if visual:
        logger.info(f"Using cached visual for paper {paper_id}")
        return visual.image_data
    return None


def save_visual(db: Session, paper_id, image_data: str, model_name: str = "gemini-3-pro-image-preview"):
    """Save generated visual to database"""
    try:
        visual = PaperVisual(
            paper_id=paper_id,
            image_data=image_data,
            model_name=model_name
        )
        db.add(visual)
        db.commit()
        logger.success(f"Saved visual for paper {paper_id}")
    except Exception as e:
        logger.error(f"Failed to save visual: {e}")
        db.rollback()


def generate_visual_explanation(db: Session, paper: Paper) -> Optional[str]:
    """
    Generate visual explanation image using Google Gemini 3 Pro Image Preview
    
    Args:
        db: Database session
        paper: Paper object with title and summary
        
    Returns:
        Base64 encoded image data (data URL format)
    """
    # Check cache first
    cached = get_cached_visual(db, paper.id)
    if cached:
        return cached
    
    try:
        from google import genai
        
        # Configure API
        api_key = os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            logger.error("GOOGLE_GENAI_API_KEY not configured")
            return None
        
        client = genai.Client(api_key=api_key)
        
        # Create prompt for visual explanation (in English for better results)
        prompt = f"""
Create an educational infographic to explain this academic paper in simple terms:

Paper Title: {paper.title}

Paper Abstract: {paper.summary[:600]}

Requirements:
1. Simple diagrams showing core concepts
2. Clear method/approach flowchart with step-by-step process
3. Key results visualization (charts or comparisons)
4. Use English labels, concise and easy to understand
5. Style: Clean, academic but accessible, like a science magazine illustration
6. Colors: Bright and clear, well-coordinated palette
7. Layout: Well-organized with clear sections

Generate a complete infographic.
"""
        
        logger.info(f"Generating visual for paper {paper.arxiv_id}")
        
        # Generate image using Gemini 3 Pro Image Preview
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt],
        )
        
        # Extract image from response (correct structure with None checks)
        if not hasattr(response, 'candidates') or not response.candidates:
            logger.warning(f"No candidates in response for paper {paper.arxiv_id}")
            return None
            
        for candidate in response.candidates:
            if not hasattr(candidate, 'content') or not hasattr(candidate.content, 'parts'):
                continue
                
            for part in candidate.content.parts:
                # Check for inline_data and ensure it's not None
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    # Convert to base64 data URL
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                    data_url = f"data:{mime_type};base64,{base64_data}"
                    
                    logger.success(f"Generated visual image for paper {paper.arxiv_id}, size: {len(image_bytes)} bytes")
                    
                    # Save to database
                    save_visual(db, paper.id, data_url)
                    
                    # Save to backend/data/fig/ directory
                    try:
                        import os
                        from pathlib import Path
                        from datetime import datetime
                        
                        fig_dir = Path(__file__).parent.parent.parent / "data" / "fig"
                        fig_dir.mkdir(parents=True, exist_ok=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{paper.arxiv_id}_{timestamp}.png"
                        filepath = fig_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(image_bytes)
                        
                        logger.info(f"Saved visual to {filepath}")
                    except Exception as e:
                        logger.warning(f"Failed to save visual to file: {e}")
                    
                    return data_url
        
        logger.warning(f"No image generated for paper {paper.arxiv_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to generate visual explanation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def generate_visual_with_imagen(paper: Paper) -> Optional[str]:
    """
    Generate visual using Imagen API (when available)
    
    This requires the Imagen API which is separate from Gemini
    """
    try:
        # Imagen API endpoint
        import requests
        
        api_key = os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            return None
        
        # Create detailed prompt
        prompt = f"""
Educational infographic for academic paper:

Title: {paper.title}

Create a visual explanation with:
- Core concepts illustrated with simple diagrams
- Method flowchart showing the approach
- Key results with charts or comparisons
- Chinese text labels (简体中文)

Style: Clean academic illustration, bright colors, well-organized layout
"""
        
        # Imagen API call (placeholder)
        # url = "https://generativelanguage.googleapis.com/v1/models/imagen-3.0-generate-001:predict"
        # headers = {"Authorization": f"Bearer {api_key}"}
        # data = {"prompt": prompt, "num_images": 1}
        # response = requests.post(url, headers=headers, json=data)
        
        logger.info(f"Imagen generation requested for {paper.arxiv_id}")
        return None
        
    except Exception as e:
        logger.error(f"Imagen generation failed: {e}")
        return None

