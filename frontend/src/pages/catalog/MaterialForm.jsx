import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

const CRITICALITIES = [
  { value: 'low', label: 'Низкая' },
  { value: 'medium', label: 'Средняя' },
  { value: 'high', label: 'Высокая' },
  { value: 'critical', label: 'Критическая' },
]

export default function MaterialForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(pk)

  const [form, setForm] = useState({
    code: '', name: '', category: '', unit: '', gost: '',
    technical_specs: '', criticality: 'medium', min_stock_level: '0',
  })
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    axios.get('/api/categories/all/').then(r => setCats(r.data)).catch(() => {})
    if (!isEdit) { setLoading(false); return }
    axios.get(`/api/materials/${pk}/`).then(r => {
      const d = r.data
      setForm({
        code: d.code, name: d.name, category: d.category,
        unit: d.unit, gost: d.gost || '', technical_specs: d.technical_specs || '',
        criticality: d.criticality, min_stock_level: d.min_stock_level,
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
        await axios.put(`/api/materials/${pk}/`, form)
        navigate(`/catalog/${pk}`)
      } else {
        const r = await axios.post('/api/materials/', form)
        navigate(`/catalog/${r.data.id}`)
      }
    } catch (err) {
      setErrors(err.response?.data || {})
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  const cancelTo = isEdit ? `/catalog/${pk}` : '/catalog'

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to={cancelTo} className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <h1 className="page-title mb-0">{isEdit ? 'Редактировать материал' : 'Новый материал / оборудование'}</h1>
      </div>

      <div className="card" style={{ maxWidth: 720 }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row g-3 mb-3">
              <div className="col-md-4">
                <label className="form-label fw-semibold small">Код МТР <span className="text-danger">*</span></label>
                <input className={`form-control ${errors.code ? 'is-invalid' : ''}`}
                  value={form.code} required onChange={e => set('code', e.target.value)} />
                {errors.code && <div className="invalid-feedback">{errors.code}</div>}
              </div>
              <div className="col-md-8">
                <label className="form-label fw-semibold small">Наименование <span className="text-danger">*</span></label>
                <input className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                  value={form.name} required onChange={e => set('name', e.target.value)} />
                {errors.name && <div className="invalid-feedback">{errors.name}</div>}
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">Категория <span className="text-danger">*</span></label>
                <select className={`form-select ${errors.category ? 'is-invalid' : ''}`}
                  value={form.category} required onChange={e => set('category', e.target.value)}>
                  <option value="">— выберите —</option>
                  {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                {errors.category && <div className="invalid-feedback">{errors.category}</div>}
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Ед. изм. <span className="text-danger">*</span></label>
                <input className="form-control" value={form.unit} required
                  onChange={e => set('unit', e.target.value)} placeholder="шт, м, кг..." />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Критичность</label>
                <select className="form-select" value={form.criticality}
                  onChange={e => set('criticality', e.target.value)}>
                  {CRITICALITIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-semibold small">ГОСТ / ТУ</label>
                <input className="form-control" value={form.gost}
                  onChange={e => set('gost', e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label fw-semibold small">Минимальный запас</label>
                <input type="number" className="form-control" min="0" step="0.001"
                  value={form.min_stock_level}
                  onChange={e => set('min_stock_level', e.target.value)} />
              </div>
              <div className="col-12">
                <label className="form-label fw-semibold small">Технические характеристики</label>
                <textarea className="form-control" rows={3} value={form.technical_specs}
                  onChange={e => set('technical_specs', e.target.value)} />
              </div>
            </div>

            <div className="d-flex gap-2">
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
