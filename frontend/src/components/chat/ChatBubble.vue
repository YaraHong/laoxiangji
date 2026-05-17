<script lang="ts" setup>
import type {Message} from '@/types/chat'
import CitationList from './CitationList.vue'

defineProps<{ message: Message }>()

function isSeparatorCell(cell: string): boolean {
  return /^:?-{3,}:?$/.test(cell)
}

function parseTableRow(line: string): string[] {
  return line
      .trim()
      .replace(/^\||\|$/g, '')
      .split('|')
      .map(c => c.trim())
}

function getAlign(cell: string): string {
  if (cell.startsWith(':') && cell.endsWith(':')) return 'center'
  if (cell.endsWith(':')) return 'right'
  return 'left'
}

function convertMarkdownTable(block: string): string {
  const lines = block.trim().split('\n')
  if (lines.length < 2) return block

  const headerCells = parseTableRow(lines[0])
  const sepCells = parseTableRow(lines[1])
  if (!sepCells.every(isSeparatorCell)) return block

  const colCount = headerCells.length
  const aligns = sepCells.map(getAlign)

  // 拆分粘在一起的行（大模型常在部分行之间遗漏 || 边界）
  const rawRows = lines.slice(2).flatMap(line => {
    const cells = parseTableRow(line)
    if (cells.length <= colCount) return [cells]
    const groups: string[][] = []
    for (let i = 0; i < cells.length; i += colCount) {
      groups.push(cells.slice(i, i + colCount))
    }
    return groups
  })
  const dataRows = rawRows.filter(r => !r.every(isSeparatorCell))

  const thStyle = (a: string) => a !== 'left' ? ` style="text-align:${a}"` : ''
  const tdStyle = (a: string) => a !== 'left' ? ` style="text-align:${a}"` : ''

  let html = '<div class="table-wrap"><table><thead><tr>'
  headerCells.forEach((c, i) => {
    html += `<th${thStyle(aligns[i])}>${escapeHtml(c)}</th>`
  })
  html += '</tr></thead><tbody>'
  dataRows.forEach(row => {
    html += '<tr>'
    row.forEach((c, i) => {
      html += `<td${tdStyle(aligns[i] || 'left')}>${escapeHtml(c)}</td>`
    })
    html += '</tr>'
  })
  html += '</tbody></table></div>'
  return html
}

function normalizeInlineTables(text: string): string {
  return text.replace(/[^\n|]*\|.+\|[^\n|]*/g, (segment) => {
    if (!segment.includes('||')) return segment
    const firstPipe = segment.indexOf('|')
    const lastPipe = segment.lastIndexOf('|')
    const prefix = segment.slice(0, firstPipe)
    const suffix = segment.slice(lastPipe + 1)
    const table = segment.slice(firstPipe, lastPipe + 1)

    // 按 || 拆分各行（保留完整管道）
    let tableLines = table.replace(/\|\|/g, '|\n|')

    // 修复粘在一起的行：分隔符 --- 后面紧挨数据列时切开
    // |------|------|------|加盟费 → |------|------|------|\n|加盟费
    tableLines = tableLines.replace(/(:\?-{3,}:?\|)([^\s\-|])/g, '$1\n|$2')

    const normalized = tableLines
    return (prefix ? prefix + '\n' : '') + normalized + (suffix ? '\n' + suffix : '')
  })
}

function renderContent(content: string, role: string): string {
  if (role !== 'assistant') return escapeHtml(content)

  content = normalizeInlineTables(content)

  const tablePlaceholders: string[] = []

  content = content.replace(/(?:^\|.+?\|[ \t]*$\n?)+/gm, (match) => {
    const idx = tablePlaceholders.length
    tablePlaceholders.push(convertMarkdownTable(match))
    return `%%TBL_${idx}%%`
  })

  let html = content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^### (.+)/gm, '<h3>$1</h3>')
      .replace(/^## (.+)/gm, '<h2>$1</h2>')
      .replace(/^# (.+)/gm, '<h1>$1</h1>')
      .replace(/^- (.+)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n/g, '<br>')

  tablePlaceholders.forEach((th, i) => {
    html = html.replace(`%%TBL_${i}%%`, th)
  })

  return html
}

function escapeHtml(text: string): string {
  return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
}
</script>

<template>
  <div :class="message.role" class="bubble-wrapper">
    <div class="avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else-if="message.role === 'human'">👨‍💼</span>
      <span v-else-if="message.role === 'system'">📢</span>
      <span v-else>🐔</span>
    </div>
    <div class="bubble-body">
      <div :class="message.role" class="bubble">
        <div
            v-if="message.role === 'assistant'"
            class="content assistant-content"
            v-html="renderContent(message.content, message.role)"
        />
        <span v-if="message.role === 'assistant' && message.isStreaming" class="streaming-cursor">|</span>
        <div v-if="message.role !== 'assistant'" class="content" v-text="message.content"/>
      </div>
      <div v-if="message.role === 'assistant'" class="bubble-footer">
        <CitationList :citations="message.citations"/>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bubble-wrapper {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-start;
}

.bubble-wrapper.user {
  flex-direction: row-reverse;
}

.bubble-wrapper.human {
  flex-direction: row-reverse;
}

.bubble-wrapper.system {
  justify-content: center;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.bubble-body {
  max-width: 75%;
  min-width: 0;
}

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.bubble.assistant {
  background: #fff;
  border-bottom-left-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.bubble.user {
  background: linear-gradient(135deg, #d4a853, #c9953a);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 6px rgba(212, 168, 83, 0.3);
}

.bubble.human {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
}

.bubble.system {
  background: #f5f7fa;
  color: #999;
  text-align: center;
  font-size: 13px;
  border-radius: 8px;
}

.content {
  white-space: pre-wrap;
}

.table-wrap {
  overflow-x: auto;
  margin: 8px 0;
}

.assistant-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
}

.assistant-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  white-space: nowrap;
}

.assistant-content :deep(td) {
  border: 1px solid #e5e5e5;
  padding: 5px 10px;
}

.assistant-content :deep(tr:nth-child(even) td) {
  background: #fafafa;
}

.assistant-content {
  overflow-x: auto;
}

.assistant-content :deep(h1),
.assistant-content :deep(h2),
.assistant-content :deep(h3) {
  margin: 4px 0;
  font-size: 15px;
  font-weight: 600;
}

.assistant-content :deep(strong) {
  font-weight: 600;
  color: #333;
}

.assistant-content :deep(ul) {
  margin: 4px 0;
  padding-left: 18px;
}

.assistant-content :deep(li) {
  margin: 2px 0;
}

.bubble-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.streaming-cursor {
  display: inline-block;
  color: #d4a853;
  font-weight: bold;
  font-size: 16px;
  line-height: 1;
  animation: blink 0.7s step-end infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
