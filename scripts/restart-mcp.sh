#!/bin/bash

echo "🧹 Cleaning up existing Chrome and MCP processes..."

# Kill existing Chrome processes used by Playwright
pkill -f "chrome.*--remote-debugging-port" 2>/dev/null || true
pkill -f "chromium.*--remote-debugging-port" 2>/dev/null || true

# Kill existing MCP processes
pkill -f "npx @playwright/mcp" 2>/dev/null || true

# Clean up Playwright cache directories
rm -rf ~/.cache/ms-playwright/mcp-chrome-* 2>/dev/null || true
rm -rf ~/Library/Caches/ms-playwright/mcp-chrome-* 2>/dev/null || true

echo "⏳ Waiting for processes to fully terminate..."
sleep 2

echo "🚀 Starting fresh MCP server..."
cd "$(dirname "$0")/.."
npm run mcp:start