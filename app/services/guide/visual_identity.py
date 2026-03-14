"""
Guide de l'Identité Visuelle Elna Tech - Service IA
Intégration du guide avec assistant virtuel
"""
import re
from typing import Dict, List, Optional


class GuideVISUELService:
    """
    Service de gestion du guide d'identité visuelle Elna Tech
    Avec IA de问答 (Q&A)
    """
    
    # Contenu du guide d'identité visuelle
    GUIDE_CONTENT = """
    # GUIDE D'IDENTITÉ VISUELLE - ELNA TECH HOLDING

    ## 1. LOGO
    
    ### Version principale
    - Le logo "Elna Tech" combine le mot "Elna" avec l'élément "Tech"
    - Version horizontale recommandée pour usage web
    - Version verticale pour usage mobile
    
    ### Zone de protection
    - Espace minimum autour du logo: 20px
    - Aucune autre élément ne doit empiéter sur cette zone
    
    ### Tailles minimales
    - Digital: 32px de hauteur minimum
    - Imprimerie: 15mm de largeur minimum

    ## 2. COULEURS

    ### Palette Primaire
    - ELNA VIOLET: #6B21A8 (RGB: 107, 33, 168)
    - ELNA BLEU: #0EA5E9 (RGB: 14, 165, 233)
    - ELNA TURQUOISE: #14B8A6 (RGB: 20, 184, 166)

    ### Palette Secondaire
    - GRIS FONCÉ: #1E293B
    - GRIS CLAIR: #64748B
    - BLANC: #FFFFFF

    ### Palette Accent
    - CORAIL: #F97316
    - VERT: #22C55E
    - ROUGE: #EF4444

    ### Utilisation des couleurs
    - Fond sombre: utiliser ELNA VIOLET ou GRIS FONCÉ
    - Fond clair: utiliser ELNA BLEU ou TURQUOISE
    - Appels à l'action: ELNA VIOLET ou CORAIL

    ## 3. TYPOGRAPHIE

    ### Font principale
    - Inter (Google Fonts)
    - Usage: Titres, boutons, navigation
    
    ### Font secondaire
    - Roboto (Google Fonts)
    - Usage: Corps de texte, paragraphes

    ### Hiérarchie
    - H1: 48px, Bold (700)
    - H2: 36px, Semi-Bold (600)
    - H3: 24px, Semi-Bold (600)
    - Body: 16px, Regular (400)
    - Caption: 14px, Regular (400)

    ## 4. IMAGES ET ICONOGRAPHIE

    ### Style photographique
    - Photos authentique et naturelle
    - Luminosité équilibrée
    - Privilégier les images de personnes africaines
    - Éviter les stock photos génériques

    ### Icônes
    - Style: Line icons (contour)
    - Épaisseur: 1.5px ou 2px
    - Couleur: HEX #1E293B ou #6B21A8
    - Coins arrondis: 2px à 4px

    ## 5. COMPOSANTS UI

    ### Boutons
    - Primaire: Fond #6B21A8, texte blanc, border-radius 8px
    - Secondaire: Fond transparent, bordure #6B21A8, texte #6B21A8
    - Danger: Fond #EF4444, texte blanc
    - Hauteur: 40px (default), 48px (large), 32px (small)

    ### Cartes
    - Fond: #FFFFFF
    - Ombre: 0 4px 6px -1px rgba(0,0,0,0.1)
    - Border-radius: 12px
    - Padding: 24px

    ### Formulaires
    - Bordure: 1px solid #E2E8F0
    - Focus: 2px solid #6B21A8
    - Border-radius: 8px
    - Hauteur input: 44px

    ### Badges/Tags
    - Border-radius: 20px (pillule)
    - Padding: 4px 12px
    - Font-size: 12px

    ## 6. ESPACE

    ### Grille
    - 12 colonnes
    - Gouttière: 24px
    - Marge externe: 24px (mobile), 48px (desktop)

    ### Espacements
    - xs: 4px
    - sm: 8px
    - md: 16px
    - lg: 24px
    - xl: 32px
    - 2xl: 48px
    - 3xl: 64px

    ## 7. ANIMATIONS

    ### Durées
    - Rapide: 150ms
    - Normal: 300ms
    - Lent: 500ms

    ### Effets
    - Hover boutons: scale(1.02), transition 150ms
    - Cartes hover: translateY(-4px), ombre augmentée
    - Fade-in: opacity 0 à 1

    ## 8. LOGO MARQUES

    ###使用时
    - "Elna Tech Holding" - Usage formel
    - "Elna Tech" - Usage courant
    - "Elna" - Usage simplifié (avec logo)
    
    NE JAMAIS:
    - Modifier les proportions
    - Changer les couleurs
    - Ajouter des effets (ombres, dégradés)
    - Utiliser sur fond de même couleur
    """

    # Questions fréquentes pré-définies
    FAQ = [
        {
            "question": "Quelles sont les couleurs principales d'Elna Tech?",
            "reponse": "Les couleurs principales sont:\n- Elna Violet: #6B21A8\n- Elna Bleu: #0EA5E9\n- Elna Turquoise: #14B8A6\n\nCes couleurs doivent être utilisées pour les éléments principaux."
        },
        {
            "question": "Quelle police utiliser pour les titres?",
            "reponse": "Utilisez la police Inter pour tous les titres (H1, H2, H3). C'est la police principale de la charte graphique Elna Tech."
        },
        {
            "question": "Comment utiliser le bouton primaire?",
            "reponse": "Le bouton primaire a:\n- Fond: #6B21A8 (Violet)\n- Texte: Blanc\n- Border-radius: 8px\n- Hauteur: 40px"
        },
        {
            "question": "Quelle est la zone de protection du logo?",
            "reponse": "La zone de protection est de 20px minimum autour du logo. Aucun autre élément ne doit empiéter sur cette zone."
        },
        {
            "question": "Comment styliser les cartes?",
            "reponse": "Les cartes Elna Tech ont:\n- Fond blanc (#FFFFFF)\n- Ombre douce\n- Border-radius: 12px\n- Padding: 24px"
        },
        {
            "question": "Quelles icônes utiliser?",
            "reponse": "Utilisez des icônes en style 'Line' (contour) avec:\n- Épaisseur: 1.5px ou 2px\n- Couleur: #1E293B ou #6B21A8\n- Coins légèrement arrondis"
        },
        {
            "question": "Quelle grille utiliser?",
            "reponse": "Utilisez une grille de 12 colonnes avec:\n- Gouttière: 24px\n- Marge: 24px (mobile), 48px (desktop)"
        },
        {
            "question": "Comment animer les éléments?",
            "reponse": "Durées d'animation:\n- Rapide: 150ms (hover)\n- Normal: 300ms (transitions)\n- Lent: 500ms (fade-in)"
        }
    ]
    
    def search_content(self, query: str) -> List[str]:
        """Recherche dans le contenu du guide"""
        query_lower = query.lower()
        lines = self.GUIDE_CONTENT.split('\n')
        results = []
        
        for i, line in enumerate(lines):
            # Chercher dans les titres et paragraphes
            if query_lower in line.lower():
                # Ajouter le contexte (ligne + suivantes)
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+3)])
                if context not in results:
                    results.append(context)
        
        return results[:5]  # Max 5 résultats
    
    def get_answer(self, question: str) -> Dict:
        """
        Répond à une question sur le guide d'identité visuelle
        Utilise une combinaison de FAQ et recherche dans le contenu
        """
        question_lower = question.lower()
        
        # 1. Chercher dans la FAQ
        for faq in self.FAQ:
            if any(word in faq["question"].lower() for word in question.split() if len(word) > 3):
                return {
                    "answer": faq["reponse"],
                    "source": "FAQ",
                    "matched_question": faq["question"]
                }
        
        # 2. Chercher dans le contenu
        search_results = self.search_content(question)
        if search_results:
            # Construire une réponse basée sur les résultats
            answer_parts = []
            for result in search_results[:3]:
                # Extraire les informations pertinentes
                lines = result.split('\n')
                for line in lines:
                    if any(word in line.lower() for word in question.split() if len(word) > 3):
                        answer_parts.append(line.strip())
            
            if answer_parts:
                return {
                    "answer": "\n".join(answer_parts[:4]),
                    "source": "Guide",
                    "search_results": len(search_results)
                }
        
        # 3. Réponse par défaut avec suggestions
        return {
            "answer": "Je n'ai pas trouvé de réponse précise à votre question. Voici quelques suggestions:\n\n- Quelles sont les couleurs principales?\n- Quelle police utiliser?\n- Comment styliser les boutons?\n- Quelle est la zone de protection du logo?",
            "source": "Suggestions",
            "suggestions": [faq["question"] for faq in self.FAQ[:4]]
        }
    
    def get_all_faq(self) -> List[Dict]:
        """Retourne toutes les FAQ"""
        return self.FAQ
    
    def get_color_palette(self) -> Dict:
        """Retourne la palette de couleurs complète"""
        return {
            "primary": {
                "violet": {"hex": "#6B21A8", "rgb": "107, 33, 168"},
                "bleu": {"hex": "#0EA5E9", "rgb": "14, 165, 233"},
                "turquoise": {"hex": "#14B8A6", "rgb": "20, 184, 166"}
            },
            "secondary": {
                "gris_fonce": {"hex": "#1E293B"},
                "gris_clair": {"hex": "#64748B"},
                "blanc": {"hex": "#FFFFFF"}
            },
            "accent": {
                "corail": {"hex": "#F97316"},
                "vert": {"hex": "#22C55E"},
                "rouge": {"hex": "#EF4444"}
            }
        }
    
    def get_component_styles(self, component: str) -> Dict:
        """Retourne les styles d'un composant spécifique"""
        styles = {
            "bouton": {
                "primaire": {
                    "background": "#6B21A8",
                    "color": "#FFFFFF",
                    "border_radius": "8px",
                    "height": "40px",
                    "hover": "scale(1.02)"
                },
                "secondaire": {
                    "background": "transparent",
                    "border": "1px solid #6B21A8",
                    "color": "#6B21A8",
                    "border_radius": "8px"
                }
            },
            "carte": {
                "background": "#FFFFFF",
                "shadow": "0 4px 6px -1px rgba(0,0,0,0.1)",
                "border_radius": "12px",
                "padding": "24px"
            },
            "formulaire": {
                "border": "1px solid #E2E8F0",
                "focus": "2px solid #6B21A8",
                "border_radius": "8px",
                "height": "44px"
            },
            "typo": {
                "h1": {"size": "48px", "weight": "700"},
                "h2": {"size": "36px", "weight": "600"},
                "h3": {"size": "24px", "weight": "600"},
                "body": {"size": "16px", "weight": "400"},
                "caption": {"size": "14px", "weight": "400"}
            }
        }
        return styles.get(component, {})


# Instance globale
guide_service = GuideVISUELService()
