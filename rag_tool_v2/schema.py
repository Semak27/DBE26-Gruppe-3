"""Kanonisches Schema + Mapping der beiden Quellen.

Die beiden Rohquellen (Kununu, Glassdoor) haben unterschiedliche Spalten.
Hier wird festgelegt, wie beide auf EIN gemeinsames Schema abgebildet werden,
damit Cleaning, RAG und Dashboard quellenuebergreifend funktionieren.
"""

# Sub-Ratings, die in BEIDEN Quellen existieren -> fuer Vergleiche im Dashboard
COMMON_RATINGS = [
    "arbeitsatmosphaere",
    "work_life_balance",
    "gehalt",
    "karriere",
    "vorgesetzte",
    "gleichberechtigung",
]

# Weitere Ratings, die nur Kununu liefert (bleiben erhalten, wo vorhanden)
EXTRA_RATINGS = [
    "image", "umwelt_sozial", "kollegen", "umgang_aeltere",
    "arbeitsbedingungen", "kommunikation", "interessante_aufgaben",
]

ALL_RATINGS = COMMON_RATINGS + EXTRA_RATINGS

# Kanonische Spalten
CANONICAL_COLUMNS = [
    "review_id", "unternehmen", "source", "typ", "datum", "titel", "gesamt_score",
    "empfehlung", "position", "bereich", "ort", "sprache",
    *ALL_RATINGS,
    "text_positiv", "text_negativ", "text_verbesserung", "text_freitext",
]

# --- Kununu-Mapping: kanonisch -> Original-Spaltenname ------------------
KUNUNU_RATING_MAP = {
    "arbeitsatmosphaere": "Arbeitsatmosphäre",
    "image": "Image",
    "work_life_balance": "Work-Life-Balance",
    "karriere": "Karrie/Weiterbildung",
    "gehalt": "Gehalt/Sozialleistungen",
    "umwelt_sozial": "Umwelt-/Sozialbewusstsein",
    "kollegen": "Kollgenzusammenhat",
    "umgang_aeltere": "Umgang mit ältreren Kollgen",
    "vorgesetzte": "Vorgesetztenverhalten",
    "arbeitsbedingungen": "Arbeitsbedingungen",
    "kommunikation": "Kommunikation",
    "gleichberechtigung": "Gleichberechtigung",
    "interessante_aufgaben": "Interessante Aufgaben",
}

# --- Glassdoor-Mapping: kanonisch -> Original-Spaltenname ---------------
GLASSDOOR_RATING_MAP = {
    "arbeitsatmosphaere": "Culture & Values",
    "gleichberechtigung": "Diversity & Inclusion",
    "work_life_balance": "Work/Life Balance",
    "gehalt": "Compensation & Benefits",
    "karriere": "Career Opportunities",
    "vorgesetzte": "Senior Management",
}

# --- Indeed-Mapping: kanonisch -> Original-Spaltenname ------------------
INDEED_RATING_MAP = {
    "work_life_balance": "Work-life Balance",
    "gehalt": "Pay and Benefits",
    "karriere": "Job Security and Advancement",
    "vorgesetzte": "Management",
    "arbeitsatmosphaere": "Culture",
}

# Normalisierung der Beschaeftigungstypen auf gemeinsame Kategorien
TYP_MAP = {
    # Kununu
    "Mitarbeiter": "Mitarbeiter",
    "Bewerber": "Bewerber",
    "Auszubildende": "Azubi",
    "Auszubildender": "Azubi",
    # Glassdoor (Employment Status)
    "Full-time": "Mitarbeiter",
    "Part-time": "Mitarbeiter",
    "Manager": "Mitarbeiter",
    "Temporary": "Mitarbeiter",
    "Contractor": "Mitarbeiter",
    "Intern": "Praktikant",
    "Apprentice": "Azubi",
}
