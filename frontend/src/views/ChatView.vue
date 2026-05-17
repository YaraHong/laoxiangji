<script lang="ts" setup>
import {onMounted} from 'vue'
import {useChat} from '@/composables/useChat'
import AppContent from '@/components/layout/AppContent.vue'
import ChatPanelLeft from '@/components/chat/ChatPanelLeft.vue'
import ChatPanelRight from '@/components/chat/ChatPanelRight.vue'

const chat = useChat()

onMounted(() => {
  chat.initSession()
})

function handleTransfer() {
  chat.requestTransfer()
}
</script>

<template>
  <div class="chat-view">
    <AppContent>
      <ChatPanelLeft :session-id="chat.sessionId" @select-question="chat.send"/>
      <ChatPanelRight
          :lead-hint="chat.leadHint"
          :loading="chat.loading"
          :messages="chat.messages"
          :sending="chat.sending"
          :session-id="chat.sessionId"
          :transferred="chat.transferred"
          @send="chat.send"
          @transfer="handleTransfer"
      />
    </AppContent>
  </div>
</template>

<style scoped>
.chat-view {
  height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}
</style>
