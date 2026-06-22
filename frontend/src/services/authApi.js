import apiClient from './apiClient';

export async function register({ email, password, full_name }) {
  const response = await apiClient.post('/v1/auth/register', {
    email,
    password,
    full_name: full_name || null,
  });
  return response.data;
}

export async function login({ email, password }) {
  const response = await apiClient.post('/v1/auth/login', {
    email,
    password,
  });
  return response.data;
}

export async function loginWithGoogle(credential) {
  const response = await apiClient.post('/v1/auth/google', {
    credential,
  });
  return response.data;
}

export async function me() {
  const response = await apiClient.get('/v1/auth/me');
  return response.data;
}

export async function logout() {
  const response = await apiClient.post('/v1/auth/logout');
  return response.data;
}
