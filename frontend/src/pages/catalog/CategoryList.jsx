import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

export default function CategoryList() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)
  const [error, setError] = useState('')

  const canManage = ['admin', 'purchaser'].includes(user?.role)

  const load = (search = q) => {
    setLoading(true)
    axios.get('/api/categories/', { params: { q: search, page_size: 50 } })
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDelete = async id => {
    if (!window.confirm('Удалить категорию?')) return
    setError('')
    setDeleting(id)
    try {
      await axios.delete(`/api/categories/${id}/`)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка удаления')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-tags me-2"></i>Категории МТР</h1>
        {canManage && (
          <Link to="/categories/new" className="btn btn-primary">
            <i className="bi bi-plus-lg me-1"></i> Новая категория
          </Link>
        )}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="input-group">
            <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
            <input className="form-control border-start-0" placeholder="Поиск..."
              value={q} onChange={e => { setQ(e.target.value); load(e.target.value) }} />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center"><div className="spinner-border text-primary" /></div>
          ) : data.results.length === 0 ? (
            <div className="text-center text-muted py-5">
              <i className="bi bi-inbox display-4 d-block mb-2"></i>Категорий не найдено
            </div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Наименование</th>
                  <th>Описание</th>
                  <th className="text-center">Материалов</th>
                  {canManage && <th className="text-end pe-3">Действия</th>}
                </tr>
              </thead>
              <tbody>
                {data.results.map(cat => (
                  <tr key={cat.id}>
                    <td className="ps-3 fw-semibold">{cat.name}</td>
                    <td className="text-muted small">{cat.description || '—'}</td>
                    <td className="text-center">
                      <span className="badge bg-primary rounded-pill">{cat.materials_count}</span>
                    </td>
                    {canManage && (
                      <td className="text-end pe-3">
                        <Link to={`/categories/${cat.id}/edit`} className="btn btn-sm btn-outline-secondary me-1">
                          <i className="bi bi-pencil"></i>
                        </Link>
                        <button className="btn btn-sm btn-outline-danger"
                          disabled={deleting === cat.id || cat.materials_count > 0}
                          title={cat.materials_count > 0 ? 'Содержит материалы' : 'Удалить'}
                          onClick={() => handleDelete(cat.id)}>
                          <i className="bi bi-trash"></i>
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
