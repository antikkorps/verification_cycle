import logging
import re
from pprint import pprint

import regnault_validator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ocr_autoclave.log')
    ]
)
logger = logging.getLogger(__name__)


def analyser_cycle_complet_grs(chemin_fichier: str) -> dict:
    """
    Analyse le fichier .grs en deux passes :
    1. Lit les données du cycle ligne par ligne pour trouver les phases de vide.
    2. Lit les données de résumé (#) pour les températures min/max.

    Args:
        chemin_fichier: Le chemin vers le fichier .grs.

    Returns:
        Un dictionnaire contenant toutes les données nécessaires à la validation.
    """
    donnees: dict = {
        "phases_de_vide": [],
        "phases_de_vide_kPa": []
    }

    try:
        # Utiliser 'latin-1' est souvent plus sûr pour les fichiers générés par des équipements
        with open(chemin_fichier, 'r', encoding='latin-1') as f_in:
            lignes_brutes = f_in.readlines()
        
        lignes = [ligne.strip() for ligne in lignes_brutes]

        # --- PASSE 1: Analyse du détail du cycle pour les vides ---
        for ligne_str in lignes:
            if 'Injection de vapeur' not in ligne_str:
                continue

            if '{' not in ligne_str:
                continue

            _, _, suffixe = ligne_str.partition('{')
            partie_evenement = suffixe.strip()

            match_mesures = re.search(r'Injection de vapeur\((\d{3,4})\[(\d{3,4})', partie_evenement)
            if not match_mesures:
                continue

            temperature_str, pression_str = match_mesures.groups()

            try:
                temperature_phase = float(temperature_str) / 10.0
                pression_vide = float(pression_str) / 10.0
            except ValueError:
                continue

            horodatage = ""
            match_horodatage = re.match(r'(\d{2}:\d{2}:\d{2})', partie_evenement)
            if match_horodatage:
                horodatage = match_horodatage.group(1)

            phase_info = {
                "horodatage": horodatage,
                "temperature_C": temperature_phase,
                "pression_kPa": pression_vide,
                "conforme": pression_vide <= 18.0
            }

            donnees["phases_de_vide"].append(phase_info)

            if phase_info["conforme"]:
                donnees["phases_de_vide_kPa"].append(pression_vide)

        # --- PASSE 2: Analyse du résumé pour les températures ---
        donnees_resume = {}
        for ligne_str in lignes:
            if ligne_str.startswith('#'):
                match = re.search(r'^#(\d+)\s*(.*)', ligne_str)
                if match:
                    cle, valeur = match.group(1), match.group(2).strip()
                    donnees_resume[cle] = valeur
        
        if '40' in donnees_resume:
            donnees['temp_min_C'] = float(donnees_resume['40']) / 10.0
        if '41' in donnees_resume:
            donnees['temp_max_C'] = float(donnees_resume['41']) / 10.0

    except FileNotFoundError:
        logger.error(f"Fichier introuvable à '{chemin_fichier}'")
        return {}
        
    return donnees

def valider_donnees_completes(donnees: dict):
    """Affiche les résultats de la validation basée sur les règles complètes."""
    print("\n" + "="*50)
    print("          VALIDATION COMPLÈTE DU CYCLE")
    print("="*50 + "\n")
    
    validation_globale_ok = True

    # --- Règle 1: Validation de la plage de température ---
    logger.info("--- 1. Validation Température Palier ---")
    if 'temp_min_C' in donnees and 'temp_max_C' in donnees:
        t_min = donnees['temp_min_C']
        t_max = donnees['temp_max_C']
        
        is_min_valid = t_min >= 134.3
        is_max_valid = t_max <= 136.4
        
        logger.info(f"  - T° min >= 134.3°C : {'✅ OK' if is_min_valid else '❌ NON CONFORME'} (mesuré: {t_min}°C)")
        logger.info(f"  - T° max <= 136.4°C : {'✅ OK' if is_max_valid else '❌ NON CONFORME'} (mesuré: {t_max}°C)")
        
        if not is_min_valid or not is_max_valid:
            validation_globale_ok = False
    else:
        logger.warning("  - ⚠️ Données de température manquantes")
        validation_globale_ok = False

    # --- Règle 2: Validation des phases de vide ---
    logger.info("\n--- 2. Validation des Phases de Vide ---")
    if 'phases_de_vide' in donnees and donnees['phases_de_vide']:
        phases = donnees['phases_de_vide']
        phases_conformes = [phase for phase in phases if phase['conforme']]

        nombre_phases = len(phases_conformes)
        is_nombre_ok = nombre_phases >= 8
        logger.info(f"  - Nombre de phases de vide conformes >= 8 : {'✅ OK' if is_nombre_ok else '❌ NON CONFORME'} (trouvé: {nombre_phases})")

        is_pressions_ok = is_nombre_ok
        logger.info(f"  - Pression <= 18 kPa sur au moins 8 phases : {'✅ OK' if is_pressions_ok else '❌ NON CONFORME'}")

        logger.info("  - Détail des phases d'injection :")
        for i, phase in enumerate(phases, 1):
            statut = "CONFORME" if phase['conforme'] else "NON CONFORME"
            horodatage = phase['horodatage'] or '-'
            logger.info(
                f"    Phase {i:02d} ({horodatage}) : "
                f"{phase['temperature_C']:.1f} °C / {phase['pression_kPa']:.1f} kPa -> {statut}"
            )

        if not is_nombre_ok or not is_pressions_ok:
            validation_globale_ok = False
    else:
        logger.warning("  - ⚠️ Données des phases de vide manquantes")
        validation_globale_ok = False

    # --- Règle 3: Validation Pression/Température (Régnault) ---
    logger.info("\n--- 3. Validation Pression/Température (Régnault) ---")
    try:
        with open(fichier_grs, 'r', encoding='latin-1') as f_in:
            file_content = f_in.read()
        
        regnault_results = regnault_validator.validate_grs_file_content(file_content)
        
        if not regnault_results:
            logger.warning("  - ⚠️ Aucune ligne de 'Palier de stérilisation' ou 'Dévaporisation' trouvée.")
            validation_globale_ok = False
        else:
            regnault_conforme = True
            for result in regnault_results:
                if result['status'] != "Conforme":
                    regnault_conforme = False
                
                logger.info(
                    f"  - Ligne {result['line_number']} ({result['line_name']}): "
                    f"T={result['temperature']}°C, P={result['pressure']}kPa -> "
                    f"Statut: {result['status']}. "
                    f"(Attendu: {result['expected_range']} kPa)"
                )
            
            if not regnault_conforme:
                validation_globale_ok = False
    except Exception as e:
        logger.error(f"  - ⚠️ Erreur lors de la lecture du fichier GRS: {e}")
        validation_globale_ok = False


    # --- Résultat Final ---
    print("\n" + "="*50)
    if validation_globale_ok:
        print("✅ RÉSULTAT FINAL : CYCLE CONFORME")
    else:
        print("❌ RÉSULTAT FINAL : CYCLE NON CONFORME")
    print("="*50)

# --- POINT D'ENTRÉE PRINCIPAL DU SCRIPT ---
if __name__ == "__main__":
    
    fichier_grs = "010939.grs"  # Remplace par le nom de ton fichier
    
    donnees_extraites = analyser_cycle_complet_grs(fichier_grs)
    
    if donnees_extraites:
        print("\n" + "="*50)
        print("          DONNÉES EXTRAITES POUR VALIDATION")
        print("="*50 + "\n")
        logger.debug(f"Données extraites: {donnees_extraites}")
        
        valider_donnees_completes(donnees_extraites)
    else:
        logger.error("Aucune donnée n'a pu être extraite du fichier.")
