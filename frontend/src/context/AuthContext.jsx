import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // При открытии приложения сначала получаем CSRF-cookie, потом проверяем текущую Django-сессию.
    // Если /me/ вернул ошибку, пользователь считается неавторизованным.
    axios.get('/api/auth/csrf/').then(() =>
      axios.get('/api/auth/me/')
        .then(r => setUser(r.data))
        .catch(() => setUser(null))
        .finally(() => setLoading(false))
    ).catch(() => setLoading(false))
  }, [])

  const login = async (username, password) => {
    // CSRF нужен для POST-запроса логина, потому что backend использует cookie-сессию Django.
    await axios.get('/api/auth/csrf/')
    const r = await axios.post('/api/auth/login/', { username, password })
    setUser(r.data)
    return r.data
  }

  const logout = async () => {
    // Logout инвалидирует серверную сессию, после чего локально очищаем пользователя.
    await axios.post('/api/auth/logout/')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
