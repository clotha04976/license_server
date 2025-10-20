import React, { useState, useEffect } from 'react';
import productService from '../api/productService';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  IconButton,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ProductForm from '../components/forms/ProductForm';

function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await productService.getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('您確定要刪除此產品嗎？')) {
      try {
        await productService.deleteProduct(id);
        fetchProducts(); // Refresh the list
      } catch (error) {
        console.error('Failed to delete product:', error);
      }
    }
  };

  const handleOpenForm = (product = null) => {
    setSelectedProduct(product);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setSelectedProduct(null);
    setIsFormOpen(false);
  };

  const handleSave = async (formData) => {
    try {
      if (selectedProduct) {
        await productService.updateProduct(selectedProduct.id, formData);
      } else {
        await productService.createProduct(formData);
      }
      fetchProducts();
      handleCloseForm();
    } catch (error) {
      console.error('Failed to save product:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          產品
        </Typography>
        <Button variant="contained" onClick={() => handleOpenForm()}>新增產品</Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>名稱</TableCell>
              <TableCell>版本</TableCell>
              <TableCell>描述</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>{product.name}</TableCell>
                <TableCell>{product.version}</TableCell>
                <TableCell>{product.description}</TableCell>
                <TableCell>
                  <IconButton aria-label="edit" onClick={() => handleOpenForm(product)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton aria-label="delete" onClick={() => handleDelete(product.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <ProductForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleSave}
        product={selectedProduct}
      />
    </Box>
  );
}

export default ProductsPage;