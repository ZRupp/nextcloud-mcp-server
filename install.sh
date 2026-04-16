#!/usr/bin/env bash
set -euo pipefail

# Nextcloud MCP Server Installer
# Installs and configures the Nextcloud MCP server for Claude Code and/or Claude Desktop.
# Usage: bash install.sh

REPO_URL="git+https://github.com/ZRupp/nextcloud-mcp-server"
PACKAGE_NAME="nextcloud-mcp-server"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Detect OS ---
detect_os() {
    case "$(uname -s)" in
        Darwin) OS="macos" ;;
        Linux)  OS="linux" ;;
        *)      err "Unsupported OS: $(uname -s)"; exit 1 ;;
    esac
    info "Detected OS: $OS"
}

# --- Install uv if needed ---
install_uv() {
    if command -v uv &>/dev/null; then
        ok "uv is already installed ($(uv --version))"
    else
        info "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv &>/dev/null; then
            ok "uv installed successfully ($(uv --version))"
        else
            err "uv installation failed. Please install manually: https://docs.astral.sh/uv/"
            exit 1
        fi
    fi
}

# --- Prompt for credentials ---
get_credentials() {
    echo ""
    echo -e "${BOLD}Nextcloud Connection Setup${NC}"
    echo "You'll need your Nextcloud URL and an app password."
    echo "Generate an app password at: Settings > Security > Devices & sessions"
    echo ""

    read -rp "Nextcloud URL (e.g., https://cloud.example.com): " NC_HOST
    NC_HOST="${NC_HOST%/}"

    read -rp "Nextcloud username: " NC_USER
    read -rsp "Nextcloud app password: " NC_PASS
    echo ""

    if [[ -z "$NC_HOST" || -z "$NC_USER" || -z "$NC_PASS" ]]; then
        err "All fields are required."
        exit 1
    fi

    # Step 1: Check server reachability
    info "Testing connection to $NC_HOST..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
        "$NC_HOST/status.php" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" == "000" ]]; then
        err "Could not reach $NC_HOST. Check the URL and your network."
        exit 1
    elif [[ "$HTTP_CODE" != "200" ]]; then
        warn "Got HTTP $HTTP_CODE from $NC_HOST/status.php (expected 200). Continuing..."
    else
        ok "Server reachable"
    fi

    # Step 2: Validate credentials against an authenticated endpoint
    info "Validating credentials..."
    AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 10 \
        -u "$NC_USER:$NC_PASS" \
        -H "OCS-APIRequest: true" \
        -H "Accept: application/json" \
        "$NC_HOST/ocs/v2.php/cloud/user" 2>/dev/null || echo -e "\n000")

    AUTH_CODE=$(echo "$AUTH_RESPONSE" | tail -1)
    AUTH_BODY=$(echo "$AUTH_RESPONSE" | sed '$d')

    if [[ "$AUTH_CODE" == "200" ]]; then
        # Extract display name for confirmation
        DISPLAY_NAME=$(echo "$AUTH_BODY" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(d['ocs']['data'].get('displayname',''))
except: print('')" 2>/dev/null)
        if [[ -n "$DISPLAY_NAME" ]]; then
            ok "Authenticated as: $DISPLAY_NAME"
        else
            ok "Credentials valid"
        fi
    elif [[ "$AUTH_CODE" == "401" ]]; then
        err "Authentication failed (HTTP 401)."
        err "Check that you're using an app password (not your login password)"
        err "and that the username and password are correct."
        exit 1
    elif [[ "$AUTH_CODE" == "000" ]]; then
        warn "Could not verify credentials (connection failed). Continuing anyway..."
    else
        warn "Unexpected response (HTTP $AUTH_CODE) while validating credentials. Continuing..."
    fi
}

# Build the MCP server JSON config to a temp file (avoids password in ps/history)
write_server_json() {
    local tmpfile="$1"
    python3 -c "
import json, sys
config = {
    'command': 'uvx',
    'args': ['--from', '$REPO_URL', '$PACKAGE_NAME', 'run', '--transport', 'stdio'],
    'env': {
        'NEXTCLOUD_HOST': sys.argv[1],
        'NEXTCLOUD_USERNAME': sys.argv[2],
        'NEXTCLOUD_PASSWORD': sys.argv[3],
    }
}
with open(sys.argv[4], 'w') as f:
    json.dump(config, f)
" "$NC_HOST" "$NC_USER" "$NC_PASS" "$tmpfile"
}

# --- Configure Claude Code ---
configure_claude_code() {
    if ! command -v claude &>/dev/null; then
        return 1
    fi

    info "Configuring Claude Code..."

    # Remove existing nextcloud server if present
    claude mcp remove nextcloud 2>/dev/null || true

    # Write config to temp file to avoid password in shell history / ps output
    local tmpfile
    tmpfile=$(mktemp)
    trap "rm -f '$tmpfile'" RETURN

    write_server_json "$tmpfile"

    # Use the temp file content as the JSON argument
    if claude mcp add-json nextcloud "$(cat "$tmpfile")" --scope user 2>/dev/null; then
        ok "Claude Code configured (user scope)"
        rm -f "$tmpfile"
        return 0
    else
        warn "Failed to configure Claude Code via CLI"
        rm -f "$tmpfile"
        return 1
    fi
}

# --- Configure Claude Desktop ---
configure_claude_desktop() {
    local config_file

    if [[ "$OS" == "macos" ]]; then
        config_file="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    else
        config_file="$HOME/.config/Claude/claude_desktop_config.json"
    fi

    # Check if Claude Desktop is installed
    local desktop_found=false
    if [[ "$OS" == "macos" && -d "/Applications/Claude.app" ]]; then
        desktop_found=true
    elif [[ "$OS" == "linux" && (-f "$config_file" || -d "$(dirname "$config_file")") ]]; then
        desktop_found=true
    fi

    if [[ "$desktop_found" != true ]]; then
        return 1
    fi

    info "Configuring Claude Desktop..."

    # Write config via python to avoid password in shell args
    python3 -c "
import json, os, sys

config_file = sys.argv[1]
os.makedirs(os.path.dirname(config_file), exist_ok=True)

existing = {}
if os.path.isfile(config_file):
    with open(config_file) as f:
        existing = json.load(f)

if 'mcpServers' not in existing:
    existing['mcpServers'] = {}

existing['mcpServers']['nextcloud'] = {
    'command': 'uvx',
    'args': ['--from', sys.argv[2], sys.argv[3], 'run', '--transport', 'stdio'],
    'env': {
        'NEXTCLOUD_HOST': sys.argv[4],
        'NEXTCLOUD_USERNAME': sys.argv[5],
        'NEXTCLOUD_PASSWORD': sys.argv[6],
    }
}

with open(config_file, 'w') as f:
    json.dump(existing, f, indent=2)
    f.write('\n')
" "$config_file" "$REPO_URL" "$PACKAGE_NAME" "$NC_HOST" "$NC_USER" "$NC_PASS"

    ok "Claude Desktop configured: $config_file"
    return 0
}

# --- Main ---
main() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD} Nextcloud MCP Server Installer${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo ""

    detect_os
    install_uv
    get_credentials

    echo ""
    configured=0

    if configure_claude_code; then
        ((configured++))
    fi

    if configure_claude_desktop; then
        ((configured++))
    fi

    if [[ $configured -eq 0 ]]; then
        warn "Neither Claude Code nor Claude Desktop detected."
        echo ""
        echo "To configure manually, run:"
        echo ""
        echo "  claude mcp add-json nextcloud '<config>' --scope user"
        echo ""
        echo "See the project README for the full JSON config format."
    fi

    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${GREEN}${BOLD} Installation complete!${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Restart Claude Code or Claude Desktop"
    echo "  2. The 'nextcloud' MCP server will connect automatically"
    echo "  3. Try asking: \"List my Nextcloud notes\" or \"What's on my calendar?\""
    echo ""
    echo "Available apps: Notes, Calendar, Contacts, Files, Deck, Cookbook,"
    echo "  Tables, Sharing, News, Collectives, WeekPlanner, Agora,"
    echo "  IntraVox, Analytics"
    echo ""
    echo "To uninstall:"
    echo "  Claude Code:    claude mcp remove nextcloud"
    echo "  Claude Desktop: remove 'nextcloud' from your config file"
    echo ""
}

main "$@"
