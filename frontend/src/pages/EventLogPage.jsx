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
  Chip,
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
  Snackbar,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import eventLogService from '../api/eventLogService';

function EventLogPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // 搜尋和篩選狀態
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('serial_number'); // serial_number, customer_name, tax_id
  const [severityFilter, setSeverityFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [confirmedFilter, setConfirmedFilter] = useState('');

  // 分頁狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchEvents();
  }, [currentPage, pageSize]);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        limit: pageSize,
      };

      // 根據搜尋類型添加搜尋參數
      if (searchTerm.trim()) {
        if (searchType === 'serial_number') {
          params.serial_number = searchTerm.trim();
        } else if (searchType === 'customer_name') {
          params.customer_name = searchTerm.trim();
        } else if (searchType === 'tax_id') {
          params.tax_id = searchTerm.trim();
        }
      }

      // 添加篩選參數
      if (severityFilter) params.severity = severityFilter;
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      if (confirmedFilter !== '') params.is_confirmed = confirmedFilter === 'true';

      const response = await eventLogService.getEventLogs(params);
      setEvents(response.data.items || response.data);
      setTotalPages(response.data.total_pages || 1);
      setTotalCount(response.data.total || response.data.length);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setError('獲取事件記錄失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    fetchEvents();
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setSearchType('serial_number');
    setSeverityFilter('');
    setEventTypeFilter('');
    setConfirmedFilter('');
    setCurrentPage(1);
    fetchEvents();
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const formatDateTime = (dateTime) => {
    if (!dateTime) return '無';
    
    const date = new Date(dateTime);
    return date.toLocaleString('zh-TW', {
      timeZone: 'Asia/Taipei',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getSeverityChip = (severity) => {
    const severityMap = {
      info: '資訊',
      warning: '警告',
      suspicious: '可疑',
      critical: '嚴重',
    };
    const colorMap = {
      info: 'info',
      warning: 'warning',
      suspicious: 'error',
      critical: 'error',
    };
    const iconMap = {
      info: <InfoIcon />,
      warning: <WarningIcon />,
      suspicious: <WarningIcon />,
      critical: <ErrorIcon />,
    };
    return (
      <Chip
        label={severityMap[severity] || severity}
        color={colorMap[severity] || 'default'}
        size="small"
        icon={iconMap[severity] || <InfoIcon />}
      />
    );
  };

  const getEventTypeChip = (eventType) => {
    const typeMap = {
      activation: '啟用',
      re_activation: '重新啟用',
      hardware_change: '硬體變化',
      validation: '驗證',
      deactivation: '停用',
    };
    return (
      <Chip
        label={typeMap[eventType] || eventType}
        color="primary"
        variant="outlined"
        size="small"
      />
    );
  };

  const getConfirmedChip = (isConfirmed) => {
    return (
      <Chip
        label={isConfirmed ? '已確認' : '未確認'}
        color={isConfirmed ? 'success' : 'warning'}
        size="small"
        icon={isConfirmed ? <CheckCircleIcon /> : <WarningIcon />}
      />
    );
  };

  const truncateMachineCode = (machineCode) => {
    if (!machineCode) return '無';
    return machineCode.length > 16 ? `${machineCode.substring(0, 16)}...` : machineCode;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          事件記錄
        </Typography>
        <IconButton onClick={fetchEvents} aria-label="refresh">
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* 搜尋和篩選區域 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>搜尋類型</InputLabel>
            <Select
              value={searchType}
              label="搜尋類型"
              onChange={(e) => setSearchType(e.target.value)}
            >
              <MenuItem value="serial_number">序號</MenuItem>
              <MenuItem value="customer_name">客戶名稱</MenuItem>
              <MenuItem value="tax_id">客戶編號</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            label="搜尋關鍵字"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ minWidth: 200 }}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
          >
            搜尋
          </Button>
          
          <Button
            variant="outlined"
            onClick={handleClearSearch}
          >
            清除
          </Button>
        </Stack>

        <Stack direction="row" spacing={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>嚴重程度</InputLabel>
            <Select
              value={severityFilter}
              label="嚴重程度"
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <MenuItem value="">全部</MenuItem>
              <MenuItem value="info">資訊</MenuItem>
              <MenuItem value="warning">警告</MenuItem>
              <MenuItem value="suspicious">可疑</MenuItem>
              <MenuItem value="critical">嚴重</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>事件類型</InputLabel>
            <Select
              value={eventTypeFilter}
              label="事件類型"
              onChange={(e) => setEventTypeFilter(e.target.value)}
            >
              <MenuItem value="">全部</MenuItem>
              <MenuItem value="activation">啟用</MenuItem>
              <MenuItem value="re_activation">重新啟用</MenuItem>
              <MenuItem value="hardware_change">硬體變化</MenuItem>
              <MenuItem value="validation">驗證</MenuItem>
              <MenuItem value="deactivation">停用</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>確認狀態</InputLabel>
            <Select
              value={confirmedFilter}
              label="確認狀態"
              onChange={(e) => setConfirmedFilter(e.target.value)}
            >
              <MenuItem value="">全部</MenuItem>
              <MenuItem value="true">已確認</MenuItem>
              <MenuItem value="false">未確認</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {/* 事件記錄表格 */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>時間</TableCell>
                <TableCell>序號</TableCell>
                <TableCell>客戶名稱</TableCell>
                <TableCell>事件類型</TableCell>
                <TableCell>嚴重程度</TableCell>
                <TableCell>機器碼</TableCell>
                <TableCell>IP 位址</TableCell>
                <TableCell>確認狀態</TableCell>
                <TableCell>詳細資訊</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {events.map((event) => (
                <TableRow key={event.id}>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDateTime(event.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {event.serial_number}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {event.customer_name || '無'}
                    </Typography>
                  </TableCell>
                  <TableCell>{getEventTypeChip(event.event_type)}</TableCell>
                  <TableCell>{getSeverityChip(event.severity)}</TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {truncateMachineCode(event.machine_code)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {event.ip_address || '無'}
                    </Typography>
                  </TableCell>
                  <TableCell>{getConfirmedChip(event.is_confirmed)}</TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {event.event_subtype || '無'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* 分頁控制 */}
      {!loading && !error && events.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <Box>
            <Chip 
              size="small"
              label={`共 ${totalCount} 筆事件`} 
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
      )}

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

export default EventLogPage;
