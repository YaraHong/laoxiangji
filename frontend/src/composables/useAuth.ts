// 认证模块已移除 - 知识库管理无需登录
export function useAuth() {
  return {
    token: { value: '' },
    user: { value: null },
    loggedIn: { value: false },
    role: { value: '' },
    initialized: { value: true },
    init: async () => true,
    login: async () => {},
    logout: async () => {},
  }
}
