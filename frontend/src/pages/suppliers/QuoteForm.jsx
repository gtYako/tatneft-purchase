import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link, useSearchParams } from 'react-router-dom'
import axios from 'axios'

export default function QuoteForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isEdit = Boolean(pk)

  const [form, setForm] = useState({
    supplier: searchParams.get('supplier') || '',
    material: searchParams.get('material') || '',
    price: '',
    delivery_days: '',
    payment_terms: '',
    logistics_notes: '',
    quote_date: new Date().toISOString().split('T')[0],
    valid_until: '',
    notes: '',
  })
  const [materials, setMaterials] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    Promise.all([
      axios.get('/api/materials/all/'),
      axios.get('/api/suppliers/all/'),
    ]).then(([mRes, sRes]) => {
      setMaterials(mRes.data)
      setSuppliers(sRes.data)
    }).catch(() => {})

    if (!isEdit) { setLoading(false); return }
    axios.get(`/api/quotes/${pk}/`).then(r => {
      const d = r.data
      setForm({
        supplier: d.supplier, material: d.material,
        price: d.price, delivery_days: d.delivery_days,
        payment_terms: d.payment_terms || '',
        logistics_notes: d.logistics_notes || '',
        quote_date: d.quote_date,
        valid_until: d.valid_until || '',
        notes: d.notes || '',
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
        await axios.put(`/api/quotes/${pk}/`, form)
      } else {
        await axios.post('/api/quotes/', form)
      }
      const matId = form.material
      if (matId) navigate(`/catalog/${matId}`)
      else navigate('/quotes')
    } catch (err) {
      setErrors(err.response?.data || {})
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  const cancelTo = form.material ? `/catalog/${form.material}` : '/quotes'

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to={cancelTo} className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <h1 className="page-title mb-0">
          {isEdit ? 'Редактировать ценовое предложение' : 'Новое ценовое предложение (КП)'}
        </h1>
      </div>

      <div className="card" style={{ maxWidth: 680 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Материал <span className="text-danger">*</span></label>
                <select className={`form-select ${errors.material ? 'is-invalid' : ''}`}
                  value={form.material} required onChange={e => set('material', e.target.value)}>
                  <option value="">— выберите МТР —</option>
                  {materials.map(m => <option key={m.id} value={m.id}>{m.code} — {m.name?.substring(0, 50)}</option>)}
                </select>
                {errors.material && <div className="invalid-feedback">{errors.material}</div>}
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Поставщик <span className="text-danger">*</span></label>
                <select className={`form-select ${errors.supplier ? 'is-invalid' : ''}`}
                  value={form.supplier} required onChange={e => set('supplier', e.target.value)}>
                  <option value="">— выберите поставщика —</option>
                  {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
                {errors.supplier && <div className="invalid-feedback">{errors.supplier}</div>}
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold small">Цена, руб. <span className="text-danger">*</span></label>
                <input type="number" className={`form-control ${errors.price ? 'is-invalid' : ''}`}
                  min="0" step="0.01" value={form.price} required
                  onChange={e => set('price', e.target.value)} />
                {errors.price && <div className="invalid-feedback">{errors.price}</div>}
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold small">Срок поставки, дн. <span className="text-danger">*</span></label>
                <input type="number" className={`form-control ${errors.delivery_days ? 'is-invalid' : ''}`}
                  min="1" value={form.delivery_days} required
                  onChange={e => set('delivery_days', e.target.value)} />
                {errors.delivery_days && <div className="invalid-feedback">{errors.delivery_days}</div>}
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold small">Дата КП <span className="text-danger">*</span></label>
                <input type="date" className="form-control" value={form.quote_date} required
                  onChange={e => set('quote_date', e.target.value)} />
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Условия оплаты</label>
                <input className="form-control" value={form.payment_terms}
                  placeholder="По счёту 30 дней / Предоплата 50%..."
                  onChange={e => set('payment_terms', e.target.value)} />
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Действительно до</label>
                <input type="date" className="form-control" value={form.valid_until}
                  onChange={e => set('valid_until', e.target.value)} />
              </div>
              <div className="col-12">
                <label className="form-label fw-semibold small">Условия логистики</label>
                <input className="form-control" value={form.logistics_notes}
                  onChange={e => set('logistics_notes', e.target.value)} />
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
                  : <><i className="bi bi-check-lg me-1"></i>Сохранить КП</>
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
