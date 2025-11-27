#!/bin/bash
# Scrat-Backup - Development-Hilfsskript
# Nützliche Befehle für die Entwicklung

set -e  # Bei Fehler abbrechen

VENV="venv/bin"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

function success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function error() {
    echo -e "${RED}❌ $1${NC}"
}

function warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Hilfe anzeigen
if [ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ -z "$1" ]; then
    echo "Scrat-Backup - Development-Hilfsskript"
    echo ""
    echo "Verwendung: ./dev.sh <command>"
    echo ""
    echo "Verfügbare Befehle:"
    echo "  format       - Code automatisch formatieren (black + isort)"
    echo "  check        - Code-Quality prüfen (black + flake8 + mypy + isort)"
    echo "  test         - Tests ausführen (pytest)"
    echo "  coverage     - Tests mit Coverage-Report"
    echo "  lint         - Nur Linting (flake8)"
    echo "  types        - Nur Type-Checking (mypy)"
    echo "  run          - Programm starten"
    echo "  clean        - Aufräumen (__pycache__, .pyc, etc.)"
    echo "  install      - Dependencies installieren"
    echo "  help         - Diese Hilfe anzeigen"
    echo ""
    exit 0
fi

# Code formatieren
if [ "$1" == "format" ]; then
    header "Code formatieren"
    echo "Running isort..."
    $VENV/isort src/ tests/
    success "isort abgeschlossen"

    echo ""
    echo "Running black..."
    $VENV/black src/ tests/
    success "black abgeschlossen"

    echo ""
    success "Code-Formatierung abgeschlossen!"
    exit 0
fi

# Code-Quality prüfen
if [ "$1" == "check" ]; then
    header "Code-Quality Checks"

    echo "1️⃣  black --check..."
    if $VENV/black --check src/ tests/; then
        success "black: Alle Dateien korrekt formatiert"
    else
        error "black: Formatierungsfehler gefunden"
        exit 1
    fi

    echo ""
    echo "2️⃣  isort --check..."
    if $VENV/isort --check-only src/ tests/; then
        success "isort: Imports korrekt sortiert"
    else
        error "isort: Import-Sortierung inkorrekt"
        exit 1
    fi

    echo ""
    echo "3️⃣  flake8..."
    if $VENV/flake8 src/ tests/; then
        success "flake8: Keine Style-Probleme"
    else
        error "flake8: Style-Probleme gefunden"
        exit 1
    fi

    echo ""
    echo "4️⃣  mypy..."
    if $VENV/mypy src/; then
        success "mypy: Keine Type-Probleme"
    else
        error "mypy: Type-Probleme gefunden"
        exit 1
    fi

    echo ""
    success "Alle Checks bestanden! 🎉"
    exit 0
fi

# Tests ausführen
if [ "$1" == "test" ]; then
    header "Tests ausführen"
    $VENV/pytest tests/ -v
    exit 0
fi

# Tests mit Coverage
if [ "$1" == "coverage" ]; then
    header "Tests mit Coverage"
    $VENV/pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    echo ""
    success "Coverage-Report erstellt: htmlcov/index.html"
    exit 0
fi

# Nur Linting
if [ "$1" == "lint" ]; then
    header "Linting (flake8)"
    $VENV/flake8 src/ tests/
    success "Linting abgeschlossen"
    exit 0
fi

# Nur Type-Checking
if [ "$1" == "types" ]; then
    header "Type-Checking (mypy)"
    $VENV/mypy src/
    success "Type-Checking abgeschlossen"
    exit 0
fi

# Programm starten
if [ "$1" == "run" ]; then
    header "Scrat-Backup starten"
    $VENV/python src/main.py
    exit 0
fi

# Aufräumen
if [ "$1" == "clean" ]; then
    header "Aufräumen"
    echo "Lösche __pycache__, .pyc, .pyo, etc."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".coverage" -delete 2>/dev/null || true
    success "Aufräumen abgeschlossen"
    exit 0
fi

# Dependencies installieren
if [ "$1" == "install" ]; then
    header "Dependencies installieren"
    $VENV/pip install -r requirements.txt
    success "Installation abgeschlossen"
    exit 0
fi

# Unbekannter Befehl
error "Unbekannter Befehl: $1"
echo "Nutze './dev.sh help' für Hilfe"
exit 1
