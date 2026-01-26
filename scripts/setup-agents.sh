#!/bin/bash
# Setup AI Agents for the framework
# Generates local config from the source of truth (.agent/ + AGENTS.md)
# Each developer runs this to configure their preferred agent(s)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$REPO_ROOT/.agent"
SKILLS_DIR="$AGENT_DIR/skills"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Available agents
AGENTS=("opencode" "claude" "copilot" "cursor" "antigravity")

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}🤖 Agents Config Setup${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "Source of truth: ${GREEN}AGENTS.md${NC} + ${GREEN}.agent/${NC}"
    echo ""
}

print_menu() {
    echo -e "${BOLD}Select agents to configure:${NC}"
    echo ""
    echo -e "  ${CYAN}1)${NC} opencode    - OpenCode TUI (.opencode/)"
    echo -e "  ${CYAN}2)${NC} claude      - Claude Code (.claude/ + CLAUDE.md)"
    echo -e "  ${CYAN}3)${NC} copilot     - GitHub Copilot (.github/copilot-instructions.md)"
    echo -e "  ${CYAN}4)${NC} cursor      - Cursor IDE (.cursorrules)"
    echo -e "  ${CYAN}5)${NC} antigravity - Antigravity IDE (GEMINI.md)"
    echo ""
    echo -e "  ${CYAN}a)${NC} all         - Configure all agents"
    echo -e "  ${CYAN}q)${NC} quit        - Exit"
    echo ""
}

setup_opencode() {
    echo -e "${BLUE}Configuring OpenCode TUI...${NC}"
    
    # Create directories
    mkdir -p "$REPO_ROOT/.opencode/skills" "$REPO_ROOT/.opencode/agents" "$REPO_ROOT/.opencode/commands"
    
    # Create symlinks for each skill
    for skill in "$SKILLS_DIR"/*/; do
        if [ -d "$skill" ]; then
            skill_name=$(basename "$skill")
            target_link="$REPO_ROOT/.opencode/skills/$skill_name"
            [ -L "$target_link" ] && rm "$target_link"
            ln -sf "../../.agent/skills/$skill_name" "$target_link"
        fi
    done

    # Create symlinks for each agent persona
    for agent in "$AGENT_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent")
            target_link="$REPO_ROOT/.opencode/agents/$agent_name"
            [ -L "$target_link" ] && rm "$target_link"
            ln -sf "../../.agent/agents/$agent_name" "$target_link"
        fi
    done

    # Create symlinks for workflows (Commands in OpenCode)
    for wf in "$AGENT_DIR/workflows"/*.md; do
        if [ -f "$wf" ]; then
            wf_name=$(basename "$wf")
            target_link="$REPO_ROOT/.opencode/commands/$wf_name"
            [ -L "$target_link" ] && rm "$target_link"
            ln -sf "../../.agent/workflows/$wf_name" "$target_link"
        fi
    done
    
    # Create opencode.json if it doesn't exist
    if [ ! -f "$REPO_ROOT/opencode.json" ]; then
        cat > "$REPO_ROOT/opencode.json" << 'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "AGENTS.md",
    ".agent/rules/*.md"
  ],
  "permission": {
    "skill": {
      "*": "allow"
    },
    "bash": {
      "*": "allow",
      "git commit *": "ask",
      "git push *": "ask",
      "git push": "ask",
      "git push --force *": "ask",
      "git rebase *": "ask",
      "git reset --hard *": "ask"
    },
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "**/.env": "deny",
      "**/.env.*": "deny",
      "**/secrets/**": "deny",
      "**/credentials.json": "deny"
    }
  }
}
EOF
    fi
    
    echo -e "  ${GREEN}✓${NC} .opencode/skills/ linked"
    echo -e "  ${GREEN}✓${NC} .opencode/agents/ linked"
    echo -e "  ${GREEN}✓${NC} opencode.json ready"
}

setup_claude() {
    echo -e "${BLUE}Configuring Claude Code...${NC}"
    
    # Create directory and symlink for skills
    mkdir -p "$REPO_ROOT/.claude"
    [ -L "$REPO_ROOT/.claude/skills" ] && rm "$REPO_ROOT/.claude/skills"
    ln -sf "../.agent/skills" "$REPO_ROOT/.claude/skills"
    
    # Symlink AGENTS.md to CLAUDE.md (auto-sync!)
    [ -L "$REPO_ROOT/CLAUDE.md" ] && rm "$REPO_ROOT/CLAUDE.md"
    [ -f "$REPO_ROOT/CLAUDE.md" ] && rm "$REPO_ROOT/CLAUDE.md"
    ln -sf "AGENTS.md" "$REPO_ROOT/CLAUDE.md"
    
    echo -e "  ${GREEN}✓${NC} .claude/skills/ → .agent/skills/"
    echo -e "  ${GREEN}✓${NC} CLAUDE.md → AGENTS.md (symlink)"
}

setup_copilot() {
    echo -e "${BLUE}Configuring GitHub Copilot...${NC}"
    
    mkdir -p "$REPO_ROOT/.github"
    [ -L "$REPO_ROOT/.github/copilot-instructions.md" ] && rm "$REPO_ROOT/.github/copilot-instructions.md"
    [ -f "$REPO_ROOT/.github/copilot-instructions.md" ] && rm "$REPO_ROOT/.github/copilot-instructions.md"
    ln -sf "../AGENTS.md" "$REPO_ROOT/.github/copilot-instructions.md"
    
    echo -e "  ${GREEN}✓${NC} .github/copilot-instructions.md → AGENTS.md (symlink)"
}

setup_cursor() {
    echo -e "${BLUE}Configuring Cursor IDE...${NC}"
    
    # Symlink AGENTS.md to .cursorrules
    [ -L "$REPO_ROOT/.cursorrules" ] && rm "$REPO_ROOT/.cursorrules"
    [ -f "$REPO_ROOT/.cursorrules" ] && rm "$REPO_ROOT/.cursorrules"
    ln -sf "AGENTS.md" "$REPO_ROOT/.cursorrules"
    
    echo -e "  ${GREEN}✓${NC} .cursorrules → AGENTS.md (symlink)"
}

setup_antigravity() {
    echo -e "${BLUE}Configuring Antigravity IDE...${NC}"
    
    # Antigravity uses GEMINI.md for the UI Customizations panel
    [ -L "$REPO_ROOT/GEMINI.md" ] && rm "$REPO_ROOT/GEMINI.md"
    [ -f "$REPO_ROOT/GEMINI.md" ] && rm "$REPO_ROOT/GEMINI.md"
    ln -sf "AGENTS.md" "$REPO_ROOT/GEMINI.md"

    # Link agent personas to rules so Antigravity can load them as instructions
    mkdir -p "$AGENT_DIR/rules"
    for agent in "$AGENT_DIR/agents"/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent")
            target_link="$AGENT_DIR/rules/persona-$agent_name"
            [ -L "$target_link" ] && rm "$target_link"
            ln -sf "../agents/$agent_name" "$target_link"
        fi
    done
    
    echo -e "  ${GREEN}✓${NC} GEMINI.md → AGENTS.md (symlink)"
    echo -e "  ${GREEN}✓${NC} .agent/agents/ linked to rules for persona support"
    echo -e "  ${GREEN}✓${NC} .agent/ structure is native to Antigravity"
}

setup_all() {
    setup_opencode
    setup_claude
    setup_copilot
    setup_cursor
    setup_antigravity
}

# Check if AGENTS.md exists
if [ ! -f "$REPO_ROOT/AGENTS.md" ]; then
    echo -e "${RED}Error: AGENTS.md not found in project root.${NC}"
    echo -e "This file is the source of truth for agent configuration."
    exit 1
fi

# Parse command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        --all|-a)
            print_header
            setup_all
            echo ""
            echo -e "${GREEN}${BOLD}✅ All agents configured!${NC}"
            exit 0
            ;;
        --opencode)
            setup_opencode
            exit 0
            ;;
        --claude)
            setup_claude
            exit 0
            ;;
        --copilot)
            setup_copilot
            exit 0
            ;;
        --cursor)
            setup_cursor
            exit 0
            ;;
        --antigravity|--gemini)
            setup_antigravity
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all, -a        Configure all agents"
            echo "  --opencode       Configure OpenCode TUI only"
            echo "  --claude         Configure Claude Code only"
            echo "  --copilot        Configure GitHub Copilot only"
            echo "  --cursor         Configure Cursor IDE only"
            echo "  --antigravity    Configure Antigravity IDE only"
            echo "  --help, -h       Show this help"
            echo ""
            echo "Without options, runs interactive mode."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
fi

# Interactive mode
print_header
print_menu

while true; do
    read -p "$(echo -e ${CYAN}Enter choice [1-5/a/q]: ${NC})" choice
    
    case "$choice" in
        1) setup_opencode ;;
        2) setup_claude ;;
        3) setup_copilot ;;
        4) setup_cursor ;;
        5) setup_antigravity ;;
        a|A) setup_all ;;
        q|Q) 
            echo -e "${YELLOW}Exiting without changes.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Try again.${NC}"
            continue
            ;;
    esac
    
    echo ""
    read -p "$(echo -e ${CYAN}Configure another agent? [y/N]: ${NC})" again
    case "$again" in
        y|Y) 
            echo ""
            print_menu
            ;;
        *)
            break
            ;;
    esac
done

echo ""
echo -e "${GREEN}${BOLD}✅ Setup complete!${NC}"
echo -e "${YELLOW}Note: Restart your AI assistant to load the new context.${NC}"
echo ""
echo -e "These files are in ${CYAN}.gitignore${NC} - they won't be committed."
echo -e "Source of truth remains: ${GREEN}AGENTS.md${NC} + ${GREEN}.agent/${NC}"
