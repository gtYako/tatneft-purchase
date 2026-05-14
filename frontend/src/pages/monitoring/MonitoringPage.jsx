import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'

// Вкладка сводки показывает состояние мониторинга и запускает быстрый парсинг.
function TabSummary({ summary, onRefresh }) {
  const [running, setRunning] = useState(false)
  const [msg, setMsg] = useState('')

  const handleRun = async () => {
    setRunning(true)
    setMsg('')
    try {
      const r = await axios.post('/api/monitoring/run-parsing/', { limit: 10 })
      setMsg(r.data.message)
      setTimeout(() => { onRefresh(); setMsg('') }, 4000)
    } catch {
      setMsg('Ошибка при запуске')
    } finally {
      setRunning(false)
    }
  }

  if (!summary) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  const stats = [
    { label: 'Источников парсинга', value: summary.parsing_sources_total, sub: `${summary.parsing_sources_active} активных`, icon: 'bi-rss', color: 'primary' },
    { label: 'Найдено товаров', value: summary.parsed_products_total, sub: `${summary.parsed_products_matched} сопоставлено`, icon: 'bi-box-seam', color: 'info' },
    { label: 'Кандидаты', value: summary.supplier_candidates_total, sub: `${summary.supplier_candidates_new} новых`, icon: 'bi-building-add', color: 'warning' },
  ]

  const lr = summary.last_run

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h5 className="mb-0">Состояние модуля</h5>
        <button className="btn btn-primary" onClick={handleRun} disabled={running}>
          {running
            ? <><span className="spinner-border spinner-border-sm me-2" />Запускается…</>
            : <><i className="bi bi-play-fill me-2"></i>Запустить парсинг</>}
        </button>
      </div>

      {msg && (
        <div className="alert alert-success py-2 mb-3">
          <i className="bi bi-check-circle me-2"></i>{msg}
          <span className="text-muted ms-2 small">Данные обновятся через ~30 сек</span>
        </div>
      )}

      <div className="row g-3 mb-4">
        {stats.map(s => (
          <div className="col-md-4" key={s.label}>
            <div className="card h-100">
              <div className="card-body">
                <div className="d-flex align-items-center gap-3">
                  <div className={`rounded-circle bg-${s.color} bg-opacity-10 d-flex align-items-center justify-content-center`}
                    style={{ width: 48, height: 48 }}>
                    <i className={`bi ${s.icon} text-${s.color} fs-5`}></i>
                  </div>
                  <div>
                    <div className="fs-3 fw-bold">{s.value}</div>
                    <div className="text-muted small">{s.label}</div>
                    <div className="text-muted" style={{ fontSize: '0.75rem' }}>{s.sub}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {lr && (
        <div className="card">
          <div className="card-header py-2">
            <i className="bi bi-clock-history me-2"></i>Последний запуск
          </div>
          <div className="card-body">
            <div className="row g-3 text-center">
              {[
                { label: 'Начало', value: new Date(lr.started_at).toLocaleString('ru') },
                { label: 'Статус', value: lr.status === 'done' ? '✅ Завершён' : lr.status === 'running' ? '🔄 Выполняется' : '❌ Ошибка' },
                { label: 'Источников', value: lr.sources_count ?? '—' },
                { label: 'Товаров найдено', value: lr.products_found ?? '—' },
                { label: 'КП создано', value: lr.quotes_created ?? '—' },
              ].map(c => (
                <div className="col" key={c.label}>
                  <div className="small text-muted">{c.label}</div>
                  <div className="fw-semibold">{c.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="alert alert-info mt-4 mb-0">
        <i className="bi bi-info-circle me-2"></i>
        <strong>Как работает парсинг:</strong> система скачивает прайс-листы активных источников,
        сопоставляет найденные товары с каталогом МТР по названию (нечёткое совпадение) и
        автоматически создаёт ценовые предложения для совпадений ≥ 35%.
        Новые сайты попадают в раздел «Кандидаты» для ручного одобрения.
      </div>
    </div>
  )
}

// Вкладка источников управляет сайтами поставщиков, которые участвуют в парсинге.
function TabSources() {
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    axios.get('/api/parsing-sources/', { params: { page_size: 50 } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const toggle = async (id) => {
    setToggling(id)
    await axios.post(`/api/parsing-sources/${id}/toggle/`).catch(() => {})
    setToggling(null)
    load()
  }

  return (
    <div>
      <h5 className="mb-3">Источники парсинга <span className="badge bg-secondary ms-1">{data.count}</span></h5>
      {loading ? (
        <div className="spinner-center"><div className="spinner-border text-primary" /></div>
      ) : data.results.length === 0 ? (
        <div className="text-center text-muted py-5"><i className="bi bi-rss display-4 d-block mb-2"></i>Источников нет</div>
      ) : (
        <div className="card">
          <div className="card-body p-0">
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Название</th>
                  <th>Поставщик</th>
                  <th>URL</th>
                  <th className="text-center">Тип</th>
                  <th className="text-center">Активен</th>
                  <th>Последний запуск</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map(s => (
                  <tr key={s.id}>
                    <td className="ps-3 fw-semibold small">{s.name}</td>
                    <td className="small">{s.supplier_name || '—'}</td>
                    <td className="small">
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-decoration-none text-truncate d-block" style={{ maxWidth: 200 }}>
                        {s.url}
                      </a>
                    </td>
                    <td className="text-center">
                      <span className="badge bg-secondary text-capitalize">{s.source_type}</span>
                    </td>
                    <td className="text-center">
                      <div className="form-check form-switch d-flex justify-content-center mb-0">
                        <input className="form-check-input" type="checkbox"
                          checked={s.is_active}
                          disabled={toggling === s.id}
                          onChange={() => toggle(s.id)} />
                      </div>
                    </td>
                    <td className="small text-muted">{s.last_parsed_at ? new Date(s.last_parsed_at).toLocaleString('ru') : '—'}</td>
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

// Вкладка найденных товаров показывает результаты парсинга и сопоставление с каталогом.
function TabProducts() {
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [matchedOnly, setMatchedOnly] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    axios.get('/api/parsed-products/', { params: { q, matched: matchedOnly, page_size: 50 } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }, [q, matchedOnly])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-3">
        <h5 className="mb-0">Найденные товары <span className="badge bg-secondary ms-1">{data.count}</span></h5>
        <div className="input-group" style={{ maxWidth: 260 }}>
          <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
          <input className="form-control border-start-0" placeholder="Поиск..." value={q} onChange={e => setQ(e.target.value)} />
        </div>
        <select className="form-select" style={{ width: 180 }} value={matchedOnly} onChange={e => setMatchedOnly(e.target.value)}>
          <option value="">Все товары</option>
          <option value="1">Только сопоставленные</option>
        </select>
      </div>

      {loading ? (
        <div className="spinner-center"><div className="spinner-border text-primary" /></div>
      ) : data.results.length === 0 ? (
        <div className="text-center text-muted py-5"><i className="bi bi-box-seam display-4 d-block mb-2"></i>Товаров не найдено</div>
      ) : (
        <div className="card">
          <div className="card-body p-0">
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Название на сайте поставщика</th>
                  <th>Поставщик</th>
                  <th className="text-end">Цена, ₽</th>
                  <th>Сопоставлен с МТР</th>
                  <th className="text-center">Совпадение</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map(p => (
                  <tr key={p.id}>
                    <td className="ps-3 small fw-semibold">{p.external_name}</td>
                    <td className="small">{p.supplier_name || '—'}</td>
                    <td className="text-end small">{p.price ? Number(p.price).toLocaleString('ru') : '—'}</td>
                    <td className="small">
                      {p.material_name
                        ? <span className="text-success"><i className="bi bi-check-circle me-1"></i>{p.material_name}</span>
                        : <span className="text-muted">—</span>}
                    </td>
                    <td className="text-center">
                      {p.match_score != null
                        ? <span className={`badge bg-${p.match_score >= 70 ? 'success' : p.match_score >= 35 ? 'warning' : 'secondary'}`}>
                            {p.match_score}%
                          </span>
                        : '—'}
                    </td>
                    <td className="small text-muted">{p.parsed_at ? new Date(p.parsed_at).toLocaleDateString('ru') : '—'}</td>
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

// Вкладка истории фиксирует последние запуски автоматического мониторинга.
function TabRuns() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    axios.get('/api/parsing-runs/')
      .then(r => setRuns(r.data)).finally(() => setLoading(false))
  }, [])

  const statusBadge = s =>
    s === 'done' ? <span className="badge bg-success">Завершён</span>
    : s === 'running' ? <span className="badge bg-primary">Выполняется</span>
    : <span className="badge bg-danger">Ошибка</span>

  return (
    <div>
      <h5 className="mb-3">История запусков</h5>
      {loading ? (
        <div className="spinner-center"><div className="spinner-border text-primary" /></div>
      ) : runs.length === 0 ? (
        <div className="text-center text-muted py-5"><i className="bi bi-clock-history display-4 d-block mb-2"></i>Запусков ещё не было</div>
      ) : (
        <div className="card">
          <div className="card-body p-0">
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Начало</th>
                  <th>Конец</th>
                  <th className="text-center">Статус</th>
                  <th className="text-center">Источников</th>
                  <th className="text-center">Товаров</th>
                  <th className="text-center">КП создано</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id}>
                    <td className="ps-3 small">{new Date(r.started_at).toLocaleString('ru')}</td>
                    <td className="small text-muted">{r.finished_at ? new Date(r.finished_at).toLocaleString('ru') : '—'}</td>
                    <td className="text-center">{statusBadge(r.status)}</td>
                    <td className="text-center small">{r.sources_count ?? '—'}</td>
                    <td className="text-center small">{r.products_found ?? '—'}</td>
                    <td className="text-center small">{r.quotes_created ?? '—'}</td>
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

// Вкладка кандидатов нужна для ручной модерации новых поставщиков.
function TabCandidates() {
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('new')
  const [acting, setActing] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    axios.get('/api/supplier-candidates/', { params: { status: statusFilter, page_size: 50 } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }, [statusFilter])

  useEffect(() => { load() }, [load])

  const approve = async (id) => {
    setActing(id)
    await axios.post(`/api/supplier-candidates/${id}/approve/`).catch(() => {})
    setActing(null)
    load()
  }

  const reject = async (id) => {
    setActing(id)
    await axios.post(`/api/supplier-candidates/${id}/reject/`).catch(() => {})
    setActing(null)
    load()
  }

  const filterBtns = [
    { value: 'new', label: 'Новые' },
    { value: 'approved', label: 'Одобренные' },
    { value: 'rejected', label: 'Отклонённые' },
    { value: '', label: 'Все' },
  ]

  return (
    <div>
      <div className="d-flex align-items-center gap-2 mb-3">
        <h5 className="mb-0">Кандидаты поставщиков <span className="badge bg-secondary ms-1">{data.count}</span></h5>
        <div className="btn-group ms-auto">
          {filterBtns.map(b => (
            <button key={b.value} className={`btn btn-sm btn-${statusFilter === b.value ? 'dark' : 'outline-secondary'}`}
              onClick={() => setStatusFilter(b.value)}>{b.label}</button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="spinner-center"><div className="spinner-border text-primary" /></div>
      ) : data.results.length === 0 ? (
        <div className="text-center text-muted py-5"><i className="bi bi-building-add display-4 d-block mb-2"></i>Кандидатов нет</div>
      ) : (
        <div className="card">
          <div className="card-body p-0">
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Название</th>
                  <th>Сайт</th>
                  <th className="text-center">Оценка</th>
                  <th>Категория</th>
                  <th className="text-center">Статус</th>
                  <th className="text-end pe-3">Действия</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map(c => (
                  <tr key={c.id}>
                    <td className="ps-3 fw-semibold small">{c.name}</td>
                    <td className="small">
                      <a href={c.website} target="_blank" rel="noreferrer" className="text-decoration-none text-truncate d-block" style={{ maxWidth: 200 }}>
                        {c.website}
                      </a>
                    </td>
                    <td className="text-center">
                      <span className={`badge bg-${c.supplier_score >= 70 ? 'success' : c.supplier_score >= 40 ? 'warning' : 'secondary'}`}>
                        {c.supplier_score}
                      </span>
                    </td>
                    <td className="small text-muted">{c.category_hint || '—'}</td>
                    <td className="text-center">
                      {c.status === 'new' && <span className="badge bg-warning text-dark">Новый</span>}
                      {c.status === 'approved' && <span className="badge bg-success">Одобрен</span>}
                      {c.status === 'rejected' && <span className="badge bg-secondary">Отклонён</span>}
                    </td>
                    <td className="text-end pe-3">
                      {c.status === 'new' && (
                        <>
                          <button className="btn btn-sm btn-success me-1" disabled={acting === c.id} onClick={() => approve(c.id)}>
                            <i className="bi bi-check-lg"></i> Одобрить
                          </button>
                          <button className="btn btn-sm btn-outline-danger" disabled={acting === c.id} onClick={() => reject(c.id)}>
                            <i className="bi bi-x-lg"></i>
                          </button>
                        </>
                      )}
                    </td>
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

// Основной экран объединяет вкладки мониторинга поставщиков.
export default function MonitoringPage() {
  const [tab, setTab] = useState('summary')
  const [summary, setSummary] = useState(null)

  const loadSummary = useCallback(() => {
    axios.get('/api/monitoring/summary/').then(r => setSummary(r.data))
  }, [])

  useEffect(() => { loadSummary() }, [loadSummary])

  const tabs = [
    { key: 'summary', label: 'Сводка', icon: 'bi-speedometer2' },
    { key: 'sources', label: 'Источники парсинга', icon: 'bi-rss' },
    { key: 'products', label: 'Найденные товары', icon: 'bi-box-seam' },
    { key: 'runs', label: 'Запуски', icon: 'bi-clock-history' },
    { key: 'candidates', label: 'Кандидаты поставщиков', icon: 'bi-building-add' },
  ]

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-radar me-2"></i>Мониторинг поставщиков</h1>

      <ul className="nav nav-tabs mb-4">
        {tabs.map(t => (
          <li className="nav-item" key={t.key}>
            <button className={`nav-link ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
              <i className={`bi ${t.icon} me-1`}></i>{t.label}
            </button>
          </li>
        ))}
      </ul>

      {tab === 'summary' && <TabSummary summary={summary} onRefresh={loadSummary} />}
      {tab === 'sources' && <TabSources />}
      {tab === 'products' && <TabProducts />}
      {tab === 'runs' && <TabRuns />}
      {tab === 'candidates' && <TabCandidates />}
    </div>
  )
}
