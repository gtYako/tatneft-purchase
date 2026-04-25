import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

export default function OrderForm() {
  const { requestPk } = useParams()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    request: requestPk,
    supplier: '',
    order_date: new Date().toISOString().split('T')[0],
    expected_delivery_date: '',
    total_amount: '',
    notes: '',
  })
  const [prefill, setPrefill] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    axios.get(`/api/orders/prefill/${requestPk}/`).then(r => {
      const d = r.data
      setPrefill(d)
      setForm(f => ({
        ...f,
        total_amount: d.total_amount || '',
        order_date: d.order_date,
        supplier: d.suppliers?.[0]?.id || '',
      }))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [requestPk])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async e => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      const r = await axios.post('/api/orders/', form)
      navigate(`/orders/${r.data.id}`)
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
        <Link to={`/requests/${requestPk}`} className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left"></i>
        </Link>
        <h1 className="page-title mb-0">Создание заказа поставщику</h1>
      </div>

      {prefill && (
        <div className="alert alert-info py-2 small mb-3">
          <i className="bi bi-info-circle me-1"></i>
          Заявка <strong>{prefill.request_number}</strong> · Расчётная сумма: <strong>{Number(prefill.total_amount).toLocaleString('ru')} ₽</strong>
        </div>
      )}

      <div className="card" style={{ maxWidth: 580 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Поставщик <span className="text-danger">*</span></label>
              <select className={`form-select ${errors.supplier ? 'is-invalid' : ''}`}
                value={form.supplier} required onChange={e => set('supplier', e.target.value)}>
                <option value="">— выберите поставщика —</option>
                {prefill?.suppliers?.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {errors.supplier && <div className="invalid-feedback">{errors.supplier}</div>}
              <div className="form-text">Поставщики из выбранных ценовых предложений</div>
            </div>

            <div className="row g-3 mb-3">
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Дата заказа <span className="text-danger">*</span></label>
                <input type="date" className="form-control" value={form.order_date} required
                  onChange={e => set('order_date', e.target.value)} />
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Ожидаемая дата доставки</label>
                <input type="date" className="form-control" value={form.expected_delivery_date}
                  onChange={e => set('expected_delivery_date', e.target.value)} />
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold small">Сумма заказа, руб. <span className="text-danger">*</span></label>
              <input type="number" className={`form-control ${errors.total_amount ? 'is-invalid' : ''}`}
                min="0" step="0.01" value={form.total_amount} required
                onChange={e => set('total_amount', e.target.value)} />
              {errors.total_amount && <div className="invalid-feedback">{errors.total_amount}</div>}
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold small">Примечания</label>
              <textarea className="form-control" rows={2} value={form.notes}
                onChange={e => set('notes', e.target.value)} />
            </div>

            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-warning fw-semibold" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Создание...</>
                  : <><i className="bi bi-cart-plus me-1"></i>Создать заказ</>
                }
              </button>
              <Link to={`/requests/${requestPk}`} className="btn btn-outline-secondary">
                <i className="bi bi-x-lg me-1"></i>Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
