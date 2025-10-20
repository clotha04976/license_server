import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';

function CustomerForm({ open, onClose, onSave, customer }) {
  const [formData, setFormData] = useState({
    tax_id: '',
    name: '',
    email: '',
    phone: '',
    address: '',
    notes: '',
  });

  useEffect(() => {
    if (customer) {
      setFormData({
        tax_id: customer.tax_id || '',
        name: customer.name || '',
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
        notes: customer.notes || '',
      });
    } else {
      // Reset form for new customer
      setFormData({ tax_id: '', name: '', email: '', phone: '', address: '', notes: '' });
    }
  }, [customer, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{customer ? '編輯客戶' : '新增客戶'}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          name="tax_id"
          label="客戶編號"
          type="text"
          fullWidth
          variant="outlined"
          value={formData.tax_id}
          onChange={handleChange}
          required
        />
        <TextField
          margin="dense"
          name="name"
          label="公司名稱"
          type="text"
          fullWidth
          variant="outlined"
          value={formData.name}
          onChange={handleChange}
          required
        />
        <TextField
          margin="dense"
          name="email"
          label="電子郵件"
          type="email"
          fullWidth
          variant="outlined"
          value={formData.email}
          onChange={handleChange}
        />
        <TextField
          margin="dense"
          name="phone"
          label="電話號碼"
          type="text"
          fullWidth
          variant="outlined"
          value={formData.phone}
          onChange={handleChange}
        />
        <TextField
          margin="dense"
          name="address"
          label="地址"
          type="text"
          fullWidth
          multiline
          rows={2}
          variant="outlined"
          value={formData.address}
          onChange={handleChange}
        />
        <TextField
          margin="dense"
          name="notes"
          label="備註"
          type="text"
          fullWidth
          multiline
          rows={3}
          variant="outlined"
          value={formData.notes}
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

export default CustomerForm;