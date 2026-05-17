<script lang="ts" setup>
import type {LeadHint, Message} from '@/types/chat'
import {QUICK_QUESTIONS} from '@/utils/constants'
import ChatBubble from './ChatBubble.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  messages: Message[]
  sending: boolean
  loading: boolean
  leadHint: LeadHint | null
  transferred: boolean
  sessionId: number | null
}>()

const emit = defineEmits<{
  send: [text: string]
  transfer: []
}>()
</script>

<template>
  <section class="right-panel">
    <div class="chat-header">
      <div class="status-area">
        <el-tag size="small" type="success">● 在线</el-tag>
        <span class="status-text">智能客服</span>
      </div>
      <span class="session-hint">老乡鸡加盟咨询助手</span>
    </div>
    <div id="chat-messages" class="messages-area">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><span>⟳</span></el-icon>
        <p>正在连接...</p>
      </div>

      <template v-else>
        <div v-if="messages.length === 0" class="welcome-area">
          <div class="welcome-logo">🐔</div>
          <h2 class="welcome-title">欢迎咨询老乡鸡加盟</h2>
          <p class="welcome-desc">我是您的智能招商顾问，可以为您解答加盟费用、流程、区域、支持政策等问题。</p>
          <div class="welcome-questions">
            <el-button
                v-for="q in QUICK_QUESTIONS"
                :key="q"
                class="welcome-chip"
                round
                size="small"
                @click="emit('send', q)"
            >
              {{ q }}
            </el-button>
          </div>
        </div>

        <ChatBubble v-for="m in messages" :key="m.id" :message="m"/>

        <div v-if="leadHint?.should_ask" class="lead-hint-bar">
          <p class="lead-hint-text">{{ leadHint.message }}</p>
          <div class="lead-hint-chips">
            <el-button
                v-for="q in leadHint.suggested_questions"
                :key="q"
                class="hint-chip"
                round
                size="small"
                @click="emit('send', q)"
            >
              {{ q }}
            </el-button>
          </div>
        </div>
      </template>
    </div>
    <ChatInput :disabled="transferred" :sending="sending" @send="emit('send', $event)" @transfer="emit('transfer')"/>
  </section>
</template>

<style scoped>
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f9fb;
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.status-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.session-hint {
  font-size: 12px;
  color: #999;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  gap: 8px;
}

.loading-state .is-loading {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.welcome-area {
  text-align: center;
  padding: 60px 20px 0;
}

.welcome-logo {
  font-size: 56px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #888;
  margin: 0 0 24px;
  line-height: 1.6;
}

.welcome-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.welcome-chip {
  font-size: 13px;
}

.lead-hint-bar {
  background: linear-gradient(135deg, #fff8e1, #fff3cd);
  border: 1px solid #ffcc80;
  border-radius: 10px;
  padding: 12px 16px;
  margin-top: 8px;
}

.lead-hint-text {
  font-size: 13px;
  color: #8d6e00;
  margin: 0 0 8px;
}

.lead-hint-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hint-chip {
  font-size: 12px;
}
</style>
