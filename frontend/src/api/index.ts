import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    // 标准响应格式：{ code, message, data }
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) {
        response.data = body.data
      } else {
        ElMessage.error(body.message || '请求失败')
        return Promise.reject(new Error(body.message || '请求失败'))
      }
    }
    return response
  },
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default api
