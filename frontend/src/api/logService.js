import apiClient from './apiClient';

const getLogs = (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.serial_number) queryParams.append('serial_number', params.serial_number);
  if (params.customer_id) queryParams.append('customer_id', params.customer_id);
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  
  const queryString = queryParams.toString();
  const url = queryString ? `/logs/?${queryString}` : '/logs/';
  
  return apiClient.get(url);
};

const downloadLog = (serialNumber, filename) => {
  const queryParams = new URLSearchParams();
  queryParams.append('serial_number', serialNumber);
  queryParams.append('filename', filename);
  
  return apiClient.get(`/logs/download?${queryParams.toString()}`, {
    responseType: 'blob',
  });
};

const getLogsBySerial = (serialNumber) => {
  return apiClient.get(`/logs/serial/${serialNumber}`);
};

const getLogsByCustomer = (customerId) => {
  return apiClient.get(`/logs/customer/${customerId}`);
};

const deleteBatch = (batchId, serialNumber) => {
  const queryParams = new URLSearchParams();
  queryParams.append('serial_number', serialNumber);
  
  return apiClient.delete(`/logs/batch/${batchId}?${queryParams.toString()}`);
};

const deleteFile = (serialNumber, filename) => {
  const queryParams = new URLSearchParams();
  queryParams.append('serial_number', serialNumber);
  queryParams.append('filename', filename);
  
  return apiClient.delete(`/logs/file?${queryParams.toString()}`);
};

const logService = {
  getLogs,
  downloadLog,
  getLogsBySerial,
  getLogsByCustomer,
  deleteBatch,
  deleteFile,
};

export default logService;
