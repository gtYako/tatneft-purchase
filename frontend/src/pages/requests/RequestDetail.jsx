import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const STATUS_LABELS = {
  draft:'Черновик', submitted:'На рассмотрении', approved:'Утверждена',
  rejected:'Отклонена', ordered:'Заказ размещён', completed:'Исполнена',
}
const STATUS_COLORS = {
  draft:'secondary', submitted:'primary', approved:'success',
  rejected:'danger', ordered:'info', completed:'dark',
}
const ORDER_STATUS = {
  draft:'secondary', sent:'primary', confirmed:'info', delivered:'success', cancelled:'danger',
}
const ORDER_STATUS_LABELS = {
  draft:'Черновик', sent:'Отправлен', confirmed:'Подтверждён', delivered:'Доставлен', cancelled:'Отменён',
}

export default function RequestDetail() {
  const { pk } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [req, setReq] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')
  const [newItem, setNewItem] = useState({ material: '', qty_requested: '' })
  const [materials, setMaterials] = useState([])
  const [rejectComment, setRejectComment] = useState('')
  const [showReject, setShowReject] = useState(false)
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState('success')

  const load = () => {
    axios.get(`/api/requests/${pk}/`).then(r => setReq(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    axios.get('/api/materials/all/').then(r => setMaterials(r.data)).catch(() => {})
  }, [pk])

  const notify = (text, type = 'success') => {
    setMsg(text); setMsgType(type)
    setTimeout(() => setMsg(''), 4000)
  }

  const doAction = async (url, body = {}, method = 'post') => {
    setActionLoading(url)
    try {
      await axios[method](url, body)
      load()
      notify('Выполнено успешно')
    } catch (err) {
      notify(err.response?.data?.detail || 'Ошибка', 'danger')
    } finally {
      setActionLoading('')
    }
  }

  const handleAddItem = async e => {
    e.preventDefault()
    setActionLoading('add-item')
    try {
      await axios.post(`/api/requests/${pk}/add-item/`, newItem)
      setNewItem({ material: '', qty_requested: '' })
      load()
      notify('Позиция добавлена')
    } catch (err) {
      notify(err.response?.data?.detail || 'Ошибка добавления', 'danger')
    } finally {
      setActionLoading('')
    }
  }

  const handleDeleteItem = async itemId => {
    if (!window.confirm('Удалить позицию?')) return
    await doAction(`/api/requests/${pk}/items/${itemId}/delete/`, {}, 'delete')
  }

  const handleReject = async e => {
    e.preventDefault()
    await doAction(`/api/requests/${pk}/reject/`, { rejection_comment: rejectComment })
    setShowReject(false)
    setRejectComment('')
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!req) return <div className="alert alert-danger">Заявка не найдена</div>

  const isDraft = req.status === 'draft'
  const canEdit = isDraft && (user?.role !== 'initiator' || req.requester === user?.id)
  const canSubmit = req.can_be_submitted
  const canApprove = req.can_be_approved && user?.can_approve
  const canApproveUser = ['manager', 'admin'].includes(user?.role)
  const canOrder = req.can_generate_order && ['purchaser', 'admin'].includes(user?.role)

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4 flex-wrap">
        <Link to="/requests" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <div>
          <h1 className="page-title mb-0">{req.request_number}</h1>
          <small className="text-muted">{req.department}</small>
        </div>
        <div className="ms-auto d-flex gap-2 flex-wrap">
          {canEdit && <Link to={`/requests/${pk}/edit`} className="btn btn-sm btn-outline-secondary"><i className="bi bi-pencil me-1"></i>Редактировать</Link>}
          {canSubmit && (
            <button className="btn btn-sm btn-primary" disabled={!!actionLoading}
              onClick={() => doAction(`/api/requests/${pk}/submit/`)}>
              <i className="bi bi-send me-1"></i>Подать на рассмотрение
            </button>
          )}
          {req.can_be_approved && canApproveUser && (
            <>
              <button className="btn btn-sm btn-success" disabled={!!actionLoading}
                onClick={() => doAction(`/api/requests/${pk}/approve/`)}>
                <i className="bi bi-check-circle me-1"></i>Утвердить
              </button>
              <button className="btn btn-sm btn-danger" disabled={!!actionLoading}
                onClick={() => setShowReject(s => !s)}>
                <i className="bi bi-x-circle me-1"></i>Отклонить
              </button>
            </>
          )}
          {req.status === 'rejected' && (
            <button className="btn btn-sm btn-outline-secondary" disabled={!!actionLoading}
              onClick={() => doAction(`/api/requests/${pk}/return-to-draft/`)}>
              <i className="bi bi-arrow-counterclockwise me-1"></i>В черновик
            </button>
          )}
          {canOrder && (
            <Link to={`/orders/new/${pk}`} className="btn btn-sm btn-warning">
              <i className="bi bi-cart-plus me-1"></i>Создать заказ
            </Link>
          )}
        </div>
      </div>

      {msg && <div className={`alert alert-${msgType} py-2`}>{msg}</div>}

      {showReject && (
        <div className="card mb-3 border-danger">
          <div className="card-body">
            <form onSubmit={handleReject}>
              <label className="form-label fw-semibold">Причина отклонения <span className="text-danger">*</span></label>
              <textarea className="form-control mb-2" rows={2} required value={rejectComment}
                onChange={e => setRejectComment(e.target.value)}
                placeholder="Укажите причину..." />
              <div className="d-flex gap-2">
                <button type="submit" className="btn btn-danger btn-sm">Отклонить</button>
                <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => setShowReject(false)}>Отмена</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Header info */}
      <div className="row g-3 mb-3">
        <div className="col-md-8">
          <div className="card h-100">
            <div className="card-body">
              <div className="row g-2">
                {[
                  ['Статус', <span className={`badge bg-${STATUS_COLORS[req.status]}`}>{STATUS_LABELS[req.status]}</span>],
                  ['Тип', <span className={`badge bg-${req.criticality === 'emergency' ? 'danger' : 'secondary'}`}>{req.criticality === 'emergency' ? 'Аварийная' : 'Плановая'}</span>],
                  ['Инициатор', req.requester_name],
                  ['Дата нужды', req.need_date],
                  ['Создана', new Date(req.created_at).toLocaleDateString('ru')],
                  ['Утверждена', req.approved_by_name ? `${req.approved_by_name} ${new Date(req.approved_at).toLocaleDateString('ru')}` : '—'],
                ].map(([k, v]) => (
                  <div className="col-6" key={k}>
                    <div className="text-muted small">{k}</div>
                    <div className="fw-semibold small">{v}</div>
                  </div>
                ))}
              </div>
              {req.justification && (
                <div className="mt-3 border-top pt-2 small">
                  <strong>Обоснование:</strong> {req.justification}
                </div>
              )}
              {req.rejection_comment && (
                <div className="alert alert-danger py-2 mt-2 small mb-0">
                  <strong>Причина отклонения:</strong> {req.rejection_comment}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body text-center d-flex flex-column justify-content-center">
              <div className="text-muted small mb-1">Итого к закупке</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1a237e' }}>
                {Number(req.total_target_amount).toLocaleString('ru')} ₽
              </div>
              <div className="text-muted small mt-2">Позиций: {req.items?.length || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Items */}
      <div className="card mb-3">
        <div className="card-header bg-white fw-semibold">
          <i className="bi bi-list-ul me-1 text-primary"></i> Позиции заявки
        </div>
        <div className="card-body p-0">
          {req.items?.length === 0 ? (
            <div className="text-center text-muted py-4 small">Позиций нет — добавьте материалы</div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Материал</th>
                  <th className="text-center">Запрошено</th>
                  <th className="text-center">На складе</th>
                  <th className="text-center">К закупке</th>
                  <th className="text-end">Цена, ₽</th>
                  <th className="text-end">Сумма, ₽</th>
                  <th>Поставщик</th>
                  {(isDraft || ['purchaser', 'admin', 'analyst', 'manager'].includes(user?.role)) && <th></th>}
                </tr>
              </thead>
              <tbody>
                {req.items.map(item => (
                  <tr key={item.id}>
                    <td className="ps-3 small">
                      <Link to={`/catalog/${item.material}`} className="text-decoration-none fw-semibold">
                        {item.material_code}
                      </Link>
                      <div className="text-muted" style={{ fontSize: '0.78rem' }}>
                        {item.material_name?.substring(0, 50)}{item.material_name?.length > 50 ? '…' : ''}
                      </div>
                    </td>
                    <td className="text-center small">{parseFloat(item.qty_requested).toFixed(1)} {item.material_unit}</td>
                    <td className="text-center small text-success">{parseFloat(item.qty_available_at_warehouse).toFixed(1)}</td>
                    <td className="text-center small fw-semibold">{parseFloat(item.qty_to_purchase).toFixed(1)}</td>
                    <td className="text-end small">
                      {item.target_price ? Number(item.target_price).toLocaleString('ru') : '—'}
                    </td>
                    <td className="text-end small">
                      {item.line_total ? Number(item.line_total).toLocaleString('ru') : '—'}
                    </td>
                    <td className="small">
                      {item.selected_quote_supplier
                        ? <span className="text-success"><i className="bi bi-check-circle me-1"></i>{item.selected_quote_supplier}</span>
                        : parseFloat(item.qty_to_purchase) > 0
                          ? <Link to={`/items/${item.id}/analyse`} className="btn btn-xs btn-outline-primary btn-sm py-0 px-1" style={{ fontSize: '0.75rem' }}>
                              Выбрать КП
                            </Link>
                          : <span className="text-muted small">Склад покрывает</span>
                      }
                    </td>
                    {isDraft && (
                      <td>
                        <button className="btn btn-sm btn-outline-danger py-0 px-1"
                          onClick={() => handleDeleteItem(item.id)}>
                          <i className="bi bi-trash" style={{ fontSize: '0.75rem' }}></i>
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

      {/* Add item form */}
      {isDraft && (
        <div className="card mb-3">
          <div className="card-header bg-white fw-semibold">
            <i className="bi bi-plus-circle me-1 text-success"></i> Добавить позицию
          </div>
          <div className="card-body">
            <form onSubmit={handleAddItem} className="row g-3 align-items-end">
              <div className="col-md-6">
                <label className="form-label small fw-semibold">Материал <span className="text-danger">*</span></label>
                <select className="form-select form-select-sm" required
                  value={newItem.material} onChange={e => setNewItem(f => ({ ...f, material: e.target.value }))}>
                  <option value="">— выберите МТР —</option>
                  {materials.map(m => <option key={m.id} value={m.id}>{m.code} — {m.name.substring(0, 60)}</option>)}
                </select>
              </div>
              <div className="col-md-3">
                <label className="form-label small fw-semibold">Количество <span className="text-danger">*</span></label>
                <input type="number" className="form-control form-control-sm" min="0.001" step="0.001" required
                  value={newItem.qty_requested}
                  onChange={e => setNewItem(f => ({ ...f, qty_requested: e.target.value }))} />
              </div>
              <div className="col-md-3">
                <button type="submit" className="btn btn-success btn-sm w-100" disabled={actionLoading === 'add-item'}>
                  {actionLoading === 'add-item'
                    ? <span className="spinner-border spinner-border-sm" />
                    : <><i className="bi bi-plus-lg me-1"></i>Добавить позицию</>
                  }
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Orders */}
      {req.orders?.length > 0 && (
        <div className="card">
          <div className="card-header bg-white fw-semibold">
            <i className="bi bi-cart3 me-1 text-warning"></i> Заказы поставщику
          </div>
          <div className="card-body p-0">
            <table className="table table-sm mb-0">
              <thead className="table-light">
                <tr><th className="ps-3">Номер заказа</th><th>Поставщик</th><th>Статус</th><th>Дата заказа</th><th className="text-end pe-3">Сумма, ₽</th></tr>
              </thead>
              <tbody>
                {req.orders.map(o => (
                  <tr key={o.id}>
                    <td className="ps-3">
                      <Link to={`/orders/${o.id}`} className="fw-semibold text-decoration-none">{o.order_number}</Link>
                    </td>
                    <td className="small">{o.supplier_name}</td>
                    <td><span className={`badge bg-${ORDER_STATUS[o.status]}`}>{ORDER_STATUS_LABELS[o.status]}</span></td>
                    <td className="small">{o.order_date}</td>
                    <td className="text-end pe-3 small">{Number(o.total_amount).toLocaleString('ru')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
