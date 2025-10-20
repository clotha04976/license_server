import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import PrivateRoute from '../components/common/PrivateRoute';
import AppLayout from '../components/common/AppLayout';
import DashboardPage from '../pages/DashboardPage';
import CustomersPage from '../pages/CustomersPage';
import ProductsPage from '../pages/ProductsPage';
import LicensesPage from '../pages/LicensesPage';
import FeaturesPage from '../pages/FeaturesPage';
import EventLogPage from '../pages/EventLogPage';

function AppRouter() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<PrivateRoute />}>
          <Route path="/" element={<AppLayout />}>
            {/* Child routes of AppLayout */}
            <Route index element={<DashboardPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="licenses" element={<LicensesPage />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="features" element={<FeaturesPage />} />
            <Route path="event-logs" element={<EventLogPage />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  );
}

export default AppRouter;