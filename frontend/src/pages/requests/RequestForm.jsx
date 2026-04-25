import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

export default function RequestForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isEdit = Boolean(pk)

  const [form, setForm] = useState({
    department: user?.department || '',
    need_date: '',
    criticality: 'planned',
    justification: '',
  })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!isEdit) return
    axios.get(`/api/requests/${pk}/`).then(r => {
      const d = r.data
      setForm({
        department: d.department,
        need_date: d.need_date,
        criticality: d.criticality,
        justification: d.justification || '',
      })
    }).finally(() => setLoading(false))
  }, [pk])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async e => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      if (isEdit) {
        await axios.put(`/api/requests/${pk}/`, form)
        navigate(`/requests/${pk}`)
      } else {
        const r = await axios.post('/api/requests/', form)
        navigate(`/requests/${r.data.id}`)
      }
    } catch (err) {
      setErrors(err.response?.data || {})
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  const cancelTo = isEdit ? `/requests/${pk}` : '/requests'

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to={cancelTo} className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <h1 className="page-title mb-0">
          {isEdit ? 'Редактировать заявку' : 'Новая заявка на закупку'}
        </h1>
      </div>

      <div className="card" style={{ maxWidth: 600 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Подразделение <span className="text-danger">*</span></label>
              <input className={`form-control ${errors.department ? 'is-invalid' : ''}`}
                value={form.department} required
                onChange={e => set('department', e.target.value)}
                placeholder="Буровой цех №3" />
              {errors.department && <div className="invalid-feedback">{errors.department}</div>}
            </div>

            <div className="row g-3 mb-3">
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Дата необходимости <span className="text-danger">*</span></label>
                <input type="date" className={`form-control ${errors.need_date ? 'is-invalid' : ''}`}
                  value={form.need_date} required
                  onChange={e => set('need_date', e.target.value)} />
                {errors.need_date && <div className="invalid-feedback">{errors.need_date}</div>}
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Тип заявки</label>
                <select className="form-select" value={form.criticality}
                  onChange={e => set('criticality', e.target.value)}>
                  <option value="planned">Плановая</option>
                  <option value="emergency">Аварийная</option>
                </select>
              </div>
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold small">Обоснование потребности</label>
              <textarea className="form-control" rows={4} value={form.justification}
                placeholder="Укажите причину и цель закупки..."
                onChange={e => set('justification', e.target.value)} />
            </div>

            <div className="alert alert-info py-2 small mb-4">
              <i className="bi bi-info-circle me-1"></i>
              После создания заявки добавьте позиции МТР и подайте на рассмотрение.
            </div>

            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                  : <><i className="bi bi-check-lg me-1"></i>{isEdit ? 'Сохранить изменения' : 'Создать заявку'}</>
                }
              </button>
              <Link to={cancelTo} className="btn btn-outline-secondary">
                <i className="bi bi-x-lg me-1"></i>Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
