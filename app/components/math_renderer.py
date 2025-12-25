"""
Module pour le rendu des formules mathématiques LaTeX
"""
import streamlit as st
import re


def render_math_content(text: str):
    """
    Rend le contenu avec support LaTeX pour les formules mathématiques.
    Détecte automatiquement les formules LaTeX même sans délimiteurs.
    """
    # Nettoyer les caractères Unicode bizarres
    text = re.sub(r'Y\^iY\^i', r'\\hat{Y}_i', text)
    text = re.sub(r'YiYi', r'Y_i', text)
    
    # 1. Formules entre crochets [ ... ]
    text = re.sub(r'\[\s*([^\]]+?)\s*\]', r'$$\1$$', text)
    
    # 2. Formules LaTeX standard \( ... \) et \[ ... \]
    text = re.sub(r'\\\(\s*([^)]+?)\s*\\\)', r'$$\1$$', text)
    text = re.sub(r'\\\[\s*([^\]]+?)\s*\\\]', r'$$\1$$', text)
    
    # 3. NOUVEAU: Détecter formules LaTeX inline sans délimiteurs
    # Pattern: \text{Word} = \frac{...}{...}
    inline_patterns = [
        # Formule complète: \text{Name} = \frac{...}{...}
        r'(\\text\{[^}]+\}\s*=\s*\\frac\{[^}]+\}\{[^}]+\})',
        # Formule avec opérations: TP + TN / TP + FP + FN + TN
        r'(\\text\{[^}]+\}\s*=\s*\\frac\{[^}]+\+[^}]+\}\{[^}]+\+[^}]+\})',
    ]
    
    for pattern in inline_patterns:
        text = re.sub(pattern, r'$$\1$$', text)
    
    # 4. Détecter formules qui commencent par \text{ ou \frac{ avec =
    latex_equation_pattern = r'(\\(?:text|frac|sum|int|sqrt|hat)\{[^}]*\}[^a-zA-Z\n]*?(?:=|\\sum|\\int|\\frac)[^\n]*?)(?=\s*(?:où|Où|Cette|Pour|La|Le|\.|,|\n|$))'
    
    def wrap_latex(match):
        formula = match.group(1).strip()
        if not formula.startswith('$'):
            return f'$$\n{formula}\n$$'
        return formula
    
    text = re.sub(latex_equation_pattern, wrap_latex, text, flags=re.MULTILINE)
    
    # 5. Diviser le texte en parties: texte normal et formules
    parts = re.split(r'(\$\$.*?\$\$)', text, flags=re.DOTALL)
    
    for part in parts:
        if part.startswith('$$') and part.endswith('$$'):
            # C'est une formule LaTeX
            formula = part[2:-2].strip()
            try:
                st.latex(formula)
            except Exception as e:
                # Si erreur LaTeX, afficher comme code
                st.code(formula, language='latex')
                st.error(f"Erreur de rendu LaTeX: {e}")
        elif part.strip():
            # C'est du texte normal
            st.markdown(part)
