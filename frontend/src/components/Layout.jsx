import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

const ROLE_LABELS = {
  admin: 'Администратор',
  purchaser: 'Закупщик',
  initiator: 'Инициатор',
  analyst: 'Аналитик',
  manager: 'Руководитель',
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const canSeeAnalytics = ['analyst', 'manager', 'admin', 'purchaser'].includes(user?.role)
  const canSeeReports   = ['analyst', 'manager', 'admin'].includes(user?.role)
  const canManageCatalog   = ['admin', 'purchaser'].includes(user?.role)
  const canManageSuppliers = ['admin', 'purchaser'].includes(user?.role)
  const canManageWarehouse = ['admin', 'purchaser', 'analyst'].includes(user?.role)
  const isAdmin = user?.role === 'admin'

  return (
    <div className="d-flex" style={{ minHeight: '100vh' }}>
      {/* Sidebar */}
      <nav className="sidebar d-flex flex-column py-3">
        <div className="px-3 mb-3">
          <div className="text-white fw-bold" style={{ fontSize: '0.95rem', lineHeight: 1.3 }}>
            <i className="bi bi-droplet-fill me-2 text-warning"></i>
            Система закупок МТО
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
            Нефтедобывающее предприятие
          </div>
        </div>

        <div className="nav-section">Главное</div>
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <i className="bi bi-speedometer2"></i> Дашборд
        </NavLink>
        <NavLink to="/requests" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <i className="bi bi-file-earmark-text"></i> Заявки
        </NavLink>
        <NavLink to="/orders" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <i className="bi bi-cart3"></i> Заказы
        </NavLink>

        <div className="nav-section">Справочники</div>
        <NavLink to="/catalog" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <i className="bi bi-box-seam"></i> Каталог МТР
        </NavLink>
        {canManageCatalog && (
          <NavLink to="/categories" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <i className="bi bi-tags"></i> Категории
          </NavLink>
        )}
        {canManageWarehouse && (
          <NavLink to="/warehouse" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <i className="bi bi-archive"></i> Склад
          </NavLink>
        )}
        {canManageSuppliers && (
          <>
            <NavLink to="/suppliers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-building"></i> Поставщики
            </NavLink>
            <NavLink to="/quotes" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-currency-dollar"></i> Ценовые предложения
            </NavLink>
          </>
        )}

        {canSeeAnalytics && (
          <>
            <div className="nav-section">Аналитика</div>
            <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-bar-chart"></i> Дашборд
            </NavLink>
            <NavLink to="/analytics/prices" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-graph-up-arrow"></i> Динамика цен
            </NavLink>
            <NavLink to="/analytics/shortage" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-exclamation-triangle"></i> Дефицит
            </NavLink>
            {canSeeReports && (
              <NavLink to="/analytics/reports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <i className="bi bi-clipboard-data"></i> Отчёты
              </NavLink>
            )}
          </>
        )}

        {isAdmin && (
          <>
            <div className="nav-section">Администрирование</div>
            <NavLink to="/admin/users" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-people"></i> Пользователи
            </NavLink>
            <NavLink to="/admin/audit" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className="bi bi-journal-text"></i> Журнал операций
            </NavLink>
          </>
        )}

        <div className="mt-auto px-3 pb-2">
          <div className="text-white-50 small mb-1" style={{ fontSize: '0.78rem' }}>
            <i className="bi bi-person-circle me-1"></i>
            {user?.full_name || user?.username}
          </div>
          <div className="badge bg-warning text-dark mb-2" style={{ fontSize: '0.7rem' }}>
            {ROLE_LABELS[user?.role] || user?.role}
          </div>
          <br />
          <button className="btn btn-sm btn-outline-light w-100" onClick={handleLogout}>
            <i className="bi bi-box-arrow-right me-1"></i> Выйти
          </button>
        </div>
      </nav>

      {/* Main */}
      <div className="main-content d-flex flex-column">
        <div className="topbar d-flex align-items-center px-4">
          <span className="text-muted small">
            {user?.department && <><i className="bi bi-geo-alt me-1"></i>{user.department}</>}
          </span>
        </div>
        <div className="p-4 flex-grow-1">
          {children}
        </div>
      </div>
    </div>
  )
}
