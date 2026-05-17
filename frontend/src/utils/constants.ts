/**
 * 快捷问题列表
 */
export const QUICK_QUESTIONS = [
  '加盟费用大概多少？',
  '加盟需要什么条件？',
  '回本周期多长？',
  '总部提供哪些支持？',
  '怎么走加盟流程？',
]

/**
 * 知识库文档类型
 */
export const DOC_TYPES = ['加盟政策', 'FAQ', '招商话术', '培训支持', '门店模型'] as const

/**
 * 文档状态映射
 */
export const DOC_STATUS_TAG_MAP: Record<string, string> = {
  pending: 'info',
  processing: 'warning',
  ready: 'success',
  error: 'danger',
}

export const DOC_STATUS_TEXT_MAP: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  ready: '已就绪',
  error: '失败',
}
