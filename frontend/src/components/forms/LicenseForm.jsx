import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  List,
  ListItem,
  IconButton,
  Divider,
  Typography,
  Box,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import AddIcon from '@mui/icons-material/Add';
import customerService from '../../api/customerService';
import productService from '../../api/productService';
import featureService from '../../api/featureService';
import licenseService from '../../api/licenseService';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

function LicenseForm({ open, onClose, onSave, license }) {
  const [availableFeatures, setAvailableFeatures] = useState([]);
  const [formData, setFormData] = useState({
    customer_id: '',
    product_id: '',
    expires_at: '',
    max_activations: 1,
    features: [],
    status: 'pending',
    connection_type: 'network',
    notes: '',
  });
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [initialMachineCode, setInitialMachineCode] = useState('');

  useEffect(() => {
    if (open) {
      customerService.getCustomers().then(res => setCustomers(res.data.items || res.data));
      productService.getProducts().then(res => setProducts(res.data.items || res.data));
      featureService.getFeatures().then(res => setAvailableFeatures(res.data.items || res.data));
    }
  }, [open]);

  useEffect(() => {
    if (license) {
      setFormData({
        customer_id: license.customer.id || '',
        product_id: license.product.id || '',
        expires_at: license.expires_at ? license.expires_at.split('T')[0] : '',
        max_activations: license.max_activations || 1,
        features: license.features || [],
        status: license.status || 'pending',
        connection_type: license.connection_type || 'network',
        notes: license.notes || '',
      });
    } else {
      setFormData({
        customer_id: '',
        product_id: '',
        expires_at: '',
        max_activations: 1,
        features: [],
        status: 'pending',
        connection_type: 'network',
        notes: '',
      });
    }
  }, [license, open]);

  useEffect(() => {
    // Reset machine code when status changes or form is re-opened
    if (formData.status !== 'active' || !open) {
      setInitialMachineCode('');
    }
  }, [formData.status, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFeatureChange = (event) => {
    const {
      target: { value },
    } = event;
    setFormData((prev) => ({
      ...prev,
      features: typeof value === 'string' ? value.split(',') : value,
    }));
  };

  const [newMachineCode, setNewMachineCode] = useState('');

  const handleSubmit = () => {
    // Validation for new active license
    if (!license && formData.status === 'active' && !initialMachineCode.trim()) {
      alert("建立狀態為 '啟用' 的新授權時，必須提供機器碼。");
      return;
    }

    const dataToSave = { ...formData };
    if (dataToSave.expires_at === '') {
      dataToSave.expires_at = null;
    } else {
      dataToSave.expires_at = new Date(dataToSave.expires_at).toISOString();
    }

    // Add machine code to the payload if applicable
    if (!license && formData.status === 'active') {
      dataToSave.machine_code = initialMachineCode.trim();
    }

    onSave(dataToSave, license ? license.id : null);
  };

  const handleRenew = async () => {
    if (!license) return;
    try {
      await licenseService.renewLicense(license.id);
      onClose(); // Close and let the parent list refresh
    } catch (error) {
      console.error("Failed to renew license:", error);
    }
  };

  const handleAddActivation = async () => {
    if (!license || !newMachineCode) return;
    try {
      await licenseService.addManualActivation(license.id, newMachineCode);
      setNewMachineCode('');
      onClose(); // Close and let the parent list refresh
    } catch (error) {
      console.error("Failed to add activation:", error);
    }
  };

  const handleDownload = async (machineCode) => {
    if (!license) return;
    try {
      const response = await licenseService.downloadLicenseFile(license.id, machineCode);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `license_${license.customer.name}_${machineCode.substring(0, 8)}.lic`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Failed to download license file:", error);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{license ? '編輯授權' : '新增授權'}</DialogTitle>
      <DialogContent>
        <FormControl fullWidth margin="dense" required>
          <InputLabel id="customer-select-label">客戶</InputLabel>
          <Select
            labelId="customer-select-label"
            name="customer_id"
            value={formData.customer_id}
            label="客戶"
            onChange={handleChange}
            disabled={!!license}
          >
            {customers.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense" required>
          <InputLabel id="product-select-label">產品</InputLabel>
          <Select
            labelId="product-select-label"
            name="product_id"
            value={formData.product_id}
            label="產品"
            onChange={handleChange}
            disabled={!!license}
          >
            {products.map(p => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField
          margin="dense"
          name="expires_at"
          label="到期日"
          type="date"
          fullWidth
          InputLabelProps={{ shrink: true }}
          value={formData.expires_at}
          onChange={handleChange}
        />
        <TextField
          margin="dense"
          name="max_activations"
          label="最大啟用次數"
          type="number"
          fullWidth
          value={formData.max_activations}
          onChange={handleChange}
        />
        <FormControl fullWidth margin="dense">
          <InputLabel id="features-select-label">功能</InputLabel>
          <Select
            labelId="features-select-label"
            name="features"
            multiple
            value={formData.features}
            onChange={handleFeatureChange}
            input={<OutlinedInput label="功能" />}
            renderValue={(selected) => selected.join(', ')}
            MenuProps={MenuProps}
          >
            {availableFeatures.map((feature) => (
              <MenuItem key={feature.id} value={feature.name}>
                <Checkbox checked={formData.features.indexOf(feature.name) > -1} />
                <ListItemText primary={feature.name} secondary={feature.description} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel id="status-select-label">狀態</InputLabel>
          <Select
            labelId="status-select-label"
            name="status"
            value={formData.status}
            label="狀態"
            onChange={handleChange}
          >
            <MenuItem value="pending">待定</MenuItem>
            <MenuItem value="active">啟用</MenuItem>
            <MenuItem value="expired">已過期</MenuItem>
            <MenuItem value="disabled">已停用</MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel id="connection-type-select-label">連線方式</InputLabel>
          <Select
            labelId="connection-type-select-label"
            name="connection_type"
            value={formData.connection_type}
            label="連線方式"
            onChange={handleChange}
          >
            <MenuItem value="network">網路版</MenuItem>
            <MenuItem value="standalone">單機版</MenuItem>
          </Select>
        </FormControl>
        <TextField
          margin="dense"
          name="notes"
          label="備註"
          type="text"
          fullWidth
          multiline
          rows={3}
          value={formData.notes}
          onChange={handleChange}
        />

        {/* Conditional Machine Code input for new active licenses */}
        {!license && formData.status === 'active' && (
          <TextField
            margin="dense"
            name="initialMachineCode"
            label="機器碼"
            type="text"
            fullWidth
            required
            value={initialMachineCode}
            onChange={(e) => setInitialMachineCode(e.target.value)}
            helperText="新授權若狀態為 '啟用'，此為必填欄位。"
          />
        )}

        {license && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>啟用紀錄</Typography>
            <List dense>
              {license.activations.map(act => (
                <ListItem
                  key={act.id}
                  secondaryAction={
                    <IconButton edge="end" aria-label="download" onClick={() => handleDownload(act.machine_code)}>
                      <DownloadIcon />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={act.machine_code}
                    secondary={`啟用於: ${new Date(act.activated_at).toLocaleString()}`}
                  />
                </ListItem>
              ))}
            </List>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <TextField
                label="新增機器碼"
                size="small"
                value={newMachineCode}
                onChange={(e) => setNewMachineCode(e.target.value)}
                sx={{ flexGrow: 1, mr: 1 }}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={handleAddActivation}
                disabled={!newMachineCode}
              >
                <AddIcon /> 新增
              </Button>
            </Box>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained">儲存</Button>
      </DialogActions>
    </Dialog>
  );
}

export default LicenseForm;