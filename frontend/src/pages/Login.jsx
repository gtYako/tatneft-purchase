import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #1a237e 0%, #283593 60%, #1565c0 100%)' }}>
      <div className="card shadow-lg" style={{ width: 400 }}>
        <div className="card-body p-4">
          <div className="text-center mb-4">
            <div style={{ fontSize: '2.5rem', color: '#1a237e' }}>
              <i className="bi bi-droplet-fill text-warning"></i>
            </div>
            <h4 className="fw-bold mt-2 mb-0" style={{ color: '#1a237e' }}>Система закупок МТО</h4>
            <div className="text-muted small">Нефтедобывающее предприятие</div>
          </div>

          {error && (
            <div className="alert alert-danger py-2 small">
              <i className="bi bi-exclamation-circle me-1"></i>{error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Логин</label>
              <input
                type="text" className="form-control" autoFocus required
                placeholder="admin / initiator / purchaser / analyst / manager"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              />
            </div>
            <div className="mb-4">
              <label className="form-label fw-semibold small">Пароль</label>
              <input
                type="password" className="form-control" required
                placeholder="demo1234"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              />
            </div>
            <button type="submit" className="btn btn-primary w-100 fw-semibold" disabled={loading}>
              {loading
                ? <><span className="spinner-border spinner-border-sm me-2" />Вход...</>
                : <><i className="bi bi-box-arrow-in-right me-2"></i>Войти</>
              }
            </button>
          </form>

          <div className="mt-4 p-3 rounded small" style={{ background: '#f0f4ff' }}>
            <div className="fw-semibold mb-1 text-muted">Тестовые аккаунты (пароль: demo1234)</div>
            {[
              ['admin', 'Администратор'],
              ['purchaser', 'Закупщик'],
              ['initiator', 'Инициатор'],
              ['analyst', 'Аналитик'],
              ['manager', 'Руководитель'],
            ].map(([u, label]) => (
              <div key={u} className="d-flex justify-content-between">
                <code className="text-primary" style={{ cursor: 'pointer' }}
                  onClick={() => setForm({ username: u, password: 'demo1234' })}>
                  {u}
                </code>
                <span className="text-muted">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
