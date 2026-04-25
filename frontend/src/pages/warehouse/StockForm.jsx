import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

export default function StockForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(pk)
  const [form, setForm] = useState({ material: '', location: '', qty_on_hand: '0', qty_reserved: '0' })
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    axios.get('/api/materials/all/').then(r => setMaterials(r.data)).catch(() => {})
    if (!isEdit) { setLoading(false); return }
    axios.get(`/api/warehouse/${pk}/`).then(r => {
      const d = r.data
      setForm({ material: d.material, location: d.location, qty_on_hand: d.qty_on_hand, qty_reserved: d.qty_reserved })
    }).finally(() => setLoading(false))
  }, [pk])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async e => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      if (isEdit) await axios.put(`/api/warehouse/${pk}/`, form)
      else await axios.post('/api/warehouse/', form)
      navigate('/warehouse')
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
        <Link to="/warehouse" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <h1 className="page-title mb-0">{isEdit ? 'Редактировать остаток' : 'Добавить складской остаток'}</h1>
      </div>
      <div className="card" style={{ maxWidth: 520 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Материал <span className="text-danger">*</span></label>
              <select className={`form-select ${errors.material ? 'is-invalid' : ''}`}
                value={form.material} required onChange={e => set('material', e.target.value)}>
                <option value="">— выберите —</option>
                {materials.map(m => <option key={m.id} value={m.id}>{m.code} — {m.name.substring(0, 50)}</option>)}
              </select>
              {errors.material && <div className="invalid-feedback">{errors.material}</div>}
            </div>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Место хранения <span className="text-danger">*</span></label>
              <input className={`form-control ${errors.location ? 'is-invalid' : ''}`}
                value={form.location} required onChange={e => set('location', e.target.value)}
                placeholder="Склад ГСМ-1 (площадка А)" />
              {errors.location && <div className="invalid-feedback">{errors.location}</div>}
            </div>
            <div className="row g-3 mb-4">
              <div className="col-6">
                <label className="form-label fw-semibold small">Количество на складе</label>
                <input type="number" className="form-control" min="0" step="0.001"
                  value={form.qty_on_hand} onChange={e => set('qty_on_hand', e.target.value)} />
              </div>
              <div className="col-6">
                <label className="form-label fw-semibold small">Зарезервировано</label>
                <input type="number" className="form-control" min="0" step="0.001"
                  value={form.qty_reserved} onChange={e => set('qty_reserved', e.target.value)} />
              </div>
            </div>
            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                  : <><i className="bi bi-check-lg me-1"></i>Сохранить</>
                }
              </button>
              <Link to="/warehouse" className="btn btn-outline-secondary">
                <i className="bi bi-x-lg me-1"></i>Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
