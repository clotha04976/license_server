import apiClient from './apiClient';

const getEventLogs = (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.serial_number) queryParams.append('serial_number', params.serial_number);
  if (params.customer_name) queryParams.append('customer_name', params.customer_name);
  if (params.tax_id) queryParams.append('tax_id', params.tax_id);
  if (params.severity) queryParams.append('severity', params.severity);
  if (params.event_type) queryParams.append('event_type', params.event_type);
  if (params.is_confirmed !== undefined) queryParams.append('is_confirmed', params.is_confirmed);
  if (params.order_by) queryParams.append('order_by', params.order_by);
  
  const queryString = queryParams.toString();
  const url = queryString ? `/admin/event-logs?${queryString}` : '/admin/event-logs';
  
  return apiClient.get(url);
};

const getEventLog = (id) => {
  return apiClient.get(`/admin/event-logs/${id}`);
};

const confirmEvent = (eventId, confirmedBy) => {
  return apiClient.post(`/admin/event-logs/${eventId}/confirm`, {
    event_id: eventId,
    confirmed_by: confirmedBy
  });
};

const getSuspiciousEvents = (days = 7, limit = 100) => {
  return apiClient.get(`/admin/event-logs/suspicious?days=${days}&limit=${limit}`);
};

const getUnconfirmedEvents = (limit = 100) => {
  return apiClient.get(`/admin/event-logs/unconfirmed?limit=${limit}`);
};

const eventLogService = {
  getEventLogs,
  getEventLog,
  confirmEvent,
  getSuspiciousEvents,
  getUnconfirmedEvents,
};

export default eventLogService;
