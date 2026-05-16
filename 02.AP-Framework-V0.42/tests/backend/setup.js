/**
 * Jest Setup File
 * AP-Framework V0.2
 *
 * 테스트 실행 전 환경 설정.
 * DB 모킹, 환경변수 설정 등을 여기에 추가합니다.
 */

// 테스트용 환경변수
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-jwt-secret';
process.env.SUPABASE_URL = 'https://test.supabase.co';
process.env.SUPABASE_KEY = 'test-supabase-key';

// 콘솔 노이즈 억제 (필요 시 주석 해제)
// jest.spyOn(console, 'log').mockImplementation(() => {});
// jest.spyOn(console, 'error').mockImplementation(() => {});
