import React, { useState, useEffect, useMemo } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import FolderIcon from '@mui/icons-material/Folder';
import DeleteIcon from '@mui/icons-material/Delete';
import logService from '../api/logService';

function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);

  // 搜尋和篩選狀態
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('serial_number');
  const [customerIdFilter, setCustomerIdFilter] = useState('');

  // 分頁狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    fetchLogs();
  }, []); // 只在載入時取得一次，分頁由前端處理

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      // 先取得所有檔案（不分頁），讓前端自己分組和分頁
      // 這樣可以確保同一批次的檔案不會被分到不同頁
      const params = {
        page: 1,
        limit: 10000, // 取得所有檔案（後端已允許此值）
      };

      if (searchTerm.trim()) {
        if (searchType === 'serial_number') {
          params.serial_number = searchTerm.trim();
        }
      }

      if (customerIdFilter) {
        params.customer_id = parseInt(customerIdFilter);
      }

      const response = await logService.getLogs(params);
      setLogs(response.data.items || []);
      // 注意：total 和 total_pages 現在是批次數量，不是檔案數量
      // 我們會在前端重新計算分頁
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setError('獲取 log 檔案列表失敗');
    } finally {
      setLoading(false);
    }
  };

  // 按批次分組，然後分頁
  const { groupedLogs, totalPages: computedTotalPages, totalCount: computedTotalCount } = useMemo(() => {
    const groups = {};
    
    logs.forEach((log) => {
      // 使用 batch_id 作為分組鍵，如果沒有 batch_id 則使用 uploaded_at 的日期時間作為批次
      const batchKey = log.batch_id || 
        new Date(log.uploaded_at).toISOString().slice(0, 16).replace('T', '_').replace(/[:-]/g, '');
      
      if (!groups[batchKey]) {
        groups[batchKey] = {
          batch_id: log.batch_id || batchKey,
          serial_number: log.serial_number,
          customer_id: log.customer_id,
          customer_tax_id: log.customer_tax_id,
          customer_name: log.customer_name,
          uploaded_at: log.uploaded_at,
          problem_description: log.problem_description,
          files: [],
        };
      }
      groups[batchKey].files.push(log);
    });
    
    // 轉換為陣列並排序（最新的在前）
    const allBatches = Object.values(groups).sort((a, b) => 
      new Date(b.uploaded_at) - new Date(a.uploaded_at)
    );
    
    // 分頁（按批次分頁）
    const total = allBatches.length;
    const totalPages = Math.ceil(total / pageSize);
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const paginatedBatches = allBatches.slice(start, end);
    
    return {
      groupedLogs: paginatedBatches,
      totalPages,
      totalCount: total,
    };
  }, [logs, currentPage, pageSize]);

  const handleSearch = () => {
    setCurrentPage(1);
    fetchLogs();
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setCustomerIdFilter('');
    setCurrentPage(1);
    fetchLogs();
  };

  const handleDownload = async (serialNumber, filename) => {
    try {
      const response = await logService.downloadLog(serialNumber, filename);
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download log:', error);
      alert('下載 log 檔案失敗');
    }
  };

  const handleOpenBatchDialog = (batch) => {
    setSelectedBatch(batch);
    setBatchDialogOpen(true);
  };

  const handleCloseBatchDialog = () => {
    setSelectedBatch(null);
    setBatchDialogOpen(false);
  };

  const handleDeleteBatch = async (batch) => {
    if (!window.confirm(`確定要刪除批次「${batch.serial_number} - ${formatDate(batch.uploaded_at)}」的所有檔案嗎？此操作無法復原。`)) {
      return;
    }

    try {
      await logService.deleteBatch(batch.batch_id, batch.serial_number);
      alert('批次刪除成功');
      fetchLogs(); // 重新載入列表
    } catch (error) {
      console.error('Failed to delete batch:', error);
      alert('刪除批次失敗：' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteFile = async (serialNumber, filename) => {
    if (!window.confirm(`確定要刪除檔案「${filename}」嗎？此操作無法復原。`)) {
      return;
    }

    try {
      await logService.deleteFile(serialNumber, filename);
      alert('檔案刪除成功');
      // 如果是在 dialog 中刪除，關閉 dialog 並重新載入
      if (selectedBatch) {
        handleCloseBatchDialog();
      }
      fetchLogs(); // 重新載入列表
    } catch (error) {
      console.error('Failed to delete file:', error);
      alert('刪除檔案失敗：' + (error.response?.data?.detail || error.message));
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
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
          Log 檔案管理
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
            <IconButton onClick={fetchLogs} disabled={loading}>
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

      {/* 批次列表表格 */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>客戶編號</TableCell>
              <TableCell>公司名稱</TableCell>
              <TableCell>序號</TableCell>
              <TableCell>上傳時間</TableCell>
              <TableCell>問題描述</TableCell>
              <TableCell>檔案數量</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : groupedLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary">
                    {searchTerm || customerIdFilter ? '沒有找到符合條件的 log 檔案' : '暫無 log 檔案'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              groupedLogs.map((batch, index) => (
                <TableRow key={index} hover>
                  <TableCell>{batch.customer_tax_id || '-'}</TableCell>
                  <TableCell>{batch.customer_name || '-'}</TableCell>
                  <TableCell>
                    <Chip label={batch.serial_number} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>{formatDate(batch.uploaded_at)}</TableCell>
                  <TableCell>
                    {batch.problem_description ? (
                      <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {batch.problem_description}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip label={`${batch.files.length} 個檔案`} size="small" />
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="查看檔案列表">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenBatchDialog(batch)}
                        >
                          <FolderIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="刪除批次">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteBatch(batch)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
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
            label={`共 ${computedTotalCount} 個批次`}
            color="primary"
            variant="outlined"
          />
        </Box>

        <Pagination
          count={computedTotalPages}
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

      {/* 批次檔案列表 Dialog */}
      <Dialog
        open={batchDialogOpen}
        onClose={handleCloseBatchDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          批次檔案列表
          {selectedBatch && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              序號: {selectedBatch.serial_number} | 
              上傳時間: {formatDate(selectedBatch.uploaded_at)}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedBatch && (
            <>
              {selectedBatch.problem_description && (
                <>
                  <Typography variant="subtitle2" sx={{ mb: 1, mt: 1 }}>
                    問題描述：
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                    {selectedBatch.problem_description}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                </>
              )}
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                檔案列表（共 {selectedBatch.files.length} 個檔案）：
              </Typography>
              <List>
                {selectedBatch.files.map((file, index) => (
                  <ListItem
                    key={index}
                    secondaryAction={
                      <Stack direction="row" spacing={1}>
                        <Tooltip title="下載">
                          <IconButton
                            edge="end"
                            onClick={() => handleDownload(selectedBatch.serial_number, file.filename)}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="刪除">
                          <IconButton
                            edge="end"
                            color="error"
                            onClick={() => handleDeleteFile(selectedBatch.serial_number, file.filename)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    }
                  >
                    <ListItemText
                      primary={file.filename}
                      secondary={`大小: ${formatFileSize(file.file_size)}`}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseBatchDialog}>關閉</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default LogsPage;
