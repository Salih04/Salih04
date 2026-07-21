PY := .venv/bin/python3

.PHONY: all setup portrait frames check clean help

help:
	@echo "make setup     create .venv and install Pillow + numpy"
	@echo "make portrait  photo -> assets/data/portrait*.txt"
	@echo "make frames    portrait + content.py -> assets/generated/*.gif, hero-static.png"
	@echo "make all       portrait + frames + check"
	@echo "make check     asset budgets, determinism, privacy"

setup:
	python3 -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip Pillow numpy
	@echo "ready. Put your photo at assets/source-private/photo.jpg"

portrait:
	@test -f assets/source-private/photo.jpg || \
	  { echo "ERROR: place your photo at assets/source-private/photo.jpg (git-ignored)"; exit 1; }
	$(PY) scripts/portrait/build_portrait.py --cols 78 --out assets/data/portrait.txt
	$(PY) scripts/portrait/build_portrait.py --cols 64 --out assets/data/portrait-stack.txt

frames:
	$(PY) scripts/terminal/render.py --build wide --loop --still assets/generated/hero-static.png
	$(PY) scripts/terminal/render.py --build stack --loop
	$(PY) scripts/terminal/stamp_readme.py

all: portrait frames check

check:
	$(PY) scripts/validation/check_assets.py

clean:
	rm -rf assets/preview/*
