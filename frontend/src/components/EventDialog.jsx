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
  Box,
  Chip,
  Checkbox,
  FormControlLabel,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import licenseService from '../api/licenseService';

function EventDialog({ open, onClose, licenseId, licenseSerialNumber }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [selectedEvents, setSelectedEvents] = useState([]);
  const [confirmedBy, setConfirmedBy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (open && licenseId) {
      fetchEvents();
    }
  }, [open, licenseId]);

  const fetchEvents = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await licenseService.getUnconfirmedEvents(licenseId);
      setEvents(response.data);
    } catch (err) {
      setError('獲取事件列表失敗');
      console.error('Failed to fetch events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEvent = (eventId) => {
    setSelectedEvents(prev => 
      prev.includes(eventId) 
        ? prev.filter(id => id !== eventId)
        : [...prev, eventId]
    );
  };

  const handleSelectAll = () => {
    if (selectedEvents.length === events.length) {
      setSelectedEvents([]);
    } else {
      setSelectedEvents(events.map(event => event.id));
    }
  };

  const handleConfirmEvents = async () => {
    if (selectedEvents.length === 0) {
      setError('請選擇要確認的事件');
      return;
    }
    if (!confirmedBy.trim()) {
      setError('請輸入確認者姓名');
      return;
    }

    setConfirming(true);
    setError('');
    
    try {
      // 批量確認事件
      const confirmPromises = selectedEvents.map(eventId => 
        licenseService.confirmEvent(eventId, confirmedBy)
      );
      
      await Promise.all(confirmPromises);
      
      // 重新獲取事件列表
      await fetchEvents();
      setSelectedEvents([]);
      setConfirmedBy('');
      
      // 通知父組件更新
      if (onClose) {
        onClose(true); // 傳遞 true 表示有更新
      }
    } catch (err) {
      setError('確認事件失敗');
      console.error('Failed to confirm events:', err);
    } finally {
      setConfirming(false);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <WarningIcon color="error" />;
      case 'suspicious':
        return <WarningIcon color="warning" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'suspicious':
        return 'warning';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getEventTypeText = (eventType, eventSubtype) => {
    const typeMap = {
      'activation': '啟用',
      're_activation': '重新啟用',
      'hardware_change': '硬體變化',
      'validation': '驗證',
      'deactivation': '停用'
    };
    
    const subtypeMap = {
      'new_activation': '新啟用',
      'machine_code_match': '機器碼匹配',
      'hardware_id_match': '硬體ID匹配',
      'validation_hardware_change': '驗證時硬體變化'
    };
    
    const typeText = typeMap[eventType] || eventType;
    const subtypeText = subtypeMap[eventSubtype] || eventSubtype;
    
    return subtypeText ? `${typeText} - ${subtypeText}` : typeText;
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

  const formatDetails = (details) => {
    if (!details) return '無';
    
    const info = [];
    
    // 顯示機器碼變化
    if (details.machine_code_updated !== undefined) {
      info.push(`機器碼更新: ${details.machine_code_updated ? '是' : '否'}`);
    }
    
    // 顯示硬體更新
    if (details.hardware_updated !== undefined) {
      info.push(`硬體更新: ${details.hardware_updated ? '是' : '否'}`);
    }
    
    // 顯示硬體變化詳細資訊
    if (details.hardware_changes) {
      const changes = [];
      Object.entries(details.hardware_changes).forEach(([key, value]) => {
        if (value.old !== value.new) {
          const oldValue = value.old ? value.old.substring(0, 8) + '...' : '無';
          const newValue = value.new ? value.new.substring(0, 8) + '...' : '無';
          changes.push(`${key}: ${oldValue} → ${newValue}`);
        }
      });
      if (changes.length > 0) {
        info.push(`硬體變化: ${changes.join(', ')}`);
      }
    }
    
    // 如果有其他詳細資訊，也顯示出來
    const otherDetails = { ...details };
    delete otherDetails.machine_code_updated;
    delete otherDetails.hardware_updated;
    delete otherDetails.hardware_changes;
    
    if (Object.keys(otherDetails).length > 0) {
      info.push(`其他: ${JSON.stringify(otherDetails, null, 2)}`);
    }
    
    return info.length > 0 ? info.join('\n') : '無變化';
  };

  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          <Typography variant="h6">
            授權事件監控 - {licenseSerialNumber}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : events.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 3 }}>
            <CheckCircleIcon color="success" sx={{ fontSize: 48, mb: 1 }} />
            <Typography variant="h6" color="success.main">
              沒有未確認的事件
            </Typography>
            <Typography variant="body2" color="text.secondary">
              所有事件都已經確認，沒有可疑活動
            </Typography>
          </Box>
        ) : (
          <>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle1">
                發現 {events.length} 個未確認事件
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedEvents.length === events.length}
                    indeterminate={selectedEvents.length > 0 && selectedEvents.length < events.length}
                    onChange={handleSelectAll}
                  />
                }
                label="全選"
              />
            </Box>
            
            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">選擇</TableCell>
                    <TableCell>時間</TableCell>
                    <TableCell>事件類型</TableCell>
                    <TableCell>嚴重程度</TableCell>
                    <TableCell>機器碼</TableCell>
                    <TableCell>IP地址</TableCell>
                    <TableCell>詳細資訊</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {events.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedEvents.includes(event.id)}
                          onChange={() => handleSelectEvent(event.id)}
                        />
                      </TableCell>
                      <TableCell>
                        {formatDateTime(event.created_at)}
                      </TableCell>
                      <TableCell>
                        {getEventTypeText(event.event_type, event.event_subtype)}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getSeverityIcon(event.severity)}
                          <Chip 
                            label={event.severity} 
                            color={getSeverityColor(event.severity)}
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                        {event.machine_code ? event.machine_code.substring(0, 16) + (event.machine_code.length > 16 ? '...' : '') : '無'}
                      </TableCell>
                      <TableCell>
                        {event.ip_address || '無'}
                      </TableCell>
                      <TableCell sx={{ maxWidth: 200 }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            wordBreak: 'break-word',
                            whiteSpace: 'pre-wrap',
                            fontSize: '0.75rem'
                          }}
                        >
                          {formatDetails(event.details)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </DialogContent>
      
      {events.length > 0 && (
        <DialogActions sx={{ p: 2, flexDirection: 'column', gap: 2 }}>
          <Box sx={{ width: '100%', display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              label="確認者姓名"
              value={confirmedBy}
              onChange={(e) => setConfirmedBy(e.target.value)}
              size="small"
              sx={{ flexGrow: 1 }}
            />
            <Button
              onClick={handleConfirmEvents}
              variant="contained"
              color="primary"
              disabled={confirming || selectedEvents.length === 0}
              startIcon={confirming ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            >
              {confirming ? '確認中...' : `確認選中事件 (${selectedEvents.length})`}
            </Button>
          </Box>
          <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
            <Button onClick={() => onClose(false)}>
              關閉
            </Button>
            <Typography variant="body2" color="text.secondary">
              已選擇 {selectedEvents.length} / {events.length} 個事件
            </Typography>
          </Box>
        </DialogActions>
      )}
    </Dialog>
  );
}

export default EventDialog;
