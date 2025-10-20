import apiClient from './apiClient';

const getFeatures = () => {
  return apiClient.get('/features/');
};

const createFeature = (data) => {
  return apiClient.post('/features/', data);
};

const updateFeature = (id, data) => {
  return apiClient.put(`/features/${id}`, data);
};

const deleteFeature = (id) => {
  return apiClient.delete(`/features/${id}`);
};

const featureService = {
  getFeatures,
  createFeature,
  updateFeature,
  deleteFeature,
};

export default featureService;