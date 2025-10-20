import apiClient from './apiClient';

const login = async (username, password) => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const response = await apiClient.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  if (response.data.access_token) {
    localStorage.setItem('accessToken', response.data.access_token);
  }
  return response.data;
};

const logout = () => {
  localStorage.removeItem('accessToken');
};

const authService = {
  login,
  logout,
};

export default authService;