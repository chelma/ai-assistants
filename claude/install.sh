#!/usr/bin/env bash

# Claude Code Configuration Installer
#
# This script creates symlinks from ~/.claude/ to your ai-assistants git repository,
# enabling version-controlled management of Claude Code configuration.
#
# Any changes made in ~/.claude/ will automatically reflect in the ai-assistants repo
# (and vice versa), allowing you to track and commit configuration changes.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Claude Code Configuration Installer${NC}"
echo "======================================"
echo ""

# Ensure ~/.claude exists
if [ ! -d "${CLAUDE_HOME}" ]; then
    echo -e "${YELLOW}Creating ${CLAUDE_HOME} directory...${NC}"
    mkdir -p "${CLAUDE_HOME}"
fi

# Create directories in ai-assistants repo if they don't exist
echo -e "${BLUE}Ensuring directory structure exists...${NC}"
for dir in skills commands memories agents workspace; do
    if [ ! -d "${SCRIPT_DIR}/${dir}" ]; then
        echo -e "${YELLOW}Creating ${SCRIPT_DIR}/${dir}${NC}"
        mkdir -p "${SCRIPT_DIR}/${dir}"
    fi
done

# Create template files if they don't exist
if [ ! -f "${SCRIPT_DIR}/settings.json" ]; then
    echo -e "${YELLOW}Creating template ${SCRIPT_DIR}/settings.json${NC}"
    cat > "${SCRIPT_DIR}/settings.json" << 'EOF'
{
  "permissions": {},
  "env": {}
}
EOF
fi

if [ ! -f "${SCRIPT_DIR}/CLAUDE.md" ]; then
    echo -e "${YELLOW}Creating template ${SCRIPT_DIR}/CLAUDE.md${NC}"
    cat > "${SCRIPT_DIR}/CLAUDE.md" << 'EOF'
# Claude Code User-Level Instructions

This file is loaded at the start of every Claude Code session.

Add global instructions, preferences, or context here that should apply across all your projects.

## Example Usage

- Coding style preferences
- Common abbreviations or terminology
- Default behaviors you prefer
- Links to personal documentation

EOF
fi

if [ ! -f "${SCRIPT_DIR}/.mcp.json" ]; then
    echo -e "${YELLOW}Creating template ${SCRIPT_DIR}/.mcp.json${NC}"
    cat > "${SCRIPT_DIR}/.mcp.json" << 'EOF'
{
  "mcpServers": {}
}
EOF
fi

# Function to create directory symlink safely
create_dir_symlink() {
    local source_dir="$1"
    local target_link="$2"
    local dir_name="$3"

    echo ""
    echo -e "${BLUE}Processing directory: ${dir_name}${NC}"

    # Check if target is already a symlink pointing to the correct location
    if [ -L "${target_link}" ]; then
        current_target=$(readlink "${target_link}")
        if [ "${current_target}" = "${source_dir}" ]; then
            echo -e "${GREEN}✓ Already symlinked correctly${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Symlink exists but points to different location:${NC}"
            echo -e "  Current: ${current_target}"
            echo -e "  Expected: ${source_dir}"
            read -p "Replace with correct symlink? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Skipping ${dir_name}${NC}"
                return 0
            fi
            rm "${target_link}"
        fi
    # Check if target exists as a regular directory
    elif [ -d "${target_link}" ]; then
        echo -e "${YELLOW}⚠ Directory exists at ${target_link}${NC}"

        # Check if directory is empty
        if [ -z "$(ls -A "${target_link}")" ]; then
            echo -e "${YELLOW}Directory is empty, removing...${NC}"
            rmdir "${target_link}"
        else
            echo -e "${YELLOW}Directory contains files:${NC}"
            ls -la "${target_link}"
            echo ""
            echo "Options:"
            echo "  1) Backup and replace with symlink (moves to ${target_link}.backup)"
            echo "  2) Skip this directory"
            read -p "Choose (1 or 2): " -n 1 -r
            echo
            if [[ $REPLY == "1" ]]; then
                backup="${target_link}.backup.$(date +%Y%m%d_%H%M%S)"
                echo -e "${YELLOW}Backing up to ${backup}${NC}"
                mv "${target_link}" "${backup}"
                echo -e "${GREEN}✓ Backed up${NC}"
            else
                echo -e "${YELLOW}Skipping ${dir_name}${NC}"
                return 0
            fi
        fi
    # Check if target exists as a file (shouldn't happen, but handle it)
    elif [ -e "${target_link}" ]; then
        echo -e "${RED}✗ File exists at ${target_link} (expected directory)${NC}"
        echo -e "${YELLOW}Skipping ${dir_name}${NC}"
        return 0
    fi

    # Create the symlink
    echo -e "${BLUE}Creating symlink...${NC}"
    ln -s "${source_dir}" "${target_link}"
    echo -e "${GREEN}✓ Symlinked: ${target_link} → ${source_dir}${NC}"
}

# Function to create file symlink safely
create_file_symlink() {
    local source_file="$1"
    local target_link="$2"
    local file_name="$3"

    echo ""
    echo -e "${BLUE}Processing file: ${file_name}${NC}"

    # Check if target is already a symlink pointing to the correct location
    if [ -L "${target_link}" ]; then
        current_target=$(readlink "${target_link}")
        if [ "${current_target}" = "${source_file}" ]; then
            echo -e "${GREEN}✓ Already symlinked correctly${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Symlink exists but points to different location:${NC}"
            echo -e "  Current: ${current_target}"
            echo -e "  Expected: ${source_file}"
            read -p "Replace with correct symlink? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Skipping ${file_name}${NC}"
                return 0
            fi
            rm "${target_link}"
        fi
    # Check if target exists as a regular file
    elif [ -f "${target_link}" ]; then
        echo -e "${YELLOW}⚠ File exists at ${target_link}${NC}"
        echo "Options:"
        echo "  1) Backup and replace with symlink (moves to ${target_link}.backup)"
        echo "  2) Skip this file"
        read -p "Choose (1 or 2): " -n 1 -r
        echo
        if [[ $REPLY == "1" ]]; then
            backup="${target_link}.backup.$(date +%Y%m%d_%H%M%S)"
            echo -e "${YELLOW}Backing up to ${backup}${NC}"
            mv "${target_link}" "${backup}"
            echo -e "${GREEN}✓ Backed up${NC}"
        else
            echo -e "${YELLOW}Skipping ${file_name}${NC}"
            return 0
        fi
    # Check if target exists as a directory (shouldn't happen, but handle it)
    elif [ -d "${target_link}" ]; then
        echo -e "${RED}✗ Directory exists at ${target_link} (expected file)${NC}"
        echo -e "${YELLOW}Skipping ${file_name}${NC}"
        return 0
    fi

    # Create the symlink
    echo -e "${BLUE}Creating symlink...${NC}"
    ln -s "${source_file}" "${target_link}"
    echo -e "${GREEN}✓ Symlinked: ${target_link} → ${source_file}${NC}"
}

# Create symlinks for directories
create_dir_symlink "${SCRIPT_DIR}/skills" "${CLAUDE_HOME}/skills" "Skills"
create_dir_symlink "${SCRIPT_DIR}/commands" "${CLAUDE_HOME}/commands" "Commands"
create_dir_symlink "${SCRIPT_DIR}/memories" "${CLAUDE_HOME}/memories" "Memories"
create_dir_symlink "${SCRIPT_DIR}/agents" "${CLAUDE_HOME}/agents" "Custom Agents"
create_dir_symlink "${SCRIPT_DIR}/workspace" "${CLAUDE_HOME}/workspace" "Workspace"

# Create symlinks for files
create_file_symlink "${SCRIPT_DIR}/settings.json" "${CLAUDE_HOME}/settings.json" "settings.json"
create_file_symlink "${SCRIPT_DIR}/CLAUDE.md" "${CLAUDE_HOME}/CLAUDE.md" "CLAUDE.md"
create_file_symlink "${SCRIPT_DIR}/.mcp.json" "${CLAUDE_HOME}/.mcp.json" ".mcp.json"

echo ""
echo -e "${GREEN}======================================"
echo -e "Installation Complete!${NC}"
echo ""
echo "Your Claude Code configuration is now symlinked to:"
echo "  ${SCRIPT_DIR}"
echo ""
echo "Symlinked items:"
echo "  📁 Directories: skills, commands, memories, agents, workspace"
echo "  📄 Files: settings.json, CLAUDE.md, .mcp.json"
echo ""
echo "Any changes in ~/.claude/ will automatically reflect in your"
echo "git repository, and vice versa. Remember to commit changes!"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. cd ${SCRIPT_DIR}"
echo "  2. git status  # Check what's changed"
echo "  3. git add .   # Stage your configuration"
echo "  4. git commit  # Commit your changes"
echo ""
echo -e "${YELLOW}Note:${NC} Template files were created if they didn't exist."
echo "Review and customize:"
echo "  - settings.json: Global permissions and environment variables"
echo "  - CLAUDE.md: User-level instructions for all sessions"
echo "  - .mcp.json: MCP server configuration"
echo ""
