import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

const ROLES = [
  { value: 'initiator', label: 'Инициатор' },
  { value: 'purchaser', label: 'Закупщик' },
  { value: 'analyst', label: 'Аналитик' },
  { value: 'manager', label: 'Руководитель' },
  { value: 'admin', label: 'Администратор' },
]

export default function UserForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(pk)

  const [form, setForm] = useState({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    email: '',
    role: 'initiator',
    is_active: true,
  })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!isEdit) return
    axios.get(`/api/admin/users/${pk}/`).then(r => {
      const d = r.data
      setForm({
        username: d.username || '',
        password: '',
        first_name: d.first_name || '',
        last_name: d.last_name || '',
        email: d.email || '',
        role: d.role || 'initiator',
        is_active: d.is_active ?? true,
      })
    }).finally(() => setLoading(false))
  }, [pk])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async e => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    const payload = { ...form }
    if (!payload.password) delete payload.password
    try {
      if (isEdit) {
        await axios.patch(`/api/admin/users/${pk}/`, payload)
      } else {
        await axios.post('/api/admin/users/', payload)
      }
      navigate('/admin/users')
    } catch (err) {
      setErrors(err.response?.data || {})
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to="/admin/users" className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left"></i>
        </Link>
        <h1 className="page-title mb-0">{isEdit ? 'Редактирование пользователя' : 'Новый пользователь'}</h1>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Логин <span className="text-danger">*</span></label>
              <input className={`form-control ${errors.username ? 'is-invalid' : ''}`}
                value={form.username} required onChange={e => set('username', e.target.value)}
                disabled={isEdit} />
              {errors.username && <div className="invalid-feedback">{errors.username}</div>}
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold small">
                Пароль {!isEdit && <span className="text-danger">*</span>}
                {isEdit && <span className="text-muted"> (оставьте пустым, чтобы не менять)</span>}
              </label>
              <input type="password" className={`form-control ${errors.password ? 'is-invalid' : ''}`}
                value={form.password} required={!isEdit}
                onChange={e => set('password', e.target.value)} />
              {errors.password && <div className="invalid-feedback">{errors.password}</div>}
            </div>

            <div className="row g-3 mb-3">
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Имя</label>
                <input className="form-control" value={form.first_name}
                  onChange={e => set('first_name', e.target.value)} />
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Фамилия</label>
                <input className="form-control" value={form.last_name}
                  onChange={e => set('last_name', e.target.value)} />
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold small">Email</label>
              <input type="email" className={`form-control ${errors.email ? 'is-invalid' : ''}`}
                value={form.email} onChange={e => set('email', e.target.value)} />
              {errors.email && <div className="invalid-feedback">{errors.email}</div>}
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold small">Роль <span className="text-danger">*</span></label>
              <select className="form-select" value={form.role} required onChange={e => set('role', e.target.value)}>
                {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>

            <div className="mb-4">
              <div className="form-check">
                <input type="checkbox" className="form-check-input" id="isActive"
                  checked={form.is_active} onChange={e => set('is_active', e.target.checked)} />
                <label className="form-check-label fw-semibold small" htmlFor="isActive">Активен</label>
              </div>
            </div>

            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-primary fw-semibold" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                  : <><i className="bi bi-check-lg me-1"></i>Сохранить</>
                }
              </button>
              <Link to="/admin/users" className="btn btn-outline-secondary">
                <i className="bi bi-x-lg me-1"></i>Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
