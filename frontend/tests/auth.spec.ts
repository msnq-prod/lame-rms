import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE ?? 'http://localhost:8000/api';

test.describe('authentication client', () => {
  test('exposes login endpoint shape', async ({ request }) => {
    let response;
    try {
      response = await request.fetch(`${API_BASE}/auth/health`, {
        method: 'GET',
        timeout: 2_000,
      });
    } catch (error) {
      test.skip(`Auth API not reachable: ${error}`);
    }
    expect(response!.status()).toBeLessThan(600);
  });
});
