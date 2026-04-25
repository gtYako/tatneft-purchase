import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import axios from 'axios'

export default function CategoryForm() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(pk)

  const [form, setForm] = useState({ name: '', description: '' })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!isEdit) return
    axios.get(`/api/categories/${pk}/`).then(r => {
      setForm({ name: r.data.name, description: r.data.description || '' })
    }).finally(() => setLoading(false))
  }, [pk])

  const handleSubmit = async e => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      if (isEdit) {
        await axios.put(`/api/categories/${pk}/`, form)
      } else {
        await axios.post('/api/categories/', form)
      }
      navigate('/categories')
    } catch (err) {
      setErrors(err.response?.data || { __all__: 'Ошибка сохранения' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to="/categories" className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left"></i>
        </Link>
        <h1 className="page-title mb-0">
          {isEdit ? 'Редактировать категорию' : 'Новая категория'}
        </h1>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <div className="card-body">
          {errors.__all__ && <div className="alert alert-danger">{errors.__all__}</div>}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold">
                Наименование <span className="text-danger">*</span>
              </label>
              <input className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                value={form.name} required autoFocus
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              {errors.name && <div className="invalid-feedback">{errors.name}</div>}
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold">Описание</label>
              <textarea className="form-control" rows={3}
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
            </div>

            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving
                  ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                  : <><i className="bi bi-check-lg me-1"></i>Сохранить</>
                }
              </button>
              <Link to="/categories" className="btn btn-outline-secondary">
                <i className="bi bi-x-lg me-1"></i>Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
