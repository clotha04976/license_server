import React, { useState, useEffect } from 'react';
import featureService from '../api/featureService';
import FeatureForm from '../components/forms/FeatureForm';
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
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

function FeaturesPage() {
  const [features, setFeatures] = useState([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState(null);

  useEffect(() => {
    fetchFeatures();
  }, []);

  const fetchFeatures = async () => {
    try {
      const response = await featureService.getFeatures();
      setFeatures(response.data);
    } catch (error) {
      console.error('Failed to fetch features:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('您確定要刪除此功能嗎？')) {
      try {
        await featureService.deleteFeature(id);
        fetchFeatures();
      } catch (error) {
        console.error('Failed to delete feature:', error);
      }
    }
  };

  const handleOpenForm = (feature = null) => {
    setSelectedFeature(feature);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setSelectedFeature(null);
    setIsFormOpen(false);
  };

  const handleSave = async (formData) => {
    try {
      if (selectedFeature) {
        await featureService.updateFeature(selectedFeature.id, formData);
      } else {
        await featureService.createFeature(formData);
      }
      fetchFeatures();
      handleCloseForm();
    } catch (error) {
      console.error('Failed to save feature:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          功能
        </Typography>
        <Button variant="contained" onClick={() => handleOpenForm()}>新增功能</Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>名稱</TableCell>
              <TableCell>描述</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {features.map((feature) => (
              <TableRow key={feature.id}>
                <TableCell>{feature.name}</TableCell>
                <TableCell>{feature.description}</TableCell>
                <TableCell>
                  <IconButton aria-label="edit" onClick={() => handleOpenForm(feature)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton aria-label="delete" onClick={() => handleDelete(feature.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <FeatureForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleSave}
        feature={selectedFeature}
      />
    </Box>
  );
}

export default FeaturesPage;