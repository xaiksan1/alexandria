#!/bin/bash

# ALEXANDRIA SEARCH SCRIPT
# Usage: ./find_in_alexandria.sh "search_term"
# Purpose: Find ANY file in Alexandria ecosystem instantly

set -e

SEARCH_TERM="${1:-.}"
ALEXANDRIA_HOME="/home/ichigo/alexandria"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 ALEXANDRIA SEARCH${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "Search Term: ${YELLOW}${SEARCH_TERM}${NC}"
echo -e "Location: ${YELLOW}${ALEXANDRIA_HOME}${NC}"
echo ""

# 1. EXACT FILENAME MATCHES (Fastest)
echo -e "${GREEN}📁 EXACT FILENAME MATCHES${NC}"
EXACT_MATCHES=$(find "${ALEXANDRIA_HOME}" -type f -name "*${SEARCH_TERM}*" 2>/dev/null | grep -v __pycache__ | grep -v node_modules | grep -v ".venv" | head -10)

if [ -z "$EXACT_MATCHES" ]; then
    echo -e "${RED}   ✗ No exact filename matches${NC}"
else
    echo "$EXACT_MATCHES" | while read -r file; do
        # Get file size and type
        SIZE=$(du -h "$file" | cut -f1)
        echo -e "   ✅ ${GREEN}$(basename "$file")${NC} (${SIZE})"
        echo -e "      ${BLUE}${file#$ALEXANDRIA_HOME/}${NC}"
    done
fi

echo ""

# 2. DIRECTORY MATCHES
echo -e "${GREEN}📂 DIRECTORY MATCHES${NC}"
DIR_MATCHES=$(find "${ALEXANDRIA_HOME}" -type d -name "*${SEARCH_TERM}*" 2>/dev/null | grep -v __pycache__ | grep -v node_modules | grep -v ".venv" | head -10)

if [ -z "$DIR_MATCHES" ]; then
    echo -e "${RED}   ✗ No directory matches${NC}"
else
    echo "$DIR_MATCHES" | while read -r dir; do
        FILE_COUNT=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo -e "   ✅ ${GREEN}$(basename "$dir")/${NC} (${FILE_COUNT} files)"
        echo -e "      ${BLUE}${dir#$ALEXANDRIA_HOME/}${NC}"
    done
fi

echo ""

# 3. CONTENT MATCHES (grep - slower but thorough)
echo -e "${GREEN}🔎 CONTENT MATCHES (in .md, .txt, .py files)${NC}"
CONTENT_MATCHES=$(grep -r "${SEARCH_TERM}" "${ALEXANDRIA_HOME}" \
    --include="*.md" \
    --include="*.txt" \
    --include="*.py" \
    2>/dev/null | \
    grep -v __pycache__ | \
    grep -v node_modules | \
    cut -d: -f1 | \
    sort -u | \
    head -5)

if [ -z "$CONTENT_MATCHES" ]; then
    echo -e "${RED}   ✗ No content matches${NC}"
else
    echo "$CONTENT_MATCHES" | while read -r file; do
        MATCHES=$(grep -c "${SEARCH_TERM}" "$file" 2>/dev/null || echo "0")
        echo -e "   ✅ ${GREEN}$(basename "$file")${NC} (${MATCHES} occurrences)"
        echo -e "      ${BLUE}${file#$ALEXANDRIA_HOME/}${NC}"
    done
fi

echo ""

# 4. QUICK REFERENCE GUIDE
echo -e "${GREEN}💡 QUICK REFERENCE${NC}"
echo -e "   CV Materials:        ${YELLOW}cd ${ALEXANDRIA_HOME}/ADAM/CV_AND_PORTFOLIO/${NC}"
echo -e "   Main Systems:        ${YELLOW}ls -la ${ALEXANDRIA_HOME}/${NC}"
echo -e "   Search by system:    ${YELLOW}./find_in_alexandria.sh FILMMAKER${NC}"
echo -e "   View index:          ${YELLOW}cat ${ALEXANDRIA_HOME}/ALEXANDRIA_COMPLETE_INDEX.md${NC}"
echo ""

# 5. SUGGESTIONS IF NO MATCH
if [ -z "$EXACT_MATCHES" ] && [ -z "$DIR_MATCHES" ] && [ -z "$CONTENT_MATCHES" ]; then
    echo -e "${YELLOW}⚠️  NO MATCHES FOUND${NC}"
    echo ""
    echo "Try searching for:"
    echo "  - System names: FILMMAKER, ADAM, PAPER2AGENT, NOSFERATU"
    echo "  - Document types: CV, PITCH, INTERVIEW, ARCHITECTURE"
    echo "  - File types: .md, .py, .sh"
    echo ""
    echo "Or view the complete index:"
    echo -e "  ${YELLOW}cat /home/ichigo/alexandria/ALEXANDRIA_COMPLETE_INDEX.md${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
