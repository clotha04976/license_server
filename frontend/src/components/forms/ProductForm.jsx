import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';

function ProductForm({ open, onClose, onSave, product }) {
  const [formData, setFormData] = useState({
    name: '',
    version: '',
    description: '',
  });

  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name || '',
        version: product.version || '',
        description: product.description || '',
      });
    } else {
      // Reset form for new product
      setFormData({ name: '', version: '', description: '' });
    }
  }, [product, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{product ? '編輯產品' : '新增產品'}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          name="name"
          label="產品名稱"
          type="text"
          fullWidth
          variant="outlined"
          value={formData.name}
          onChange={handleChange}
          required
        />
        <TextField
          margin="dense"
          name="version"
          label="版本"
          type="text"
          fullWidth
          variant="outlined"
          value={formData.version}
          onChange={handleChange}
        />
        <TextField
          margin="dense"
          name="description"
          label="描述"
          type="text"
          fullWidth
          multiline
          rows={4}
          variant="outlined"
          value={formData.description}
          onChange={handleChange}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained">儲存</Button>
      </DialogActions>
    </Dialog>
  );
}

export default ProductForm;