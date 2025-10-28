export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  mfaCode?: string;
}

export interface RefreshPayload {
  refreshToken: string;
  mfaCode?: string;
}

export interface MfaSetupResponse {
  secret: string;
  provisioningUri: string;
}

const defaultHeaders = {
  'Content-Type': 'application/json',
};

export async function login(baseUrl: string, payload: LoginPayload): Promise<TokenPair> {
  const response = await fetch(`${baseUrl}/auth/login`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }
  const data = await response.json();
  return normalizeTokenPair(data);
}

export async function refreshToken(baseUrl: string, payload: RefreshPayload): Promise<TokenPair> {
  const response = await fetch(`${baseUrl}/auth/refresh`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Refresh failed: ${response.status}`);
  }
  const data = await response.json();
  return normalizeTokenPair(data);
}

export async function setupMfa(baseUrl: string): Promise<MfaSetupResponse> {
  const response = await fetch(`${baseUrl}/auth/mfa/setup`, {
    method: 'POST',
    headers: defaultHeaders,
  });
  if (!response.ok) {
    throw new Error(`Unable to setup MFA: ${response.status}`);
  }
  return response.json();
}

function normalizeTokenPair(data: any): TokenPair {
  return {
    accessToken: data.access_token ?? data.accessToken,
    refreshToken: data.refresh_token ?? data.refreshToken,
    expiresIn: Number(data.expires_in ?? data.expiresIn ?? 0),
    tokenType: data.token_type ?? data.tokenType ?? 'bearer',
  };
}
