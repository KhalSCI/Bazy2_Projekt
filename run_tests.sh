#!/bin/bash
# Skrypt do uruchamiania testów dla Symulatora Giełdy

# Kolory
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Przejdź do katalogu projektu
cd "$(dirname "$0")"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Symulator Giełdy - Testy${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Sprawdź czy pytest jest zainstalowany
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest nie jest zainstalowany!${NC}"
    echo "Instaluję pytest..."
    pip install pytest pytest-cov -q
fi

# Parsuj argumenty
RUN_INTEGRATION=false
RUN_COVERAGE=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --integration|-i)
            RUN_INTEGRATION=true
            ;;
        --coverage|-c)
            RUN_COVERAGE=true
            ;;
        --verbose|-v)
            VERBOSE=true
            ;;
        --help|-h)
            echo "Użycie: ./run_tests.sh [opcje]"
            echo ""
            echo "Opcje:"
            echo "  -i, --integration  Uruchom również testy integracyjne (wymaga bazy danych)"
            echo "  -c, --coverage     Generuj raport pokrycia kodu"
            echo "  -v, --verbose      Szczegółowe wyjście"
            echo "  -h, --help         Pokaż tę pomoc"
            echo ""
            echo "Przykłady:"
            echo "  ./run_tests.sh              # Tylko testy jednostkowe"
            echo "  ./run_tests.sh -c           # Z raportem pokrycia"
            echo "  ./run_tests.sh -i           # Z testami integracyjnymi"
            echo "  ./run_tests.sh -i -c -v     # Wszystko"
            exit 0
            ;;
    esac
done

# Buduj komendę pytest
PYTEST_CMD="pytest"

if $VERBOSE; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if $RUN_COVERAGE; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing --cov-report=html"
fi

# Testy jednostkowe
echo -e "${GREEN}[1/2] Uruchamiam testy jednostkowe...${NC}"
echo ""

$PYTEST_CMD tests/test_validators.py tests/test_services.py tests/test_procedures.py

UNIT_EXIT_CODE=$?

# Testy integracyjne (opcjonalnie)
if $RUN_INTEGRATION; then
    echo ""
    echo -e "${GREEN}[2/2] Uruchamiam testy integracyjne...${NC}"
    echo ""

    export RUN_INTEGRATION_TESTS=1
    $PYTEST_CMD tests/test_integration.py

    INTEGRATION_EXIT_CODE=$?
else
    echo ""
    echo -e "${YELLOW}[2/2] Testy integracyjne pominięte (użyj --integration aby uruchomić)${NC}"
    INTEGRATION_EXIT_CODE=0
fi

# Podsumowanie
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Podsumowanie${NC}"
echo -e "${YELLOW}========================================${NC}"

if [ $UNIT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Testy jednostkowe: PASSED${NC}"
else
    echo -e "${RED}✗ Testy jednostkowe: FAILED${NC}"
fi

if $RUN_INTEGRATION; then
    if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Testy integracyjne: PASSED${NC}"
    else
        echo -e "${RED}✗ Testy integracyjne: FAILED${NC}"
    fi
fi

if $RUN_COVERAGE; then
    echo ""
    echo -e "${GREEN}Raport pokrycia HTML: htmlcov/index.html${NC}"
fi

# Exit code
if [ $UNIT_EXIT_CODE -ne 0 ] || [ $INTEGRATION_EXIT_CODE -ne 0 ]; then
    exit 1
fi

exit 0
