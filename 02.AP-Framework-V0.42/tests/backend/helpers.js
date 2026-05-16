/**
 * Test Helpers for Backend Tests
 * AP-Framework V0.2
 *
 * Mock request/response 유틸리티.
 * P-502 (단위 테스트 생성기)가 이 파일을 참조하여 테스트를 생성합니다.
 */

/**
 * Express request 객체 모킹
 */
function mockRequest(overrides = {}) {
  return {
    body: {},
    params: {},
    query: {},
    headers: {},
    user: null,
    ...overrides,
  };
}

/**
 * Express response 객체 모킹
 */
function mockResponse() {
  const res = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  res.send = jest.fn().mockReturnValue(res);
  res.set = jest.fn().mockReturnValue(res);
  res.cookie = jest.fn().mockReturnValue(res);
  res.clearCookie = jest.fn().mockReturnValue(res);
  res.redirect = jest.fn().mockReturnValue(res);
  return res;
}

/**
 * Express next 함수 모킹
 */
function mockNext() {
  return jest.fn();
}

/**
 * JWT 토큰 생성 헬퍼 (테스트용)
 */
function generateTestToken(payload = {}, secret = 'test-jwt-secret') {
  const jwt = require('jsonwebtoken');
  return jwt.sign(
    { id: 1, email: 'test@example.com', role: 'user', ...payload },
    secret,
    { expiresIn: '1h' }
  );
}

/**
 * 관리자 토큰 생성 헬퍼
 */
function generateAdminToken(secret = 'test-jwt-secret') {
  return generateTestToken({ role: 'admin' }, secret);
}

module.exports = {
  mockRequest,
  mockResponse,
  mockNext,
  generateTestToken,
  generateAdminToken,
};
