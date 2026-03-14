"""
Elna Academy - Formation Personnalisée
Parcours adaptés aux lacunes réelles de l'entrepreneur
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

router = APIRouter(prefix="/academy", tags=["🎓 Elna Academy"])


class Level(str, Enum):
    debutant = "debutant"
    intermediaire = "intermediaire"
    avance = "avance"


class Category(str, Enum):
    finance = "finance"
    marketing = "marketing"
    gestion = "gestion"
    digital = "digital"
    conformite = "conformite"


# Contenu des formations
COURSES = [
    {
        "id": 1,
        "title": "Maîtriser la Gestion de Trésorerie",
        "description": "Apprenez à gérer votre trésorerie au quotidien et à anticiper les besoins de liquidités",
        "category": "finance",
        "level": "debutant",
        "duration": "45 min",
        "modules": 5,
        "icon": "💰"
    },
    {
        "id": 2,
        "title": "Comprendre ses États Financiers",
        "description": "Lire et interpréter un bilan, un compte de résultat et un tableau de flux",
        "category": "finance",
        "level": "intermediaire",
        "duration": "1h30",
        "modules": 8,
        "icon": "📊"
    },
    {
        "id": 3,
        "title": "Stratégie de Prix et Marges",
        "description": "Comment fixer vos prix pour être rentable tout en restant compétitif",
        "category": "finance",
        "level": "avance",
        "duration": "1h",
        "modules": 6,
        "icon": "🏷️"
    },
    {
        "id": 4,
        "title": "Marketing Digital pour PME",
        "description": "Les bases du marketing digital pour développer votre visibilité en ligne",
        "category": "marketing",
        "level": "debutant",
        "duration": "1h",
        "modules": 6,
        "icon": "📱"
    },
    {
        "id": 5,
        "title": "Fidéliser ses Clients",
        "description": "Stratégies éprouvées pour garder vos clients et augmenter leur valeur",
        "category": "marketing",
        "level": "intermediaire",
        "duration": "45 min",
        "modules": 4,
        "icon": "❤️"
    },
    {
        "id": 6,
        "title": "Gestion d'Entreprise",
        "description": "Les fondamentaux de la gestion d'une TPE/PME en Afrique",
        "category": "gestion",
        "level": "debutant",
        "duration": "2h",
        "modules": 10,
        "icon": "⚙️"
    },
    {
        "id": 7,
        "title": "Recruter et Manager",
        "description": "Comment construire et gérer une équipe performante",
        "category": "gestion",
        "level": "intermediaire",
        "duration": "1h15",
        "modules": 7,
        "icon": "👥"
    },
    {
        "id": 8,
        "title": "Outils Digitaux Essentiels",
        "description": "Maîtriser les outils numériques indispensables pour votre activité",
        "category": "digital",
        "level": "debutant",
        "duration": "1h30",
        "modules": 8,
        "icon": "💻"
    },
    {
        "id": 9,
        "title": "E-commerce et Vente en Ligne",
        "description": "Créer et gérer une boutique en ligne performante",
        "category": "digital",
        "level": "intermediaire",
        "duration": "2h",
        "modules": 12,
        "icon": "🛒"
    },
    {
        "id": 10,
        "title": "Conformité Fiscale Simplifiée",
        "description": "Comprendre vos obligations fiscales et les gérer facilement",
        "category": "conformite",
        "level": "debutant",
        "duration": "1h",
        "modules": 5,
        "icon": "📋"
    },
    {
        "id": 11,
        "title": "Statuts Juridiques et Régimes",
        "description": "Choisir le bon statut juridique pour votre entreprise",
        "category": "conformite",
        "level": "intermediaire",
        "duration": "45 min",
        "modules": 4,
        "icon": "⚖️"
    },
    {
        "id": 12,
        "title": "Prévention des Fraudes",
        "description": "Identifier et prévenir les arnaques et fraudes dans les affaires",
        "category": "conformite",
        "level": "avance",
        "duration": "30 min",
        "modules": 3,
        "icon": "🛡️"
    }
]

# Parcours recommandés basés sur les lacunes détectées
RECOMMENDED_PATHS = [
    {
        "id": 1,
        "title": "起点 : Gestion de Base",
        "description": "Pour les entrepreneurs debutants qui veulent maîtriser les fondamentaux",
        "courses": [1, 6, 8],
        "duration": "4h15",
        "icon": "🚀"
    },
    {
        "id": 2,
        "title": "Croissance : Marketing & Ventes",
        "description": "Développer votre clientèle et augmenter vos revenus",
        "courses": [4, 5, 9],
        "duration": "3h45",
        "icon": "📈"
    },
    {
        "id": 3,
        "title": "Sécurité : Conformité",
        "description": "Protéger votre entreprise des risques juridiques et financiers",
        "courses": [10, 11, 12],
        "duration": "2h15",
        "icon": "🔒"
    },
    {
        "id": 4,
        "title": "Expert : Finance Avancée",
        "description": "Pour les entrepreneurs expérimentés qui veulent optimiser",
        "courses": [2, 3, 7],
        "duration": "3h45",
        "icon": "⭐"
    }
]


@router.get("/")
def get_academy_info():
    """Information sur Elna Academy"""
    return {
        "name": "Elna Academy",
        "tagline": "Formation personnalisée sur vos lacunes réelles",
        "total_courses": len(COURSES),
        "total_paths": len(RECOMMENDED_PATHS),
        "description": "L'IA détecte vos lacunes et vous recommande les formations adaptées"
    }


@router.get("/courses")
def get_courses(
    category: Optional[Category] = None,
    level: Optional[Level] = None
):
    """Liste des formations"""
    courses = COURSES
    if category:
        courses = [c for c in courses if c["category"] == category.value]
    if level:
        courses = [c for c in courses if c["level"] == level.value]
    return courses


@router.get("/courses/{course_id}")
def get_course(course_id: int):
    """Détails d'une formation"""
    for course in COURSES:
        if course["id"] == course_id:
            return course
    return {"error": "Formation non trouvée"}


@router.get("/paths")
def get_paths():
    """Parcours recommandés"""
    return RECOMMENDED_PATHS


@router.get("/paths/{path_id}")
def get_path(path_id: int):
    """Détails d'un parcours"""
    for path in RECOMMENDED_PATHS:
        if path["id"] == path_id:
            # Ajouter les détails des formations
            path_detail = path.copy()
            path_detail["courses_detail"] = [
                c for c in COURSES if c["id"] in path["courses"]
            ]
            return path_detail
    return {"error": "Parcours non trouvé"}


@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: int):
    """
    Recommandations personnalisées basées sur l'activité
    L'IA analyse les données et recommande les formations pertinentes
    """
    # Simulation - en production, analyser les données utilisateur
    return {
        "user_id": user_id,
        "recommendations": [
            {
                "reason": "Vos transactions varient beaucoup",
                "course": COURSES[0],  # Trésorerie
                "priority": "high"
            },
            {
                "reason": "Opportunités de croissance détectées",
                "course": COURSES[4],  # Fidélisation
                "priority": "medium"
            },
            {
                "reason": "Conformité à améliorer",
                "course": COURSES[9],  # Fiscale
                "priority": "medium"
            }
        ]
    }


@router.get("/progress/{user_id}")
def get_progress(user_id: int):
    """Progression de l'utilisateur"""
    return {
        "user_id": user_id,
        "completed_courses": 3,
        "in_progress": 2,
        "total_time": "4h30",
        "certificates": 2,
        "next_course": COURSES[2]
    }


@router.post("/progress/{user_id}/complete")
def complete_course(user_id: int, course_id: int):
    """Marquer une formation comme terminée"""
    return {
        "user_id": user_id,
        "course_id": course_id,
        "status": "completed",
        "certificate_earned": True
    }
