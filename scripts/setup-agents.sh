#!/bin/bash
# Setup AI Agents for the framework
# Configures directories and symlinks for multiple AI assistants

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$REPO_ROOT/.agent"
SKILLS_DIR="$AGENT_DIR/skills"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🤖 AI Framework Setup"
echo "====================="

# 1. Antigravity (native)
echo -e "${BLUE}Configuring Antigravity...${NC}"
mkdir -p "$AGENT_DIR/rules" "$AGENT_DIR/skills" "$AGENT_DIR/workflows"
echo -e "  ${GREEN}✓ .agent/ structure ready${NC}"

# 2. Claude Code support (.claude/skills -> .agent/skills)
echo -e "${BLUE}Configuring Claude Code support...${NC}"
mkdir -p "$REPO_ROOT/.claude"
if [ -L "$REPO_ROOT/.claude/skills" ]; then
    rm "$REPO_ROOT/.claude/skills"
fi
ln -s "$SKILLS_DIR" "$REPO_ROOT/.claude/skills"
cp "$REPO_ROOT/AGENTS.md" "$REPO_ROOT/CLAUDE.md"
echo -e "  ${GREEN}✓ .claude/skills linked${NC}"
echo -e "  ${GREEN}✓ AGENTS.md copied to CLAUDE.md${NC}"

# 3. GitHub Copilot instructions support
echo -e "${BLUE}Configuring GitHub Copilot instructions...${NC}"
mkdir -p "$REPO_ROOT/.github"
cp "$REPO_ROOT/AGENTS.md" "$REPO_ROOT/.github/copilot-instructions.md"
echo -e "  ${GREEN}✓ AGENTS.md copied to .github/copilot-instructions.md${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${YELLOW}Note: Restart your AI assistant to load the new context.${NC}"
