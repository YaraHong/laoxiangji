<script setup lang="ts">
defineProps<{ page: string }>()
const emit = defineEmits<{ navigate: [page: 'chat' | 'knowledge'] }>()
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <div class="brand">
        <div class="logo">🐔</div>
        <span class="title">老乡鸡连锁加盟智能客服</span>
      </div>
      <nav class="nav-tabs">
        <button
          :class="['nav-btn', { active: page === 'chat' }]"
          @click="emit('navigate', 'chat')"
        >
          智能客服
        </button>
        <button
          :class="['nav-btn', { active: page === 'knowledge' }]"
          @click="emit('navigate', 'knowledge')"
        >
          知识库管理
        </button>
      </nav>
      <div class="user-area" />
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e6e1;
  display: flex;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}
.header-inner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo {
  font-size: 28px;
}
.title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
.nav-tabs {
  display: flex;
  gap: 4px;
  flex: 1;
  justify-content: center;
}
.nav-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-btn:hover {
  background: #f5f5f5;
  color: #333;
}
.nav-btn.active {
  background: #d4a853;
  color: #fff;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
}
</style>
