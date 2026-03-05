import apiClient from './apiClient';

const getTrainingDataRecords = (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.serial_number) queryParams.append('serial_number', params.serial_number);
  if (params.customer_id) queryParams.append('customer_id', params.customer_id);
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  
  const queryString = queryParams.toString();
  const url = queryString ? `/training-data/?${queryString}` : '/training-data/';
  
  return apiClient.get(url);
};

const trainingDataService = {
  getTrainingDataRecords,
};

export default trainingDataService;
