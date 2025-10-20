import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Snackbar,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ComputerIcon from '@mui/icons-material/Computer';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import BlockIcon from '@mui/icons-material/Block';
import licenseService from '../api/licenseService';

function ActivationsDialog({ open, onClose, licenseId, licenseSerialNumber }) {
  const [activations, setActivations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    if (open && licenseId) {
      fetchActivations();
    }
  }, [open, licenseId]);

  const fetchActivations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await licenseService.getLicenseActivations(licenseId);
      setActivations(response.data);
    } catch (error) {
      console.error('Failed to fetch activations:', error);
      setError('獲取啟用記錄失敗');
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleDeleteActivation = async (activationId) => {
    if (window.confirm('此刪除會直接讓使用者可以再次註冊，確定要直接刪除嗎？')) {
      try {
        await licenseService.deleteActivation(activationId);
        // 從本地狀態中移除該筆記錄
        setActivations(prevActivations => 
          prevActivations.filter(activation => activation.id !== activationId)
        );
        showSnackbar('啟用記錄已成功刪除', 'success');
      } catch (error) {
        console.error('Failed to delete activation:', error);
        // 嘗試從錯誤回應中取得詳細訊息
        let errorMessage = '刪除啟用記錄失敗';
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        showSnackbar(errorMessage, 'error');
      }
    }
  };

  const handleBlacklistActivation = async (activationId) => {
    if (window.confirm('確定要將此啟用記錄加入黑名單嗎？加入黑名單後，該電腦將無法再次驗證授權。')) {
      try {
        await licenseService.blacklistActivation(activationId);
        // 更新本地狀態
        setActivations(prevActivations =>
          prevActivations.map(activation =>
            activation.id === activationId
              ? { ...activation, status: 'blacklisted', blacklisted_at: new Date().toISOString() }
              : activation
          )
        );
        showSnackbar('啟用記錄已加入黑名單', 'success');
      } catch (error) {
        console.error('Failed to blacklist activation:', error);
        // 嘗試從錯誤回應中取得詳細訊息
        let errorMessage = '加入黑名單失敗';
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        showSnackbar(errorMessage, 'error');
      }
    }
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
      active: '啟用中',
      deactivated: '已停用',
      blacklisted: '黑名單',
    };
    const colorMap = {
      active: 'success',
      deactivated: 'default',
      blacklisted: 'error',
    };
    const iconMap = {
      active: <CheckCircleIcon />,
      deactivated: <CancelIcon />,
      blacklisted: <BlockIcon />,
    };
    return (
      <Chip
        label={statusMap[status] || status}
        color={colorMap[status] || 'default'}
        size="small"
        icon={iconMap[status] || <CancelIcon />}
      />
    );
  };

  const formatDateTime = (dateTime) => {
    if (!dateTime) return '無';
    
    // 確保時間字串被正確解析為 UTC 時間
    let date;
    if (typeof dateTime === 'string') {
      // 如果字串沒有時區資訊，假設它是 UTC 時間
      if (!dateTime.includes('Z') && !dateTime.includes('+') && !dateTime.includes('-', 10)) {
        date = new Date(dateTime + 'Z');
      } else {
        date = new Date(dateTime);
      }
    } else {
      date = new Date(dateTime);
    }
    
    // 轉換為台北時間
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

  const truncateText = (text, maxLength = 20) => {
    if (!text) return '無';
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">
            授權啟用記錄 - {licenseSerialNumber}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
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
          <>
            {activations.length === 0 ? (
              <Alert severity="info">
                此授權尚未有任何啟用記錄
              </Alert>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>綁定硬體資訊</TableCell>
                      <TableCell>狀態</TableCell>
                      <TableCell>IP 位址</TableCell>
                      <TableCell>啟用時間</TableCell>
                      <TableCell>最後驗證時間</TableCell>
                      <TableCell>停用時間</TableCell>
                      <TableCell>黑名單時間</TableCell>
                      <TableCell>操作</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {activations.map((activation) => (
                      <TableRow key={activation.id}>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {/* 機器碼 */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ minWidth: '50px' }}>
                                機器碼:
                              </Typography>
                              <Tooltip title={activation.machine_code}>
                                <Typography variant="body2" sx={{ fontFamily: 'monospace', flex: 1 }}>
                                  {truncateText(activation.machine_code, 40)}
                                </Typography>
                              </Tooltip>
                              <IconButton
                                size="small"
                                onClick={() => copyToClipboard(activation.machine_code, '機器碼已複製到剪貼簿')}
                              >
                                <ContentCopyIcon fontSize="inherit" />
                              </IconButton>
                            </Box>
                            
                            {/* 硬體 ID */}
                            {(activation.keypro_id || activation.motherboard_id || activation.disk_id) && (
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, ml: 1 }}>
                                {activation.keypro_id && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: '50px' }}>
                                      加密狗:
                                    </Typography>
                                    <Tooltip title={activation.keypro_id}>
                                      <Typography variant="caption" sx={{ fontFamily: 'monospace', flex: 1 }}>
                                        {truncateText(activation.keypro_id, 30)}
                                      </Typography>
                                    </Tooltip>
                                    <IconButton
                                      size="small"
                                      onClick={() => copyToClipboard(activation.keypro_id, '加密狗 ID 已複製')}
                                    >
                                      <ContentCopyIcon fontSize="inherit" />
                                    </IconButton>
                                  </Box>
                                )}
                                {activation.motherboard_id && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: '50px' }}>
                                      主機板:
                                    </Typography>
                                    <Tooltip title={activation.motherboard_id}>
                                      <Typography variant="caption" sx={{ fontFamily: 'monospace', flex: 1 }}>
                                        {truncateText(activation.motherboard_id, 30)}
                                      </Typography>
                                    </Tooltip>
                                    <IconButton
                                      size="small"
                                      onClick={() => copyToClipboard(activation.motherboard_id, '主機板 ID 已複製')}
                                    >
                                      <ContentCopyIcon fontSize="inherit" />
                                    </IconButton>
                                  </Box>
                                )}
                                {activation.disk_id && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: '50px' }}>
                                      硬碟:
                                    </Typography>
                                    <Tooltip title={activation.disk_id}>
                                      <Typography variant="caption" sx={{ fontFamily: 'monospace', flex: 1 }}>
                                        {truncateText(activation.disk_id, 40)}
                                      </Typography>
                                    </Tooltip>
                                    <IconButton
                                      size="small"
                                      onClick={() => copyToClipboard(activation.disk_id, '硬碟 ID 已複製')}
                                    >
                                      <ContentCopyIcon fontSize="inherit" />
                                    </IconButton>
                                  </Box>
                                )}
                              </Box>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>{getStatusChip(activation.status)}</TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {activation.ip_address || '無'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(activation.activated_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(activation.last_validated_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(activation.deactivated_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(activation.blacklisted_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            {activation.status !== 'blacklisted' && (
                              <Tooltip title="加入黑名單">
                                <IconButton
                                  size="small"
                                  onClick={() => handleBlacklistActivation(activation.id)}
                                  sx={{ color: 'warning.main' }}
                                >
                                  <BlockIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="刪除啟用記錄">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteActivation(activation.id)}
                                sx={{ color: 'error.main' }}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>關閉</Button>
      </DialogActions>

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
    </Dialog>
  );
}

export default ActivationsDialog;
