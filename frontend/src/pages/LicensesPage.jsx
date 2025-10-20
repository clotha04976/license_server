import React, { useState, useEffect } from 'react';
import licenseService from '../api/licenseService';
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
  Chip,
  Tooltip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  Alert,
  Pagination,
  Stack,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PlusOneIcon from '@mui/icons-material/PlusOne';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ComputerIcon from '@mui/icons-material/Computer';
import LicenseForm from '../components/forms/LicenseForm';
import EventDialog from '../components/EventDialog';
import ActivationsDialog from '../components/ActivationsDialog';

function LicensesPage() {
  const [licenses, setLicenses] = useState([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [orderBy, setOrderBy] = useState('created_at_desc');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // 分頁相關狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // 事件監控相關狀態
  const [eventCounts, setEventCounts] = useState({});
  const [isEventDialogOpen, setIsEventDialogOpen] = useState(false);
  const [selectedLicenseForEvents, setSelectedLicenseForEvents] = useState(null);

  // 啟用記錄相關狀態
  const [isActivationsDialogOpen, setIsActivationsDialogOpen] = useState(false);
  const [selectedLicenseForActivations, setSelectedLicenseForActivations] = useState(null);

  useEffect(() => {
    const timerId = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500); // 500ms delay

    return () => {
      clearTimeout(timerId);
    };
  }, [searchTerm]);

  useEffect(() => {
    fetchLicenses();
  }, [debouncedSearchTerm, statusFilter, orderBy, currentPage, pageSize]);

  // 獲取事件數量
  useEffect(() => {
    if (licenses.length > 0) {
      fetchEventCounts();
    }
  }, [licenses]);

  const fetchLicenses = async () => {
    setLoading(true);
    try {
      const params = {
        search: debouncedSearchTerm || undefined,
        status: statusFilter || undefined,
        order_by: orderBy,
        page: currentPage,
        limit: pageSize,
      };
      
      const response = await licenseService.getLicenses(params);
      setLicenses(response.data.items);
      setTotalPages(response.data.total_pages);
      setTotalCount(response.data.total);
    } catch (error) {
      console.error('Failed to fetch licenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEventCounts = async () => {
    try {
      const counts = {};
      for (const license of licenses) {
        try {
          const response = await licenseService.getUnconfirmedEventsCount(license.id);
          counts[license.id] = response.data.count;
        } catch (error) {
          console.error(`Failed to fetch event count for license ${license.id}:`, error);
          counts[license.id] = 0;
        }
      }
      setEventCounts(counts);
    } catch (error) {
      console.error('Failed to fetch event counts:', error);
    }
  };

  const handleOpenEventDialog = (license) => {
    setSelectedLicenseForEvents(license);
    setIsEventDialogOpen(true);
  };

  const handleCloseEventDialog = (hasUpdates = false) => {
    setIsEventDialogOpen(false);
    setSelectedLicenseForEvents(null);
    if (hasUpdates) {
      // 如果有更新，重新獲取事件數量
      fetchEventCounts();
      showSnackbar('事件已確認', 'success');
    }
  };

  const handleOpenActivationsDialog = (license) => {
    setSelectedLicenseForActivations(license);
    setIsActivationsDialogOpen(true);
  };

  const handleCloseActivationsDialog = () => {
    setIsActivationsDialogOpen(false);
    setSelectedLicenseForActivations(null);
  };

  const handleDelete = async (id) => {
    if (window.confirm('您確定要刪除此授權嗎？此操作無法復原。')) {
      try {
        await licenseService.deleteLicense(id);
        // 立即從本地狀態中移除該筆記錄
        setLicenses(prevLicenses => prevLicenses.filter(license => license.id !== id));
        showSnackbar('授權已成功刪除', 'success');
        // 同時重新獲取資料以確保同步
        fetchLicenses();
      } catch (error) {
        console.error('Failed to delete license:', error);
        // 嘗試從錯誤回應中取得詳細訊息
        let errorMessage = '刪除授權失敗';
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        showSnackbar(errorMessage, 'error');
      }
    }
  };

  const handleRenew = async (id) => {
    if (window.confirm('您確定要將此授權續約一年嗎？')) {
      try {
        const renewedLicense = await licenseService.renewLicense(id);
        // 立即更新本地狀態
        setLicenses(prevLicenses =>
          prevLicenses.map(license =>
            license.id === id ? renewedLicense.data : license
          )
        );
        showSnackbar('授權已成功續約一年', 'success');
        // 同時重新獲取資料以確保同步
        fetchLicenses();
      } catch (error) {
        console.error('Failed to renew license:', error);
        // 嘗試從錯誤回應中取得詳細訊息
        let errorMessage = '續約失敗';
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        showSnackbar(errorMessage, 'error');
      }
    }
  };

  const handleOpenForm = (license = null) => {
    setSelectedLicense(license);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setSelectedLicense(null);
    setIsFormOpen(false);
  };

  const handleSave = async (formData, licenseId) => {
    try {
      if (licenseId) {
        // 更新授權
        const updatedLicense = await licenseService.updateLicense(licenseId, formData);
        // 立即更新本地狀態
        setLicenses(prevLicenses =>
          prevLicenses.map(license =>
            license.id === licenseId ? updatedLicense.data : license
          )
        );
        showSnackbar('授權已成功更新', 'success');
      } else {
        // 新增授權
        const newLicense = await licenseService.createLicense(formData);
        // 立即將新授權加入本地狀態
        setLicenses(prevLicenses => [newLicense.data, ...prevLicenses]);
        showSnackbar('授權已成功新增', 'success');
      }
      handleCloseForm();
      // 同時重新獲取資料以確保同步
      fetchLicenses();
    } catch (error) {
      console.error('Failed to save license:', error);
      // 嘗試從錯誤回應中取得詳細訊息
      let errorMessage = '儲存授權失敗';
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      showSnackbar(errorMessage, 'error');
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 分頁處理函數
  const handlePageChange = (event, page) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (event) => {
    setPageSize(event.target.value);
    setCurrentPage(1);
  };

  const copyToClipboard = (text, successMessage = '已複製到剪貼簿') => {
    // 在不安全的環境或 navigator.clipboard 不可用時使用備用方法
    fallbackCopyToClipboard(text, successMessage);
  };

  const fallbackCopyToClipboard = (text, successMessage) => {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = 0;
    textArea.style.left = 0;
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = 0;
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        showSnackbar(successMessage, 'success');
      } else {
        showSnackbar('無法複製', 'error');
      }
    } catch (err) {
      console.error('備用複製方法失敗:', err);
      showSnackbar('複製失敗', 'error');
    }
    document.body.removeChild(textArea);
  };

  const getStatusChip = (status) => {
    const statusMap = {
      active: '啟用',
      pending: '待定',
      expired: '已過期',
      disabled: '已停用',
    };
    const colorMap = {
      active: 'success',
      pending: 'warning',
      expired: 'error',
      disabled: 'default',
    };
    return <Chip label={statusMap[status] || status} color={colorMap[status] || 'default'} size="small" />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          授權
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <IconButton onClick={fetchLicenses} aria-label="refresh">
            <RefreshIcon />
          </IconButton>
          <TextField
            label="依客戶或統一編號搜尋"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>狀態</InputLabel>
            <Select
              value={statusFilter}
              label="狀態"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">全部</MenuItem>
              <MenuItem value={'pending'}>待定</MenuItem>
              <MenuItem value={'active'}>啟用</MenuItem>
              <MenuItem value={'expired'}>已過期</MenuItem>
              <MenuItem value={'disabled'}>已停用</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>排序方式</InputLabel>
            <Select
              value={orderBy}
              label="排序方式"
              onChange={(e) => setOrderBy(e.target.value)}
            >
              <MenuItem value="created_at_desc">最新建立</MenuItem>
              <MenuItem value="created_at_asc">最舊建立</MenuItem>
              <MenuItem value="updated_at_desc">最近更新</MenuItem>
              <MenuItem value="updated_at_asc">最舊更新</MenuItem>
              <MenuItem value="expires_at_desc">最晚到期</MenuItem>
              <MenuItem value="expires_at_asc">最早到期</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" onClick={() => handleOpenForm()}>新增授權</Button>
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>序號</TableCell>
              <TableCell>客戶</TableCell>
              <TableCell>客戶編號</TableCell>
              <TableCell>產品</TableCell>
              <TableCell>連線方式</TableCell>
              <TableCell>狀態</TableCell>
              <TableCell>到期日</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {licenses.map((license) => (
              <TableRow key={license.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Tooltip title={license.serial_number}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', mr: 1 }}>
                        {license.serial_number}
                      </Typography>
                    </Tooltip>
                    <IconButton size="small" onClick={() => copyToClipboard(license.serial_number, '序號已複製到剪貼簿')}>
                      <ContentCopyIcon fontSize="inherit" />
                    </IconButton>
                  </Box>
                </TableCell>
                <TableCell>{license.customer.name}</TableCell>
                <TableCell>{license.customer.tax_id}</TableCell>
                <TableCell>{license.product.name}</TableCell>
                <TableCell>
                  <Chip
                    label={license.connection_type === 'network' ? '網路版' : '單機版'}
                    color={license.connection_type === 'network' ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{getStatusChip(license.status)}</TableCell>
                <TableCell>
                  {license.expires_at ? new Date(license.expires_at).toLocaleDateString() : '永不'}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Tooltip title="編輯">
                      <IconButton aria-label="edit" onClick={() => handleOpenForm(license)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="續約一年">
                      <IconButton aria-label="renew" onClick={() => handleRenew(license.id)}>
                        <PlusOneIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="刪除">
                      <IconButton aria-label="delete" onClick={() => handleDelete(license.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                    {/* 啟用記錄按鈕 */}
                    <Tooltip title="查看啟用記錄">
                      <IconButton
                        aria-label="activations"
                        onClick={() => handleOpenActivationsDialog(license)}
                        sx={{ color: 'primary.main' }}
                      >
                        <ComputerIcon />
                      </IconButton>
                    </Tooltip>
                    {/* 事件監控按鈕 */}
                    {eventCounts[license.id] > 0 ? (
                      <Tooltip title={`有 ${eventCounts[license.id]} 個未確認事件`}>
                        <IconButton
                          aria-label="events"
                          onClick={() => handleOpenEventDialog(license)}
                          sx={{ color: 'warning.main' }}
                        >
                          <WarningIcon />
                        </IconButton>
                      </Tooltip>
                    ) : (
                      <Tooltip title="無未確認事件">
                        <IconButton
                          aria-label="events"
                          onClick={() => handleOpenEventDialog(license)}
                          sx={{ color: 'success.main' }}
                        >
                          <CheckCircleIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 分頁控制 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        {/* 左側統計資訊 */}
        <Box>
          <Chip 
            size="small"
            label={`共 ${totalCount} 筆授權`} 
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

      <LicenseForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleSave}
        license={selectedLicense}
      />

      {/* 事件監控對話框 */}
      <EventDialog
        open={isEventDialogOpen}
        onClose={handleCloseEventDialog}
        licenseId={selectedLicenseForEvents?.id}
        licenseSerialNumber={selectedLicenseForEvents?.serial_number}
      />

      {/* 啟用記錄對話框 */}
      <ActivationsDialog
        open={isActivationsDialogOpen}
        onClose={handleCloseActivationsDialog}
        licenseId={selectedLicenseForActivations?.id}
        licenseSerialNumber={selectedLicenseForActivations?.serial_number}
      />

      {/* 複製成功通知 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default LicensesPage;