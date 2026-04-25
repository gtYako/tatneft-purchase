import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const STATUS_LABELS = { draft:'Черновик', sent:'Отправлен поставщику', confirmed:'Подтверждён', delivered:'Доставлен', cancelled:'Отменён' }
const STATUS_COLORS = { draft:'secondary', sent:'primary', confirmed:'info', delivered:'success', cancelled:'danger' }
const NEXT_STATUSES = {
  draft: ['sent', 'cancelled'],
  sent: ['confirmed', 'cancelled'],
  confirmed: ['delivered', 'cancelled'],
  delivered: [],
  cancelled: [],
}

export default function OrderDetail() {
  const { pk } = useParams()
  const { user } = useAuth()
  const canManage = ['purchaser', 'admin'].includes(user?.role)
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [msg, setMsg] = useState('')

  const load = () => {
    axios.get(`/api/orders/${pk}/`).then(r => setOrder(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [pk])

  const updateStatus = async newStatus => {
    setUpdating(true)
    try {
      await axios.post(`/api/orders/${pk}/status/`, { status: newStatus })
      load()
      setMsg(`Статус изменён: ${STATUS_LABELS[newStatus]}`)
      setTimeout(() => setMsg(''), 3000)
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Ошибка')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!order) return <div className="alert alert-danger">Заказ не найден</div>

  const nextStatuses = NEXT_STATUSES[order.status] || []

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to="/orders" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <div>
          <h1 className="page-title mb-0">{order.order_number}</h1>
          <small className="text-muted">{order.supplier_name}</small>
        </div>
        {canManage && nextStatuses.length > 0 && (
          <div className="ms-auto d-flex gap-2">
            {nextStatuses.map(s => (
              <button key={s} className={`btn btn-sm btn-${STATUS_COLORS[s]}`}
                disabled={updating} onClick={() => updateStatus(s)}>
                <i className="bi bi-arrow-right-circle me-1"></i>
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        )}
      </div>

      {msg && <div className="alert alert-info py-2">{msg}</div>}

      <div className="row g-3">
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Информация о заказе</div>
            <div className="card-body">
              <table className="table table-sm table-borderless mb-0">
                <tbody>
                  {[
                    ['Статус', <span className={`badge bg-${STATUS_COLORS[order.status]}`}>{STATUS_LABELS[order.status]}</span>],
                    ['Поставщик', order.supplier_name],
                    ['Заявка', <Link to={`/requests/${order.request}`} className="text-decoration-none">{order.request_number}</Link>],
                    ['Дата заказа', order.order_date],
                    ['Ожидаемая доставка', order.expected_delivery_date || '—'],
                    ['Фактическая доставка', order.actual_delivery_date || '—'],
                    ['Сумма', `${Number(order.total_amount).toLocaleString('ru')} ₽`],
                    ['Создан', order.created_by_name || '—'],
                    ['Просрочен', order.is_overdue ? <span className="text-danger fw-semibold">Да</span> : 'Нет'],
                  ].map(([k, v]) => (
                    <tr key={k}>
                      <td className="text-muted small pe-3" style={{ whiteSpace: 'nowrap' }}>{k}</td>
                      <td className="fw-semibold small">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {order.notes && (
                <div className="border-top pt-2 mt-2 small text-muted">{order.notes}</div>
              )}
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Изменение статуса</div>
            <div className="card-body">
              <div className="d-flex flex-column gap-2">
                {Object.entries(STATUS_LABELS).map(([s, label]) => (
                  <div key={s} className={`p-2 rounded d-flex align-items-center gap-2 ${order.status === s ? 'bg-light border' : ''}`}>
                    <span className={`badge bg-${STATUS_COLORS[s]}`}>{label}</span>
                    {order.status === s && <span className="text-muted small">(текущий)</span>}
                    {canManage && nextStatuses.includes(s) && (
                      <button className={`btn btn-sm btn-outline-${STATUS_COLORS[s]} ms-auto`}
                        disabled={updating} onClick={() => updateStatus(s)}>
                        Перевести
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
