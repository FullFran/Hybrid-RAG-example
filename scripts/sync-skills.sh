#!/bin/bash
# Sync skill metadata to agent profiles
# This version detects which agents are active and only syncs those.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/.agent/skills"
AGENTS_MD="$REPO_ROOT/AGENTS.md"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Flags
SYNC_ALL=false
SYNC_OPENCODE=false
SYNC_CLAUDE=false
SYNC_CURSOR=false
SYNC_COPILOT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --all) SYNC_ALL=true; shift ;;
    --opencode) SYNC_OPENCODE=true; shift ;;
    --claude) SYNC_CLAUDE=true; shift ;;
    --cursor) SYNC_CURSOR=true; shift ;;
    --copilot) SYNC_COPILOT=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# If no flags, auto-detect active agents
if [ "$SYNC_ALL" = false ] && [ "$SYNC_OPENCODE" = false ] && [ "$SYNC_CLAUDE" = false ] && [ "$SYNC_CURSOR" = false ] && [ "$SYNC_COPILOT" = false ]; then
    echo -e "${CYAN}Auto-detecting active agents...${NC}"
    [ -d "$REPO_ROOT/.opencode" ] && SYNC_OPENCODE=true
    [ -d "$REPO_ROOT/.claude" ] && SYNC_CLAUDE=true
    [ -L "$REPO_ROOT/.cursorrules" ] && SYNC_CURSOR=true
    [ -L "$REPO_ROOT/.github/copilot-instructions.md" ] && SYNC_COPILOT=true
fi

echo -e "${BLUE}Syncing skills to active profiles...${NC}"

# Extract YAML frontmatter field
extract_field() {
    local file="$1"
    local field="$2"
    # Only look at the first 20 lines to stay within frontmatter and avoid body matches
    head -n 20 "$file" | grep "^$field:" | head -n 1 | cut -d ':' -f 2- | sed 's/^[[:space:]]*//; s/^[">][[:space:]]*//'
}

# Validate skill against agentskills.io standard
validate_skill() {
    local skill_md="$1"
    local dir_name=$(basename "$(dirname "$skill_md")")
    local name=$(extract_field "$skill_md" "name")
    local desc=$(extract_field "$skill_md" "description")

    # 1. Check if name matches directory
    if [ "$name" != "$dir_name" ]; then
        echo -e "${RED}Error: Skill name '$name' does not match directory '$dir_name' in $skill_md${NC}"
        return 1
    fi

    # 2. Check name format (lowercase alphanumeric and hyphens only)
    if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
        echo -e "${RED}Error: Invalid skill name format '$name' in $skill_md. Must be lowercase alphanumeric and hyphens only.${NC}"
        return 1
    fi

    # 3. Check description length
    if [ ${#desc} -gt 1024 ]; then
        echo -e "${RED}Error: Description too long in $skill_md (max 1024 chars).${NC}"
        return 1
    fi

    if [ -z "$desc" ]; then
        echo -e "${RED}Error: Description is empty in $skill_md.${NC}"
        return 1
    fi

    return 0
}

# Temporary file for the table
TEMP_TABLE=$(mktemp)

# Headers
echo "| Skill | Description | URL |" > "$TEMP_TABLE"
echo "|-------|-------------|-----|" >> "$TEMP_TABLE"

# Loop through skills
for skill_md in $(find "$SKILLS_DIR" -name "SKILL.md" | sort); do
    if ! validate_skill "$skill_md"; then
        echo -e "${YELLOW}Skipping invalid skill: $skill_md${NC}"
        continue
    fi
    
    skill_name=$(extract_field "$skill_md" "name")
    skill_desc=$(extract_field "$skill_md" "description" | head -n 1)
    # Get path relative to the root
    skill_rel_path=".agent/skills/$(basename "$(dirname "$skill_md")")/SKILL.md"
    
    echo "| \`$skill_name\` | $skill_desc | [$skill_rel_path]($skill_rel_path) |" >> "$TEMP_TABLE"
done

# 1. Always update AGENTS.md (Source of Truth)
echo -e "${BLUE}Updating AGENTS.md (Source of Truth)...${NC}"
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
        if [[ "$line" =~ ^\| ]] || [[ "$line" == "" ]]; then continue; else IN_TABLE=0; fi
    fi
    if [ $IN_TABLE -eq 0 ]; then echo "$line" >> "$NEW_AGENTS"; fi
done < "$AGENTS_MD"
mv "$NEW_AGENTS" "$AGENTS_MD"

# 2. Sync OpenCode if active
if [ "$SYNC_OPENCODE" = true ]; then
    echo -e "${BLUE}Syncing OpenCode (.opencode/)...${NC}"
    mkdir -p "$REPO_ROOT/.opencode/skills" "$REPO_ROOT/.opencode/agents" "$REPO_ROOT/.opencode/commands"
    
    # Skills
    for skill in "$SKILLS_DIR"/*/; do
        if [ -d "$skill" ]; then
            skill_name=$(basename "$skill")
            ln -sf "../../.agent/skills/$skill_name" "$REPO_ROOT/.opencode/skills/$skill_name"
        fi
    done

    # Agents (Output Styles)
    for agent in "$AGENT_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent")
            ln -sf "../../.agent/agents/$agent_name" "$REPO_ROOT/.opencode/agents/$agent_name"
        fi
    done

    # Commands (Workflows)
    for wf in "$AGENT_DIR/workflows"/*.md; do
        if [ -f "$wf" ]; then
            wf_name=$(basename "$wf")
            ln -sf "../../.agent/workflows/$wf_name" "$REPO_ROOT/.opencode/commands/$wf_name"
        fi
    done
fi

# 3. Sync Claude if active
if [ "$SYNC_CLAUDE" = true ]; then
    echo -e "${BLUE}Syncing Claude Code (.claude/)...${NC}"
    mkdir -p "$REPO_ROOT/.claude"
    [ -L "$REPO_ROOT/.claude/skills" ] || ln -sf "../.agent/skills" "$REPO_ROOT/.claude/skills"
    # CLAUDE.md is a symlink now, so it updates automatically with AGENTS.md
fi

rm "$TEMP_TABLE"

echo -e "${GREEN}✅ Sync complete!${NC}"
echo -e "   Profiles updated: $( [ "$SYNC_OPENCODE" = true ] && echo -n "opencode " )$( [ "$SYNC_CLAUDE" = true ] && echo -n "claude " )$( [ "$SYNC_CURSOR" = true ] && echo -n "cursor " )$( [ "$SYNC_COPILOT" = true ] && echo -n "copilot " )"
