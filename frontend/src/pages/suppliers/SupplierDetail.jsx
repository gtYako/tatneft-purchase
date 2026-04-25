import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const ratingColor = r => r >= 9 ? 'success' : r >= 7 ? 'info' : r >= 4 ? 'warning' : 'danger'

export default function SupplierDetail() {
  const { pk } = useParams()
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser'].includes(user?.role)
  const [supplier, setSupplier] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/suppliers/${pk}/`).then(r => setSupplier(r.data)).finally(() => setLoading(false))
  }, [pk])

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!supplier) return <div className="alert alert-danger">Поставщик не найден</div>

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to="/suppliers" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <div>
          <h1 className="page-title mb-0">{supplier.name}</h1>
          <small className="text-muted">ИНН: {supplier.inn}</small>
        </div>
        {canManage && (
          <div className="ms-auto d-flex gap-2">
            <Link to={`/suppliers/${pk}/edit`} className="btn btn-sm btn-outline-primary">
              <i className="bi bi-pencil me-1"></i> Редактировать
            </Link>
            <Link to={`/quotes/new?supplier=${pk}`} className="btn btn-sm btn-success">
              <i className="bi bi-plus-lg me-1"></i> Добавить КП
            </Link>
          </div>
        )}
      </div>

      <div className="row g-3 mb-3">
        <div className="col-md-5">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Реквизиты</div>
            <div className="card-body">
              <table className="table table-sm table-borderless mb-0">
                <tbody>
                  {[
                    ['Статус', <span className={`badge bg-${supplier.is_active ? 'success' : 'secondary'}`}>{supplier.is_active ? 'Активен' : 'Неактивен'}</span>],
                    ['Рейтинг', <span className={`badge bg-${ratingColor(supplier.rating)}`}>{supplier.rating}/10</span>],
                    ['Надёжность', `${supplier.delivery_reliability}%`],
                    ['Контакт', supplier.contact_person || '—'],
                    ['Телефон', supplier.phone || '—'],
                    ['Email', supplier.email || '—'],
                    ['Адрес', supplier.address || '—'],
                    ['КП', supplier.quotes_count],
                    ['Заказов', supplier.orders_count],
                  ].map(([k, v]) => (
                    <tr key={k}>
                      <td className="text-muted small pe-3">{k}</td>
                      <td className="fw-semibold small">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {supplier.notes && (
                <div className="border-top pt-2 mt-2 small text-muted">{supplier.notes}</div>
              )}
            </div>
          </div>
        </div>

        <div className="col-md-7">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Последние ценовые предложения</div>
            <div className="card-body p-0">
              {supplier.quotes?.length === 0 ? (
                <div className="text-center text-muted py-4 small">КП нет</div>
              ) : (
                <table className="table table-sm table-hover mb-0">
                  <thead className="table-light">
                    <tr><th className="ps-3">Материал</th><th className="text-end">Цена, ₽</th><th className="text-center">Срок</th><th>Дата</th></tr>
                  </thead>
                  <tbody>
                    {supplier.quotes?.slice(0, 10).map(q => (
                      <tr key={q.id}>
                        <td className="ps-3 small">{q.material_code} — {q.material_name?.substring(0, 35)}</td>
                        <td className="text-end small">{Number(q.price).toLocaleString('ru')}</td>
                        <td className="text-center small">{q.delivery_days} дн.</td>
                        <td className="small">{q.quote_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>

      {supplier.orders?.length > 0 && (
        <div className="card">
          <div className="card-header bg-white fw-semibold">Заказы</div>
          <div className="card-body p-0">
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr><th className="ps-3">Номер заказа</th><th>Заявка</th><th>Статус</th><th>Дата</th><th className="text-end pe-3">Сумма, ₽</th></tr>
              </thead>
              <tbody>
                {supplier.orders.map(o => (
                  <tr key={o.id}>
                    <td className="ps-3"><Link to={`/orders/${o.id}`} className="fw-semibold text-decoration-none">{o.order_number}</Link></td>
                    <td className="small">{o.request_number}</td>
                    <td><span className={`badge bg-${o.status_color}`}>{o.status}</span></td>
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
