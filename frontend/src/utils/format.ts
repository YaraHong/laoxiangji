/**
 * 格式化 ISO 日期时间为简短显示格式
 * 例如：2024-01-15T10:30:00 → 2024-01-15 10:30
 */
export function formatDateTime(isoString: string): string {
    return isoString.slice(0, 16).replace('T', ' ')
}
