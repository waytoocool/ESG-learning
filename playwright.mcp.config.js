// Playwright MCP Configuration
// This ensures clean browser management for AI testing sessions

module.exports = {
  // Browser configuration
  browser: {
    // Use isolated browser contexts for each session
    isolated: true,
    
    // Clean up browser instances on startup
    cleanup: {
      onStart: true,
      killExisting: true,
      clearCache: true
    },
    
    // Browser launch options
    launchOptions: {
      headless: true,
      viewport: { width: 1280, height: 720 },
      // Force new browser instance
      args: [
        '--no-sandbox',
        '--disable-web-security',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--force-color-profile=srgb'
      ]
    }
  },
  
  // Server configuration
  server: {
    port: 3001,
    timeout: 30000
  },
  
  // Session management
  session: {
    // Automatically cleanup sessions after 30 minutes of inactivity
    timeout: 30 * 60 * 1000,
    
    // Maximum number of concurrent sessions
    maxSessions: 1,
    
    // Clean up on exit
    cleanupOnExit: true
  }
};