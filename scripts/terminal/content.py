"""All hero copy lives here. Edit this file, then run `make all`.

Sourced from the CV and the public GitHub profile. Nothing here asserts a
metric, employer, or project that is not already in those documents.

Line lengths are budget-checked at build time: if something does not fit its
card, render.py fails loudly rather than clipping it silently.
"""

NAME = "Salih Camcı"
GREETING = "Hi"
GREETING_TAIL = "I'm"

# Typed out, held, deleted, then the next one. Cycles for the whole loop.
ROTATE = [
    "Software Engineer",
    "Incoming MSc Data Science · University of Basel",
    "Former Backend Engineering Intern · Crytek",
]

WIDE = {
    "title_left": "portrait",
    "title_right": "salih@basel — zsh — 120x34",
    "command": "whoami",
    "rotate": ROTATE,
    "fields": [
        ("~/location", "Istanbul → Basel, Sep 2026"),
        ("~/focus", "backend · data science · agentic systems"),
        ("~/github", "github.com/Salih04"),
        ("~/email", "salihcamci04@gmail.com"),
    ],
    "skills": [
        "Python", "Go", "SQL", "PyTorch", "FastAPI",
        "Docker", "PostgreSQL", "Redis", "TypeScript", "Temporal",
    ],
    "connect": ["GitHub", "LinkedIn", "Portfolio"],
}

# Mobile: shorter strings so the type can stay large at 420px.
STACK = {
    "title_left": "portrait",
    "title_right": "salih@basel — zsh",
    "command": "whoami",
    "rotate": [
        "Software Engineer",
        "MSc Data Science · Basel",
        "Backend Eng · Crytek",
    ],
    "fields": [
        ("~/location", "Istanbul → Basel"),
        ("~/focus", "backend · data · agents"),
        ("~/github", "github.com/Salih04"),
    ],
    "skills": ["Python", "Go", "SQL", "PyTorch", "FastAPI", "Docker"],
    "connect": ["GitHub", "LinkedIn"],
}
