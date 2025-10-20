import apiClient from './apiClient';

const getProducts = () => {
  return apiClient.get('/products/');
};

const getProduct = (id) => {
  return apiClient.get(`/products/${id}`);
};

const createProduct = (data) => {
  return apiClient.post('/products/', data);
};

const updateProduct = (id, data) => {
  return apiClient.put(`/products/${id}`, data);
};

const deleteProduct = (id) => {
  return apiClient.delete(`/products/${id}`);
};

const productService = {
  getProducts,
  getProduct,
  createProduct,
  updateProduct,
  deleteProduct,
};

export default productService;