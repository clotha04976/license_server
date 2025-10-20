import apiClient from './apiClient';

const getCustomers = (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.search) queryParams.append('search', params.search);
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params.sort_order) queryParams.append('sort_order', params.sort_order);
  
  const queryString = queryParams.toString();
  const url = queryString ? `/customers/?${queryString}` : '/customers/';
  
  return apiClient.get(url);
};

const getCustomer = (id) => {
  return apiClient.get(`/customers/${id}`);
};

const createCustomer = (data) => {
  return apiClient.post('/customers/', data);
};

const updateCustomer = (id, data) => {
  return apiClient.put(`/customers/${id}`, data);
};

const deleteCustomer = (id) => {
  return apiClient.delete(`/customers/${id}`);
};

const customerService = {
  getCustomers,
  getCustomer,
  createCustomer,
  updateCustomer,
  deleteCustomer,
};

export default customerService;