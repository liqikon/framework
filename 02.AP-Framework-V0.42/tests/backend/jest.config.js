/**
 * Jest Configuration for Backend Tests
 * AP-Framework V0.2
 *
 * Usage:
 *   cd tests/backend
 *   npm install  # (devDependencies: jest, supertest)
 *   npx jest --forceExit
 */
module.exports = {
  testEnvironment: 'node',
  testTimeout: 10000,
  roots: ['./'],
  testMatch: ['**/*.test.js'],
  setupFilesAfterSetup: ['./setup.js'],
  verbose: true,
  forceExit: true,
  detectOpenHandles: true,
};
