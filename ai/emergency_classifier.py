from __future__ import annotations

import re
from typing import Dict


FALL_KEYWORDS = ["fell down", "fall", "cannot get up", "down", "slipped", "tripped"]
INJURY_KEYWORDS = ["injury", "hurt", "cut", "pain", "bleeding", "wound", "sprained"]
DIZZINESS_KEYWORDS = ["dizzy", "lightheaded", "faint", "unsteady", "vertigo"]
BREATHING_KEYWORDS = ["cannot breathe", "breathing trouble", "short of breath", "trouble breathing", "choking"]
CHEST_KEYWORDS = ["chest pain", "tight chest", "heart pain"]
WEAKNESS_KEYWORDS = ["weak", "very weak", "cannot stand", "tired", "shaky"]
OK_KEYWORDS = ["i am okay", "i'm okay", "okay", "fine", "safe", "not urgent", "no need help"]
HELP_KEYWORDS = ["help", "emergency", "need help", "urgent", "please help"]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_emergency(text: str) -> Dict[str, object]:
    cleaned = clean_text(text)
    scores = {
        "Fall": 0,
        "Injury": 0,
        "Dizziness": 0,
        "Breathing difficulty": 0,
        "Chest pain": 0,
        "Weakness": 0,
        "General emergency": 0,
        "Other": 0,
    }

    for category, keywords in {
        "Fall": FALL_KEYWORDS,
        "Injury": INJURY_KEYWORDS,
        "Dizziness": DIZZINESS_KEYWORDS,
        "Breathing difficulty": BREATHING_KEYWORDS,
        "Chest pain": CHEST_KEYWORDS,
        "Weakness": WEAKNESS_KEYWORDS,
    }.items():
        for keyword in keywords:
            if keyword in cleaned:
                scores[category] += 1

    if any(word in cleaned for word in HELP_KEYWORDS):
        scores["General emergency"] += 2
    if any(word in cleaned for word in OK_KEYWORDS):
        scores["Other"] += 1

    category = max(scores.items(), key=lambda item: item[1])[0]
    if all(value == 0 for value in scores.values()):
        category = "Other"

    severity = "NORMAL"
    if category in {"Fall", "Breathing difficulty", "Chest pain", "General emergency"}:
        severity = "CRITICAL"
    elif category in {"Injury", "Dizziness", "Weakness"}:
        severity = "WARNING"

    if any(word in cleaned for word in OK_KEYWORDS):
        severity = "NORMAL"
        category = "Other"

    max_score = max(scores.values())
    confidence = round(min(0.95, 0.5 + (max_score * 0.12)), 2)
    messages = {
        "Fall": "Immediate assistance may be required.",
        "Injury": "The user may need urgent support.",
        "Dizziness": "Please monitor the person closely.",
        "Breathing difficulty": "This may be a serious breathing issue.",
        "Chest pain": "This situation should be escalated quickly.",
        "Weakness": "The user may be weak or unable to stand safely.",
        "General emergency": "Emergency help may be needed.",
        "Other": "The message has been reviewed for a possible emergency.",
    }

    return {
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "message": messages.get(category, "The input has been analyzed."),
    }
