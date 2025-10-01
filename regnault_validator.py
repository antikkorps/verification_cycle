 
"""
Module pour la validation des cycles d'autoclave par rapport à la table de Régnault.
"""

# Table de Régnault pour les températures de 134°C à 137°C.
# Les clés sont les températures entières en °C.
# Les valeurs sont des listes de tuples (pression_min, pression_max) pour chaque dixième de degré.
REGNAULT_TABLE = {
    134: [
        (299.2, 309.2), (300.1, 310.1), (301.0, 311.0), (301.9, 311.9),
        (302.8, 312.8), (303.7, 313.7), (304.6, 314.6), (305.5, 315.5),
        (306.4, 316.4), (307.3, 317.3)
    ],
    135: [
        (308.2, 318.2), (309.1, 319.1), (310.0, 320.0), (311.0, 321.0),
        (311.9, 321.9), (312.8, 322.8), (313.7, 323.7), (314.6, 324.6),
        (315.6, 325.6), (316.5, 326.5)
    ],
    136: [
        (317.4, 327.4), (318.4, 328.4), (319.3, 329.3), (320.2, 330.2),
        (321.2, 331.2), (322.1, 332.1), (323.1, 333.1), (324.0, 334.0),
        (325.0, 335.0), (325.9, 335.9)
    ],
    137: [
        (326.9, 336.9)  # Plage unique pour 137.0°C
    ]
}

def check_pressure_conformity(temperature: float, pressure: float) -> tuple[str, tuple[float, float] | None]:
    """
    Vérifie si une pression donnée est conforme pour une température donnée
    selon la table de Régnault.

    Args:
        temperature: La température en °C.
        pressure: La pression en kPa.

    Returns:
        Un tuple contenant le statut ("Conforme", "Non Conforme", "Température hors table", 
        "Décimale de température hors table") et la plage de pression attendue.
    """
    temp_int = int(temperature)
    # Gère les imprécisions des flottants pour trouver l'index décimal
    temp_dec_index = int(round((temperature - temp_int) * 10))

    if temp_int not in REGNAULT_TABLE:
        return "Température hors table", None

    pressure_ranges = REGNAULT_TABLE[temp_int]
    if temp_dec_index >= len(pressure_ranges):
        return "Décimale de température hors table", None

    min_pressure, max_pressure = pressure_ranges[temp_dec_index]

    if min_pressure <= pressure <= max_pressure:
        return "Conforme", (min_pressure, max_pressure)
    else:
        return "Non Conforme", (min_pressure, max_pressure)

def validate_grs_file_content(file_content: str) -> list[dict]:
    """
    Analyse le contenu d'un fichier GRS et valide les lignes de stérilisation
    et de dévaporisation.

    Args:
        file_content: Le contenu du fichier GRS sous forme de chaîne de caractères.

    Returns:
        Une liste de dictionnaires, chacun représentant le résultat de la validation
        pour une ligne pertinente.
    """
    results = []
    lines = file_content.splitlines()
    for i, line in enumerate(lines):
        # "stérilisation" et "Dévaporisation" peuvent avoir des encodages différents
        if "Palier de st" in line or "vaporisation" in line:
            try:
                parts = line.split('{')
                data = parts[0].split(';')
                
                # Les valeurs sont mises à l'échelle par 10 dans le fichier
                temperature = float(data[0]) / 10.0
                pressure = float(data[2]) / 10.0
                
                line_name = "Inconnu"
                if "Palier de st" in line:
                    line_name = "Palier de stérilisation"
                elif "vaporisation" in line:
                    line_name = "Dévaporisation"

                status, pressure_range = check_pressure_conformity(temperature, pressure)
                
                results.append({
                    "line_number": i + 1,
                    "line_name": line_name,
                    "temperature": temperature,
                    "pressure": pressure,
                    "expected_range": pressure_range,
                    "status": status
                })
            except (IndexError, ValueError) as e:
                results.append({
                    "line_number": i + 1,
                    "line_name": "Erreur de parsing",
                    "error": str(e),
                    "original_line": line
                })

    return results
