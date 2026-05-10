<script setup lang="ts">
import type { Message } from '@/types/chat'
import CitationList from './CitationList.vue'

defineProps<{ message: Message }>()

function renderContent(content: string, role: string): string {
  if (role !== 'assistant') return escapeHtml(content)
  return content
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
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
</script>

<template>
  <div class="bubble-wrapper" :class="message.role">
    <div class="avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else-if="message.role === 'human'">👨‍💼</span>
      <span v-else-if="message.role === 'system'">📢</span>
      <span v-else>🐔</span>
    </div>
    <div class="bubble-body">
      <div class="bubble" :class="message.role">
        <div
          v-if="message.role === 'assistant'"
          class="content assistant-content"
          v-html="renderContent(message.content, message.role)"
        />
        <span v-if="message.role === 'assistant' && message.isStreaming" class="streaming-cursor">|</span>
        <div v-if="message.role !== 'assistant'" class="content" v-text="message.content" />
      </div>
      <div v-if="message.role === 'assistant'" class="bubble-footer">
        <CitationList :citations="message.citations" />
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
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.bubble.user {
  background: linear-gradient(135deg, #d4a853, #c9953a);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 6px rgba(212,168,83,0.3);
}
.bubble.human {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 6px rgba(64,158,255,0.3);
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
  50% { opacity: 0; }
}
</style>
