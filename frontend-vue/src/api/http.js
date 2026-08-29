import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 12000,
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  },
)
