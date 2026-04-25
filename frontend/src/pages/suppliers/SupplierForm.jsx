import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

export default function SupplierForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(pk)
  const [form, setForm] = useState({
    name: '', inn: '', contact_person: '', phone: '', email: '',
    address: '', rating: '7.0', delivery_reliability: '90.0',
    is_active: true, notes: '',
  })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!isEdit) return
    axios.get(`/api/suppliers/${pk}/`).then(r => {
      const d = r.data
      setForm({
        name: d.name, inn: d.inn, contact_person: d.contact_person || '',
        phone: d.phone || '', email: d.email || '', address: d.address || '',
        rating: d.rating, delivery_reliability: d.delivery_reliability,
        is_active: d.is_active, notes: d.notes || '',
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
        await axios.put(`/api/suppliers/${pk}/`, form)
        navigate(`/suppliers/${pk}`)
      } else {
        const r = await axios.post('/api/suppliers/', form)
        navigate(`/suppliers/${r.data.id}`)
      }
    } catch (err) {
      setErrors(err.response?.data || {})
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  const cancelTo = isEdit ? `/suppliers/${pk}` : '/suppliers'

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to={cancelTo} className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <h1 className="page-title mb-0">{isEdit ? 'Редактировать поставщика' : 'Новый поставщик'}</h1>
      </div>
      <div className="card" style={{ maxWidth: 700 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row g-3">
              <div className="col-md-8">
                <label className="form-label fw-semibold small">Наименование <span className="text-danger">*</span></label>
                <input className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                  value={form.name} required onChange={e => set('name', e.target.value)} />
                {errors.name && <div className="invalid-feedback">{errors.name}</div>}
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold small">ИНН <span className="text-danger">*</span></label>
                <input className={`form-control ${errors.inn ? 'is-invalid' : ''}`}
                  value={form.inn} required onChange={e => set('inn', e.target.value)} />
                {errors.inn && <div className="invalid-feedback">{errors.inn}</div>}
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Контактное лицо</label>
                <input className="form-control" value={form.contact_person} onChange={e => set('contact_person', e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Телефон</label>
                <input className="form-control" value={form.phone} onChange={e => set('phone', e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Email</label>
                <input type="email" className="form-control" value={form.email} onChange={e => set('email', e.target.value)} />
              </div>
              <div className="col-12">
                <label className="form-label fw-semibold small">Адрес</label>
                <input className="form-control" value={form.address} onChange={e => set('address', e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Рейтинг (1–10)</label>
                <input type="number" className="form-control" min="1" max="10" step="0.1"
                  value={form.rating} onChange={e => set('rating', e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Надёжность поставок, %</label>
                <input type="number" className="form-control" min="0" max="100" step="0.1"
                  value={form.delivery_reliability} onChange={e => set('delivery_reliability', e.target.value)} />
              </div>
              <div className="col-md-6 d-flex align-items-end pb-1">
                <div className="form-check">
                  <input className="form-check-input" type="checkbox" id="isActive"
                    checked={form.is_active} onChange={e => set('is_active', e.target.checked)} />
                  <label className="form-check-label fw-semibold small" htmlFor="isActive">Активен</label>
                </div>
              </div>
              <div className="col-12">
                <label className="form-label fw-semibold small">Примечания</label>
                <textarea className="form-control" rows={2} value={form.notes}
                  onChange={e => set('notes', e.target.value)} />
              </div>
            </div>

            <div className="d-flex gap-2 mt-4">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                  : <><i className="bi bi-check-lg me-1"></i>Сохранить</>
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
