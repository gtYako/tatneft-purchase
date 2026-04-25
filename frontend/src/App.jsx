import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'

import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CategoryList from './pages/catalog/CategoryList.jsx'
import CategoryForm from './pages/catalog/CategoryForm.jsx'
import MaterialList from './pages/catalog/MaterialList.jsx'
import MaterialDetail from './pages/catalog/MaterialDetail.jsx'
import MaterialForm from './pages/catalog/MaterialForm.jsx'
import StockList from './pages/warehouse/StockList.jsx'
import StockForm from './pages/warehouse/StockForm.jsx'
import RequestList from './pages/requests/RequestList.jsx'
import RequestDetail from './pages/requests/RequestDetail.jsx'
import RequestForm from './pages/requests/RequestForm.jsx'
import QuoteSelect from './pages/requests/QuoteSelect.jsx'
import SupplierList from './pages/suppliers/SupplierList.jsx'
import SupplierDetail from './pages/suppliers/SupplierDetail.jsx'
import SupplierForm from './pages/suppliers/SupplierForm.jsx'
import QuoteList from './pages/suppliers/QuoteList.jsx'
import QuoteForm from './pages/suppliers/QuoteForm.jsx'
import OrderList from './pages/orders/OrderList.jsx'
import OrderDetail from './pages/orders/OrderDetail.jsx'
import OrderForm from './pages/orders/OrderForm.jsx'
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard.jsx'
import PriceDynamics from './pages/analytics/PriceDynamics.jsx'
import ShortageReport from './pages/analytics/ShortageReport.jsx'
import Reports from './pages/analytics/Reports.jsx'
import UserList from './pages/admin/UserList.jsx'
import UserForm from './pages/admin/UserForm.jsx'
import AuditLog from './pages/admin/AuditLog.jsx'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="spinner-center">
      <div className="spinner-border text-primary" role="status" />
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="spinner-center">
      <div className="spinner-border text-primary" role="status" />
    </div>
  )

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />

      <Route path="/*" element={
        <PrivateRoute>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />

              <Route path="/catalog" element={<MaterialList />} />
              <Route path="/catalog/new" element={<MaterialForm />} />
              <Route path="/catalog/:pk" element={<MaterialDetail />} />
              <Route path="/catalog/:pk/edit" element={<MaterialForm />} />

              <Route path="/categories" element={<CategoryList />} />
              <Route path="/categories/new" element={<CategoryForm />} />
              <Route path="/categories/:pk/edit" element={<CategoryForm />} />

              <Route path="/warehouse" element={<StockList />} />
              <Route path="/warehouse/new" element={<StockForm />} />
              <Route path="/warehouse/:pk/edit" element={<StockForm />} />

              <Route path="/requests" element={<RequestList />} />
              <Route path="/requests/new" element={<RequestForm />} />
              <Route path="/requests/:pk" element={<RequestDetail />} />
              <Route path="/requests/:pk/edit" element={<RequestForm />} />
              <Route path="/items/:itemPk/analyse" element={<QuoteSelect />} />

              <Route path="/suppliers" element={<SupplierList />} />
              <Route path="/suppliers/new" element={<SupplierForm />} />
              <Route path="/suppliers/:pk" element={<SupplierDetail />} />
              <Route path="/suppliers/:pk/edit" element={<SupplierForm />} />

              <Route path="/quotes" element={<QuoteList />} />
              <Route path="/quotes/new" element={<QuoteForm />} />
              <Route path="/quotes/:pk/edit" element={<QuoteForm />} />

              <Route path="/orders" element={<OrderList />} />
              <Route path="/orders/new/:requestPk" element={<OrderForm />} />
              <Route path="/orders/:pk" element={<OrderDetail />} />

              <Route path="/analytics" element={<AnalyticsDashboard />} />
              <Route path="/analytics/prices" element={<PriceDynamics />} />
              <Route path="/analytics/shortage" element={<ShortageReport />} />
              <Route path="/analytics/reports" element={<Reports />} />

              <Route path="/admin/users" element={<UserList />} />
              <Route path="/admin/users/new" element={<UserForm />} />
              <Route path="/admin/users/:pk/edit" element={<UserForm />} />
              <Route path="/admin/audit" element={<AuditLog />} />
            </Routes>
          </Layout>
        </PrivateRoute>
      } />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
