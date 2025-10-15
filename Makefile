PYTHON ?= python3
DATA_DIR := data

TEST_URL  := https://drive.usercontent.google.com/download?id=19hd7xfTrrP_isuUJwyqj_r1iLxT7X1nK&export=download&authuser=0&confirm=t&uuid=f154999d-ed7b-493f-972a-b34ec3a75ef0&at=AENtkXZy2CKiVtlVDssRTY02i61s%3A1730315886898
CALIB_URL := https://drive.usercontent.google.com/download?id=1Zclv8r_iwMgEiikKZMuZvAPSGbqn796x&export=download&authuser=0

TEST_FILE  := $(DATA_DIR)/test.csv
CALIB_FILE := $(DATA_DIR)/calib2.csv

.PHONY: all download clean redownload install prepare tk test telebot

all: download

download: $(TEST_FILE) $(CALIB_FILE)
	@echo "✓ test.csv and calib2.csv are in $(DATA_DIR)/"

$(DATA_DIR):
	mkdir -p $@

$(TEST_FILE): | $(DATA_DIR)
	@echo "↓ test.csv"
	curl -L --fail --retry 5 --progress-bar "$(TEST_URL)" -o "$@.part" && mv "$@.part" "$@"
	@echo "✓ $@"

$(CALIB_FILE): | $(DATA_DIR)
	@echo "↓ calib2.csv"
	curl -L --fail --retry 5 --progress-bar "$(CALIB_URL)" -o "$@.part" && mv "$@.part" "$@"
	@echo "✓ $@"

redownload:
	rm -f $(TEST_FILE) $(CALIB_FILE)
	$(MAKE) download

clean:
	rm -rf "$(DATA_DIR)"

PIP ?= pip3

install: requirements.txt
	@echo "→ Installing Python dependencies system-wide (via $(PIP))"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	sudo apt install -y python3-tk
	@echo "✓ Dependencies installed."

PREP_SCRIPTS := $(addprefix preparation,$(addsuffix .py,1 2 3 4 5))

prepare: install $(PREP_SCRIPTS)
	@set -e; \
	for s in $(PREP_SCRIPTS); do \
		echo "→ Running $(PYTHON) $$s"; \
		$(PYTHON) "$$s"; \
	done
	@echo "✓ Preparation complete"

tk: install tktktk.py
	@echo "→ Running Tkinter GUI"
	$(PYTHON) tktktk.py


test: install algdetect.py
	@echo "→ Running algdetect test"
	$(PYTHON) algdetect.py


telebot: install preparationNEWNEWNEW.py tgbotfinal.py
	echo "→ Starting Telegram bot"; \
	$(PYTHON) tgbotfinal.py