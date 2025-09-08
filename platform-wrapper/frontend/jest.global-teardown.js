/**
 * Global Jest teardown for multi-tenant testing environment
 * Runs once after all test suites complete
 */

module.exports = async () => {
  // Restore original console methods
  if (global.__ORIGINAL_CONSOLE__) {
    console.log = global.__ORIGINAL_CONSOLE__.log
    console.warn = global.__ORIGINAL_CONSOLE__.warn
    console.error = global.__ORIGINAL_CONSOLE__.error
    console.debug = global.__ORIGINAL_CONSOLE__.debug
  }
  
  // Clean up global test configuration
  delete global.__TEST_CONFIG__
  delete global.__ORIGINAL_CONSOLE__
  
  // Clean up any global resources
  if (global.gc) {
    global.gc()
  }
  
  console.log('🧹 Jest Global Teardown: Test environment cleaned up')
}