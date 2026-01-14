#!/usr/bin/env python3
"""
Démonstration du formatage amélioré des listes numérotées
"""

def demo_formatting():
    """Démontre le formatage des listes numérotées"""
    
    # Exemple de réponse mal formatée (comme le chatbot pourrait la générer)
    bad_response = """Les principales technologies IoT sont: 1- Les capteurs qui collectent des données environnementales 2- Les réseaux de communication qui transmettent les informations 3- Les plateformes cloud qui stockent et analysent les données 4- Les interfaces utilisateur qui permettent la visualisation"""
    
    print("=== DÉMONSTRATION DU FORMATAGE DES LISTES ===\n")
    
    print("AVANT (difficile à lire):")
    print("-" * 50)
    print(bad_response)
    print()
    
    # Simulation du formatage automatique
    formatted_response = bad_response
    
    # Pattern de remplacement (même logique que dans response_generator.py)
    import re
    patterns = [
        (r'([^0-9])\s+(\d+[-–]\s)', r'\1\n\n\2'),
        (r'([^0-9])\s+(\d+\.\s)', r'\1\n\n\2'),
        (r'([^0-9])\s+(\d+\)\s)', r'\1\n\n\2'),
    ]
    
    for find_pattern, replace_pattern in patterns:
        new_text = re.sub(find_pattern, replace_pattern, formatted_response)
        if new_text != formatted_response:
            formatted_response = new_text
            break
    
    print("APRÈS (facile à lire):")
    print("-" * 50)
    print(formatted_response)
    print()
    
    print("✅ Chaque élément numéroté est maintenant sur une ligne séparée!")
    print("✅ Amélioration automatique de la lisibilité des réponses du chatbot")

if __name__ == "__main__":
    demo_formatting()