"""
API Guide d'Identité Visuelle
Assistant IA pour le guide de marque Elna Tech
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.services.guide.visual_identity import guide_service

router = APIRouter(prefix="/guide", tags=["🎨 Guide Marque"])


class QuestionRequest(BaseModel):
    question: str


class FAQResponse(BaseModel):
    question: str
    reponse: str


@router.get("")
def get_guide_info():
    """Information sur le guide d'identité visuelle"""
    return {
        "title": "Guide d'Identité Visuelle Elna Tech",
        "description": "Assistant IA pour questions sur la charte graphique",
        "categories": [
            "Logo",
            "Couleurs",
            "Typographie",
            "Images",
            "Composants UI",
            "Espace",
            "Animations"
        ],
        "endpoints": {
            "faq": "/api/guide/faq",
            "colors": "/api/guide/colors",
            "component": "/api/guide/component/{name}",
            "ask": "/api/guide/ask"
        }
    }


@router.get("/faq", response_model=List[FAQResponse])
def get_faq():
    """Questions fréquentes sur le guide"""
    return guide_service.get_all_faq()


@router.get("/colors")
def get_colors():
    """Palette de couleurs complète"""
    return guide_service.get_color_palette()


@router.get("/component/{component_name}")
def get_component_style(component_name: str):
    """Styles d'un composant spécifique"""
    return guide_service.get_component_styles(component_name)


@router.post("/ask")
def ask_question(request: QuestionRequest):
    """Pose une question à l'assistant IA du guide"""
    result = guide_service.get_answer(request.question)
    return {
        "question": request.question,
        "answer": result["answer"],
        "source": result["source"]
    }
