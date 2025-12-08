# 📐 Guide des Formules Mathématiques

## Rendu LaTeX dans l'Interface

L'application supporte maintenant le **rendu automatique des formules mathématiques** en LaTeX !

### Comment ça fonctionne ?

Les formules entre crochets `[ ... ]` sont automatiquement détectées et affichées en format mathématique.

### Exemples

#### Avant (texte brut)
```
[ \text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (\hat{Y}_i - Y_i)^2 ]
```

#### Après (rendu mathématique)
La formule s'affiche correctement avec:
- Fractions
- Symboles mathématiques
- Indices et exposants
- Sommes, intégrales, etc.

### Formules Supportées

#### 1. Équations Simples
```
[ y = mx + b ]
[ a^2 + b^2 = c^2 ]
[ E = mc^2 ]
```

#### 2. Fractions
```
[ \frac{a}{b} ]
[ \frac{1}{n} \sum_{i=1}^{n} x_i ]
```

#### 3. Sommes et Produits
```
[ \sum_{i=1}^{n} x_i ]
[ \prod_{i=1}^{n} x_i ]
```

#### 4. Intégrales
```
[ \int_{0}^{\infty} e^{-x^2} dx ]
[ \int_{a}^{b} f(x) dx ]
```

#### 5. Matrices
```
[ \begin{bmatrix} a & b \\ c & d \end{bmatrix} ]
```

#### 6. Racines
```
[ \sqrt{x} ]
[ \sqrt[n]{x} ]
```

#### 7. Indices et Exposants
```
[ x_i ]
[ x^2 ]
[ x_i^2 ]
```

#### 8. Symboles Grecs
```
[ \alpha, \beta, \gamma, \delta ]
[ \theta, \lambda, \mu, \sigma ]
```

### Exemples du Cours ML

#### Mean Squared Error (MSE)
```
[ \text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (\hat{Y}_i - Y_i)^2 ]
```

#### Régression Linéaire
```
[ y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + ... + \beta_n x_n + \epsilon ]
```

#### Fonction Sigmoïde
```
[ \sigma(x) = \frac{1}{1 + e^{-x}} ]
```

#### Distance Euclidienne
```
[ d(x, y) = \sqrt{\sum_{i=1}^{n} (x_i - y_i)^2} ]
```

#### Entropie
```
[ H(X) = -\sum_{i=1}^{n} p(x_i) \log_2 p(x_i) ]
```

### Syntaxe LaTeX Courante

| Symbole | LaTeX | Rendu |
|---------|-------|-------|
| Fraction | `\frac{a}{b}` | a/b |
| Somme | `\sum_{i=1}^{n}` | Σ |
| Intégrale | `\int_{a}^{b}` | ∫ |
| Racine | `\sqrt{x}` | √x |
| Exposant | `x^2` | x² |
| Indice | `x_i` | xᵢ |
| Alpha | `\alpha` | α |
| Beta | `\beta` | β |
| Theta | `\theta` | θ |
| Lambda | `\lambda` | λ |
| Mu | `\mu` | μ |
| Sigma | `\sigma` | σ |

### Texte dans les Formules

Pour ajouter du texte dans une formule:
```
[ \text{MSE} = ... ]
[ \text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} ]
```

### Formules Multi-lignes

Pour les équations sur plusieurs lignes:
```
[
\begin{align}
y &= mx + b \\
m &= \frac{y_2 - y_1}{x_2 - x_1}
\end{align}
]
```

### Limitations

- Les formules doivent être entre crochets `[ ]`
- Le LaTeX doit être valide
- Si une formule ne s'affiche pas, elle sera affichée en texte brut

### Dépannage

**Problème**: La formule ne s'affiche pas correctement

**Solutions**:
1. Vérifiez que la formule est entre `[ ]`
2. Vérifiez la syntaxe LaTeX
3. Essayez de simplifier la formule
4. Consultez la documentation LaTeX

**Exemple de formule invalide**:
```
[ \frac{a}{b  # Manque le }
```

**Exemple de formule valide**:
```
[ \frac{a}{b} ]
```

### Ressources LaTeX

- [LaTeX Math Symbols](https://www.overleaf.com/learn/latex/List_of_Greek_letters_and_math_symbols)
- [LaTeX Math Guide](https://en.wikibooks.org/wiki/LaTeX/Mathematics)
- [Detexify](http://detexify.kirelabs.org/classify.html) - Dessinez un symbole pour trouver son code LaTeX

### Questions Fréquentes

**Q: Puis-je utiliser $$ au lieu de [ ] ?**
R: Oui, les deux formats sont supportés.

**Q: Les formules inline sont-elles supportées ?**
R: Oui, utilisez `[ formule ]` dans le texte.

**Q: Puis-je copier-coller des formules LaTeX ?**
R: Oui, assurez-vous juste qu'elles sont entre `[ ]`.

**Q: Les formules sont-elles sauvegardées ?**
R: Oui, dans l'historique de conversation.

---

**Date**: 8 décembre 2025  
**Version**: 1.0
