import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
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
import UserList from './pages/admin/UserList.jsx'
import UserForm from './pages/admin/UserForm.jsx'
import AuditLog from './pages/admin/AuditLog.jsx'
import MonitoringPage from './pages/monitoring/MonitoringPage.jsx'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="spinner-center">
      <div className="spinner-border text-primary" role="status" />
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

const ROLE_LABELS = {
  admin: 'Администратор',
  purchaser: 'Закупщик',
  initiator: 'Инициатор',
  analyst: 'Аналитик',
  manager: 'Руководитель',
}

function AccessDenied({ roles = [] }) {
  const { user } = useAuth()
  const allowed = roles.map(role => ROLE_LABELS[role] || role).join(', ')
  const current = ROLE_LABELS[user?.role] || user?.role || 'не определена'

  return (
    <div className="card border-warning shadow-sm">
      <div className="card-body p-4">
        <div className="d-flex align-items-start gap-3">
          <div className="text-warning" style={{ fontSize: '2rem', lineHeight: 1 }}>
            <i className="bi bi-shield-lock-fill"></i>
          </div>
          <div>
            <h1 className="h4 mb-2">Недостаточно прав</h1>
            <p className="text-muted mb-2">
              Эта страница недоступна для вашей роли. Текущая роль: <strong>{current}</strong>.
            </p>
            {allowed && (
              <p className="text-muted small mb-3">
                Доступ разрешен для ролей: {allowed}.
              </p>
            )}
            <div className="d-flex gap-2">
              <Link to="/" className="btn btn-primary">
                <i className="bi bi-house-door me-1"></i>На главную
              </Link>
              <button type="button" className="btn btn-outline-secondary" onClick={() => window.history.back()}>
                Назад
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function RoleRoute({ roles, children }) {
  const { user } = useAuth()
  if (!roles || roles.includes(user?.role)) return children
  return <AccessDenied roles={roles} />
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
              <Route path="/catalog/new" element={<RoleRoute roles={['admin', 'purchaser']}><MaterialForm /></RoleRoute>} />
              <Route path="/catalog/:pk" element={<MaterialDetail />} />
              <Route path="/catalog/:pk/edit" element={<RoleRoute roles={['admin', 'purchaser']}><MaterialForm /></RoleRoute>} />

              <Route path="/categories" element={<RoleRoute roles={['admin', 'purchaser']}><CategoryList /></RoleRoute>} />
              <Route path="/categories/new" element={<RoleRoute roles={['admin', 'purchaser']}><CategoryForm /></RoleRoute>} />
              <Route path="/categories/:pk/edit" element={<RoleRoute roles={['admin', 'purchaser']}><CategoryForm /></RoleRoute>} />

              <Route path="/warehouse" element={<RoleRoute roles={['admin', 'purchaser', 'analyst']}><StockList /></RoleRoute>} />
              <Route path="/warehouse/new" element={<RoleRoute roles={['admin', 'purchaser', 'analyst']}><StockForm /></RoleRoute>} />
              <Route path="/warehouse/:pk/edit" element={<RoleRoute roles={['admin', 'purchaser', 'analyst']}><StockForm /></RoleRoute>} />

              <Route path="/requests" element={<RequestList />} />
              <Route path="/requests/new" element={<RequestForm />} />
              <Route path="/requests/:pk" element={<RequestDetail />} />
              <Route path="/requests/:pk/edit" element={<RequestForm />} />
              <Route path="/items/:itemPk/analyse" element={<RoleRoute roles={['admin', 'purchaser', 'analyst', 'manager']}><QuoteSelect /></RoleRoute>} />

              <Route path="/suppliers" element={<RoleRoute roles={['admin', 'purchaser']}><SupplierList /></RoleRoute>} />
              <Route path="/suppliers/new" element={<RoleRoute roles={['admin', 'purchaser']}><SupplierForm /></RoleRoute>} />
              <Route path="/suppliers/:pk" element={<RoleRoute roles={['admin', 'purchaser']}><SupplierDetail /></RoleRoute>} />
              <Route path="/suppliers/:pk/edit" element={<RoleRoute roles={['admin', 'purchaser']}><SupplierForm /></RoleRoute>} />

              <Route path="/quotes" element={<RoleRoute roles={['admin', 'purchaser']}><QuoteList /></RoleRoute>} />
              <Route path="/quotes/new" element={<RoleRoute roles={['admin', 'purchaser']}><QuoteForm /></RoleRoute>} />
              <Route path="/quotes/:pk/edit" element={<RoleRoute roles={['admin', 'purchaser']}><QuoteForm /></RoleRoute>} />

              <Route path="/orders" element={<OrderList />} />
              <Route path="/orders/new/:requestPk" element={<RoleRoute roles={['admin', 'purchaser']}><OrderForm /></RoleRoute>} />
              <Route path="/orders/:pk" element={<OrderDetail />} />

              <Route path="/analytics" element={<RoleRoute roles={['admin', 'purchaser', 'analyst', 'manager']}><AnalyticsDashboard /></RoleRoute>} />
              <Route path="/analytics/prices" element={<RoleRoute roles={['admin', 'purchaser', 'analyst', 'manager']}><PriceDynamics /></RoleRoute>} />
              <Route path="/analytics/shortage" element={<RoleRoute roles={['admin', 'purchaser', 'analyst', 'manager']}><ShortageReport /></RoleRoute>} />
              <Route path="/admin/users" element={<RoleRoute roles={['admin']}><UserList /></RoleRoute>} />
              <Route path="/admin/users/new" element={<RoleRoute roles={['admin']}><UserForm /></RoleRoute>} />
              <Route path="/admin/users/:pk/edit" element={<RoleRoute roles={['admin']}><UserForm /></RoleRoute>} />
              <Route path="/admin/audit" element={<RoleRoute roles={['admin']}><AuditLog /></RoleRoute>} />
              <Route path="/monitoring" element={<RoleRoute roles={['admin']}><MonitoringPage /></RoleRoute>} />
              <Route path="*" element={<Navigate to="/" replace />} />
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
