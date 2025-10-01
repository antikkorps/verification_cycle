# OCR Autoclave

Projet d'OCR pour la validation de cycles d'autoclave en stérilisation médicale.

## Description

Ce projet permet d'analyser et de valider des cycles de stérilisation en extrayant et en vérifiant les données critiques depuis des fichiers `.grs` générés par les autoclaves. Il vérifie la conformité selon trois critères principaux :

- **Température de palier** : Doit être entre 134.3°C et 136.4°C
- **Phases de vide** : Au moins 8 phases avec pression ≤ 18 kPa
- **Table de Régnault** : Validation pression/température selon les normes

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le dépôt**

   ```bash
   git clone <url-du-dépôt>
   cd ocr_autoclave
   ```

2. **Créer un environnement virtuel**

   ```bash
   python3 -m venv venv
   ```

3. **Activer l'environnement virtuel**
   - Sur Linux/Mac :
     ```bash
     source venv/bin/activate
     ```
   - Sur Windows :
     ```bash
     venv\Scripts\activate
     ```

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### Lancement de l'analyse

Pour lancer la validation du cycle par défaut :

```bash
python3 main.py
```

Le script analyse automatiquement le fichier `010939.grs` présent dans le répertoire.

### Utilisation avec un autre fichier

Pour analyser un fichier différent, modifiez la variable `fichier_grs` dans `main.py` :

```python
fichier_grs = "votre_fichier.grs"
```

### Résultats

- **Affichage console** : Résumé visuel de la validation avec mise en forme
- **Fichier de log** : `ocr_autoclave.log` contenant les détails techniques
- **Niveaux de conformité** : ✅ CONFORME ou ❌ NON CONFORME pour chaque critère

## Structure du projet

```
ocr_autoclave/
├── main.py                 # Script principal d'analyse
├── regnault_validator.py   # Module de validation Régnault
├── debug_preprocessing.py  # Outil de prétraitement d'images
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
├── .gitignore             # Fichiers ignorés par Git
└── ocr_autoclave.log      # Logs générés (créé après exécution)
```

## Dépendances

- `opencv-python` : Traitement d'images
- `numpy` : Calculs numériques
- `pillow` : Manipulation d'images
- `pytesseract` : Reconnaissance de texte (OCR)

## Logs

Le système de logging génère deux types de sortie :

1. **Console** : Affichage utilisateur avec mise en forme
2. **Fichier** (`ocr_autoclave.log`) : Logs techniques avec timestamps pour débogage

Niveaux de logging :

- `INFO` : Résultats normaux et informations
- `WARNING` : Données manquantes ou anomalies mineures
- `ERROR` : Erreurs critiques et non-conformités
- `DEBUG` : Informations détaillées (décommenter pour activer)

## Développement

### Tests

Pour tester avec différents fichiers `.grs`, placez-les dans le répertoire principal et modifiez la variable `fichier_grs` dans `main.py`.

