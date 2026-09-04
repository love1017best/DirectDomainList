#!/bin/bash
# Build script: preprocess and convert domain list to YAML

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIST_FILE="${SCRIPT_DIR}/DirectDomain.list"
YAML_FILE="${SCRIPT_DIR}/DirectDomain.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Domain List Build Script${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check if list file exists
if [ ! -f "$LIST_FILE" ]; then
    echo -e "${RED}Error: $LIST_FILE not found${NC}"
    exit 1
fi

# Step 1: Preprocess (deduplicate + validate)
echo ""
echo -e "${GREEN}[1/2] Running preprocessor...${NC}"
python3 "${SCRIPT_DIR}/preprocess_list.py" "$LIST_FILE" -d -v --inplace

# Step 2: Convert to YAML
echo ""
echo -e "${GREEN}[2/2] Converting to YAML...${NC}"
python3 "${SCRIPT_DIR}/convert_list_to_yaml.py" "$LIST_FILE" "$YAML_FILE"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build complete!${NC}"
echo -e "${GREEN}  Output: $YAML_FILE${NC}"
echo -e "${GREEN}========================================${NC}"
