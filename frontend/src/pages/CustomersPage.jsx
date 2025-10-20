import React, { useState, useEffect } from 'react';
import customerService from '../api/customerService';
import CustomerForm from '../components/forms/CustomerForm';
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
  TextField,
  InputAdornment,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';

function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  
  // 搜尋和分頁狀態
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState('asc');
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCustomers();
  }, [currentPage, pageSize, sortBy, sortOrder]);

  const fetchCustomers = async (search = searchTerm) => {
    setLoading(true);
    try {
      const params = {
        search: search || undefined,
        page: currentPage,
        limit: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      
      const response = await customerService.getCustomers(params);
      setCustomers(response.data.items);
      setTotalPages(response.data.total_pages);
      setTotalCount(response.data.total);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('您確定要刪除此客戶嗎？')) {
      try {
        await customerService.deleteCustomer(id);
        fetchCustomers(); // Refresh the list
      } catch (error) {
        console.error('Failed to delete customer:', error);
      }
    }
  };

  const handleOpenForm = (customer = null) => {
    setSelectedCustomer(customer);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setSelectedCustomer(null);
    setIsFormOpen(false);
  };

  const handleSave = async (formData) => {
    try {
      if (selectedCustomer) {
        await customerService.updateCustomer(selectedCustomer.id, formData);
      } else {
        await customerService.createCustomer(formData);
      }
      fetchCustomers();
      handleCloseForm();
    } catch (error) {
      console.error('Failed to save customer:', error);
    }
  };

  // 搜尋相關處理函數
  const handleSearch = () => {
    setCurrentPage(1);
    fetchCustomers(searchTerm);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setCurrentPage(1);
    fetchCustomers('');
  };

  const handlePageChange = (event, page) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (event) => {
    setPageSize(event.target.value);
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  return (
    <Box>
      {/* 標題和工具列 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          客戶管理
        </Typography>
        
        {/* 搜尋和控制區域 */}
        <Stack direction="row" spacing={1} alignItems="center">
          {/* 搜尋框 */}
          <TextField
            size="small"
            variant="outlined"
            placeholder="搜尋客戶..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            sx={{ width: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton onClick={handleClearSearch} size="small">
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          
          {/* 搜尋按鈕 */}
          <Button 
            variant="contained" 
            color="secondary"
            onClick={handleSearch} 
            disabled={loading}
          >
            搜尋
          </Button>
          
          
          {/* 新增客戶按鈕 */}
          <Button variant="contained" onClick={() => handleOpenForm()}>
            新增客戶
          </Button>
        </Stack>
      </Box>


      {/* 客戶表格 */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell 
                sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                onClick={() => handleSort('tax_id')}
              >
                客戶編號
                {sortBy === 'tax_id' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                onClick={() => handleSort('name')}
              >
                公司名稱
                {sortBy === 'name' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                onClick={() => handleSort('email')}
              >
                電子郵件
                {sortBy === 'email' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                onClick={() => handleSort('phone')}
              >
                電話
                {sortBy === 'phone' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography>載入中...</Typography>
                </TableCell>
              </TableRow>
            ) : customers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="text.secondary">
                    {searchTerm ? '沒有找到符合條件的客戶' : '暫無客戶資料'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              customers.map((customer) => (
                <TableRow key={customer.id} hover>
                  <TableCell>{customer.tax_id}</TableCell>
                  <TableCell>{customer.name}</TableCell>
                  <TableCell>{customer.email}</TableCell>
                  <TableCell>{customer.phone}</TableCell>
                  <TableCell>
                    <IconButton aria-label="edit" onClick={() => handleOpenForm(customer)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton aria-label="delete" onClick={() => handleDelete(customer.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 分頁控制 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        {/* 左側統計資訊 */}
        <Box>
          <Chip 
            size="small"
            label={`共 ${totalCount} 筆資料`} 
            color="primary" 
            variant="outlined"
          />
        </Box>
        
        {/* 中間分頁控制 */}
        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          color="primary"
          showFirstButton
          showLastButton
        />
        
        {/* 右側每頁筆數選擇 */}
        <FormControl size="small" sx={{ minWidth: 80 }}>
          <InputLabel>每頁</InputLabel>
          <Select
            value={pageSize}
            label="每頁"
            onChange={handlePageSizeChange}
          >
            <MenuItem value={10}>10</MenuItem>
            <MenuItem value={20}>20</MenuItem>
            <MenuItem value={50}>50</MenuItem>
            <MenuItem value={100}>100</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <CustomerForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleSave}
        customer={selectedCustomer}
      />
    </Box>
  );
}

export default CustomersPage;