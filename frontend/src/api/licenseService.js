import apiClient from './apiClient';

const getLicenses = (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.search) queryParams.append('search', params.search);
  if (params.status) queryParams.append('status', params.status);
  if (params.order_by) queryParams.append('order_by', params.order_by);
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  
  const queryString = queryParams.toString();
  const url = queryString ? `/admin/licenses/?${queryString}` : '/admin/licenses/';
  
  return apiClient.get(url);
};

const getLicense = (id) => {
  return apiClient.get(`/admin/licenses/${id}`);
};

const createLicense = (data) => {
  return apiClient.post('/admin/licenses/', data);
};

const updateLicense = (id, data) => {
  return apiClient.put(`/admin/licenses/${id}`, data);
};

const deleteLicense = (id) => {
  return apiClient.delete(`/admin/licenses/${id}`);
};

const renewLicense = (id) => {
  return apiClient.post(`/admin/licenses/${id}/renew`);
};

const addManualActivation = (id, machineCode) => {
  return apiClient.post(`/admin/licenses/${id}/activations`, { machine_code: machineCode });
};

const getLicenseActivations = (id) => {
  return apiClient.get(`/admin/licenses/${id}/activations`);
};

const deleteActivation = (id) => {
  return apiClient.delete(`/admin/activations/${id}`);
};

const blacklistActivation = (id) => {
  return apiClient.post(`/admin/activations/${id}/blacklist`);
};

const downloadLicenseFile = (id, machineCode) => {
  return apiClient.get(`/admin/licenses/${id}/download/${machineCode}`, {
    responseType: 'blob', // Important for file downloads
  });
};

// 事件相關 API
const getLicenseEvents = (id, limit = 50) => {
  return apiClient.get(`/admin/licenses/${id}/events?limit=${limit}`);
};

const getUnconfirmedEvents = (id) => {
  return apiClient.get(`/admin/licenses/${id}/events/unconfirmed`);
};

const getUnconfirmedEventsCount = (id) => {
  return apiClient.get(`/admin/licenses/${id}/events/unconfirmed/count`);
};

const confirmEvent = (eventId, confirmedBy) => {
  return apiClient.post(`/admin/events/${eventId}/confirm`, {
    event_id: eventId,
    confirmed_by: confirmedBy
  });
};

const getSuspiciousEvents = (days = 7, limit = 100) => {
  return apiClient.get(`/admin/events/suspicious?days=${days}&limit=${limit}`);
};

const licenseService = {
  getLicenses,
  getLicense,
  createLicense,
  updateLicense,
  deleteLicense,
  renewLicense,
  addManualActivation,
  getLicenseActivations,
  deleteActivation,
  blacklistActivation,
  downloadLicenseFile,
  // 事件相關
  getLicenseEvents,
  getUnconfirmedEvents,
  getUnconfirmedEventsCount,
  confirmEvent,
  getSuspiciousEvents,
};

export default licenseService;