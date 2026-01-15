#!/bin/bash
# Sync skill metadata to AGENTS.md
# This version actually updates the file between markers.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/.agent/skills"
AGENTS_MD="$REPO_ROOT/AGENTS.md"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Syncing skills to AGENTS.md...${NC}"

# Extract YAML frontmatter field
extract_field() {
    local file="$1"
    local field="$2"
    grep "^$field:" "$file" | cut -d ':' -f 2- | sed 's/^[[:space:]]*//; s/^[">][[:space:]]*//'
}

# Temporary file for the table
TEMP_TABLE=$(mktemp)

# Headers
echo "| Skill | Description | URL |" > "$TEMP_TABLE"
echo "|-------|-------------|-----|" >> "$TEMP_TABLE"

# Loop through skills
for skill_md in $(find "$SKILLS_DIR" -name "SKILL.md" | sort); do
    skill_name=$(extract_field "$skill_md" "name")
    skill_desc=$(extract_field "$skill_md" "description" | head -n 1)
    # Get path relative to the root
    skill_rel_path=".agent/skills/$(basename "$(dirname "$skill_md")")/SKILL.md"
    
    echo "| \`$skill_name\` | $skill_desc | [$skill_rel_path]($skill_rel_path) |" >> "$TEMP_TABLE"
done

# We need to find the "Available Skills" section and replace the table under it.
# For simplicity in this lab environment, we will use a temp file to rewrite the AGENTS.md
NEW_AGENTS=$(mktemp)
IN_TABLE=0

while IFS= read -r line; do
    if [[ "$line" == "## Available Skills" ]]; then
        echo "$line" >> "$NEW_AGENTS"
        echo "" >> "$NEW_AGENTS"
        cat "$TEMP_TABLE" >> "$NEW_AGENTS"
        IN_TABLE=1
        continue
    fi
    
    if [ $IN_TABLE -eq 1 ]; then
        # Skip existing table lines
        if [[ "$line" =~ ^\| ]] || [[ "$line" == "" ]]; then
            continue
        else
            IN_TABLE=0
        fi
    fi
    
    if [ $IN_TABLE -eq 0 ]; then
        echo "$line" >> "$NEW_AGENTS"
    fi
done < "$AGENTS_MD"

mv "$NEW_AGENTS" "$AGENTS_MD"
rm "$TEMP_TABLE"

echo -e "${GREEN}✅ AGENTS.md updated successfully with $(find "$SKILLS_DIR" -name "SKILL.md" | wc -l) skills.${NC}"
