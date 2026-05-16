<script setup lang="ts">
import {ref} from 'vue'
import {Promotion} from '@element-plus/icons-vue'

const emit = defineEmits<{
  send: [text: string]
  transfer: []
}>()

const input = ref('')
const props = defineProps<{ sending: boolean; disabled?: boolean }>()

function onSend() {
  const text = input.value.trim()
  if (!text) return
  emit('send', text)
  input.value = ''
}
</script>

<template>
  <div class="chat-input-area">
    <el-input
      v-model="input"
      type="textarea"
      :rows="2"
      placeholder="输入您的问题，Enter 发送，Shift+Enter 换行"
      resize="none"
      :disabled="sending || props.disabled"
      @keydown.enter.exact.prevent="onSend"
    />
    <div class="input-actions">
      <el-button type="warning" :icon="Promotion" size="small" :disabled="props.disabled" @click="emit('transfer')">
        转人工
      </el-button>
      <el-button type="primary" size="small" :loading="sending" :disabled="props.disabled" @click="onSend">
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
}
.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
:deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
}
</style>
