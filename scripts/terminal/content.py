"""All hero copy lives here. Edit this file, then run `make all`.

Sourced from the CV and the public GitHub profile. Nothing here asserts a
metric, employer, or project that is not already in those documents.

Line-length budgets (characters), enforced by render.py at build time:
    wide  identity card -> 72
    stack identity card -> 48
"""

NAME = "Salih Camcı"

# Wide build (desktop, 1280x520).
WIDE = {
    "title_left": "portrait",
    "title_right": "salih@basel — zsh",
    "command": "whoami",
    "roles": [
        "Software Engineer",
        "Incoming MSc Data Science · University of Basel",
        "Former Backend Engineering Intern · Crytek",
    ],
    "fields": [
        ("~/focus", "backend systems · data science · agentic workflows"),
        ("~/building", "research tooling · AI systems · spatial interfaces"),
        ("~/stack", "Python  Go  SQL  PyTorch  FastAPI  Docker"),
        ("~/links", "github.com/Salih04 · in/salih-camci · salih04.github.io"),
    ],
}

# Stacked build (mobile, 560 wide). Shorter lines so the type can be larger.
STACK = {
    "title_left": "portrait",
    "title_right": "salih@basel — zsh",
    "command": "whoami",
    "roles": [
        "Software Engineer",
        "Incoming MSc Data Science · Basel",
        "Former Backend Eng Intern · Crytek",
    ],
    "fields": [
        ("~/focus", "backend · data science · agents"),
        ("~/stack", "Python Go SQL PyTorch FastAPI"),
        ("~/links", "github.com/Salih04"),
    ],
}
