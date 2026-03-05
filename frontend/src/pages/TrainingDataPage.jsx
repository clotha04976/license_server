import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Stack,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import trainingDataService from '../api/trainingDataService';

function TrainingDataPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 搜尋和篩選狀態
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('serial_number');
  const [customerIdFilter, setCustomerIdFilter] = useState('');

  // 分頁狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchRecords();
  }, [currentPage, pageSize]);

  const fetchRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        limit: pageSize,
      };

      if (searchTerm.trim()) {
        if (searchType === 'serial_number') {
          params.serial_number = searchTerm.trim();
        }
      }

      if (customerIdFilter) {
        params.customer_id = parseInt(customerIdFilter);
      }

      const response = await trainingDataService.getTrainingDataRecords(params);
      setRecords(response.data.items || []);
      setTotalPages(response.data.total_pages || 1);
      setTotalCount(response.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch training data records:', error);
      setError('獲取訓練資料記錄失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    fetchRecords();
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setCustomerIdFilter('');
    setCurrentPage(1);
    fetchRecords();
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <Box>
      {/* 標題和工具列 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          訓練資料管理
        </Typography>

        {/* 搜尋和控制區域 */}
        <Stack direction="row" spacing={1} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>搜尋類型</InputLabel>
            <Select
              value={searchType}
              label="搜尋類型"
              onChange={(e) => setSearchType(e.target.value)}
            >
              <MenuItem value="serial_number">序號</MenuItem>
            </Select>
          </FormControl>

          <TextField
            size="small"
            variant="outlined"
            placeholder="搜尋序號..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            sx={{ width: 300 }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />

          <TextField
            size="small"
            variant="outlined"
            placeholder="客戶 ID"
            value={customerIdFilter}
            onChange={(e) => setCustomerIdFilter(e.target.value)}
            type="number"
            sx={{ width: 120 }}
          />

          <Button variant="contained" color="secondary" onClick={handleSearch} disabled={loading}>
            搜尋
          </Button>

          {(searchTerm || customerIdFilter) && (
            <Button variant="outlined" onClick={handleClearSearch} disabled={loading}>
              清除
            </Button>
          )}

          <Tooltip title="重新整理">
            <IconButton onClick={fetchRecords} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 記錄列表表格 */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>客戶編號</TableCell>
              <TableCell>公司名稱</TableCell>
              <TableCell>序號</TableCell>
              <TableCell>年月</TableCell>
              <TableCell>發票數量</TableCell>
              <TableCell>首次上傳時間</TableCell>
              <TableCell>最後更新時間</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : records.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary">
                    {searchTerm || customerIdFilter ? '沒有找到符合條件的記錄' : '暫無訓練資料記錄'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              records.map((record, index) => (
                <TableRow key={index} hover>
                  <TableCell>{record.customer_tax_id || '-'}</TableCell>
                  <TableCell>{record.customer_name || '-'}</TableCell>
                  <TableCell>
                    <Chip label={record.serial_number} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>{record.year}.{String(record.month).padStart(2, '0')}</TableCell>
                  <TableCell>
                    <Chip label={`${record.invoice_count} 張`} size="small" />
                  </TableCell>
                  <TableCell>{formatDate(record.uploaded_at)}</TableCell>
                  <TableCell>{formatDate(record.last_updated)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 分頁控制 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        <Box>
          <Chip
            size="small"
            label={`共 ${totalCount} 筆資料`}
            color="primary"
            variant="outlined"
          />
        </Box>

        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={(event, page) => setCurrentPage(page)}
          color="primary"
          showFirstButton
          showLastButton
        />

        <FormControl size="small" sx={{ minWidth: 80 }}>
          <InputLabel>每頁</InputLabel>
          <Select
            value={pageSize}
            label="每頁"
            onChange={(e) => {
              setPageSize(e.target.value);
              setCurrentPage(1);
            }}
          >
            <MenuItem value={10}>10</MenuItem>
            <MenuItem value={20}>20</MenuItem>
            <MenuItem value={50}>50</MenuItem>
            <MenuItem value={100}>100</MenuItem>
          </Select>
        </FormControl>
      </Box>
    </Box>
  );
}

export default TrainingDataPage;
