import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

function DashboardPage() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        儀表板
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography variant="body1">
          歡迎使用授權伺服器管理儀表板。
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          請從側邊欄選擇一個選項來管理客戶、產品或授權。
        </Typography>
      </Paper>
    </Box>
  );
}

export default DashboardPage;