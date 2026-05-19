import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const ROLE_LABELS = {
  initiator: 'Инициатор',
  purchaser: 'Закупщик',
  analyst: 'Аналитик',
  manager: 'Руководитель',
  admin: 'Администратор',
}

const ROLE_COLORS = {
  initiator: 'secondary',
  purchaser: 'primary',
  analyst: 'info',
  manager: 'warning',
  admin: 'danger',
}

export default function UserList() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [actionId, setActionId] = useState(null)

  const load = () => {
    setLoading(true)
    axios.get('/api/admin/users/').then(r => {
      setUsers(r.data.results || r.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = users.filter(u =>
    // Поиск локальный: список пользователей уже загружен, поэтому не дергаем API на каждый символ.
    u.username?.toLowerCase().includes(search.toLowerCase()) ||
    u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    u.email?.toLowerCase().includes(search.toLowerCase())
  )

  const toggleActive = async (u) => {
    // Стоп-кнопка не удаляет пользователя, а только меняет is_active через PATCH.
    setActionId(u.id)
    try {
      await axios.patch(`/api/admin/users/${u.id}/`, { is_active: !u.is_active })
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка изменения статуса')
    } finally {
      setActionId(null)
    }
  }

  const deleteUser = async (u) => {
    // Удаление может превратиться в деактивацию на backend, если пользователь связан с документами.
    const label = u.full_name || u.username
    if (!window.confirm(`Убрать пользователя "${label}"?`)) return
    setActionId(u.id)
    try {
      await axios.delete(`/api/admin/users/${u.id}/`)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка удаления пользователя')
    } finally {
      setActionId(null)
    }
  }

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-people me-2"></i>Пользователи</h1>
        <Link to="/admin/users/new" className="btn btn-primary btn-sm">
          <i className="bi bi-plus-circle me-1"></i>Добавить
        </Link>
      </div>

      <div className="card mb-3">
        <div className="card-body py-2">
          <input
            className="form-control form-control-sm"
            style={{ maxWidth: 320 }}
            placeholder="Поиск по логину / ФИО / email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center py-5"><div className="spinner-border text-primary" /></div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Логин</th>
                  <th>ФИО</th>
                  <th>Email</th>
                  <th className="text-center">Роль</th>
                  <th className="text-center">Статус</th>
                  <th className="text-end pe-3">Действия</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr><td colSpan={6} className="text-center text-muted py-4">Нет пользователей</td></tr>
                )}
                {filtered.map(u => {
                  const isSelf = currentUser?.id === u.id
                  const busy = actionId === u.id

                  return (
                    <tr key={u.id}>
                      <td className="ps-3 fw-semibold small">{u.username}</td>
                      <td className="small">{u.full_name || '—'}</td>
                      <td className="small text-muted">{u.email || '—'}</td>
                      <td className="text-center">
                        <span className={`badge bg-${ROLE_COLORS[u.role] || 'secondary'}`}>
                          {ROLE_LABELS[u.role] || u.role}
                        </span>
                      </td>
                      <td className="text-center">
                        <span className={`badge bg-${u.is_active ? 'success' : 'secondary'}`}>
                          {u.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="text-end pe-3">
                        <div className="d-flex gap-2 justify-content-end">
                          <Link to={`/admin/users/${u.id}/edit`} className="btn btn-outline-primary btn-sm" title="Редактировать">
                            <i className="bi bi-pencil"></i>
                          </Link>
                          <button
                            className={`btn btn-sm btn-outline-${u.is_active ? 'warning' : 'success'}`}
                            onClick={() => toggleActive(u)}
                            disabled={busy || isSelf}
                            title={u.is_active ? 'Деактивировать' : 'Активировать'}
                          >
                            {busy ? (
                              <span className="spinner-border spinner-border-sm" />
                            ) : (
                              <i className={`bi bi-${u.is_active ? 'pause-circle' : 'play-circle'}`}></i>
                            )}
                          </button>
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => deleteUser(u)}
                            disabled={busy || isSelf}
                            title={isSelf ? 'Нельзя удалить себя' : 'Удалить'}
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
