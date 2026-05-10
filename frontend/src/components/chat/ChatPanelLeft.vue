<script setup lang="ts">
import { ref } from 'vue'
import CooperationProcess from './CooperationProcess.vue'
import QuickQuestions from './QuickQuestions.vue'

defineProps<{ sessionId?: number | null }>()

const emit = defineEmits<{ 'select-question': [text: string] }>()

const collapsed = ref(false)
</script>

<template>
  <button class="toggle-btn" @click="collapsed = !collapsed">
    {{ collapsed ? '☰ 菜单' : '✕' }}
  </button>
  <aside class="left-panel" :class="{ collapsed }">
    <div class="brand-section">
      <div class="brand-logo">🐔</div>
      <h2 class="brand-name">老乡鸡</h2>
      <p class="brand-tagline">全国知名中式快餐品牌</p>
      <p class="brand-desc">全国 1200+ 门店 · 年服务 1 亿人次</p>
    </div>
    <el-divider />
    <CooperationProcess />
    <el-divider />
    <QuickQuestions @select-question="emit('select-question', $event)" />  </aside>
</template>

<style scoped>
.toggle-btn {
  display: none;
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
}
.left-panel {
  width: 320px;
  min-width: 280px;
  background: #fff;
  overflow: hidden;
  padding: 16px 16px;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 0;
  flex-shrink: 0;
  transition: transform 0.25s ease;
}
.left-panel.collapsed {
  display: none;
}
.brand-section {
  text-align: center;
  padding: 4px 0 8px;
}
.brand-logo {
  font-size: 36px;
  margin-bottom: 4px;
}
.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #d4a853;
  margin: 0 0 2px;
}
.brand-tagline {
  font-size: 12px;
  color: #666;
  margin: 0 0 2px;
}
.brand-desc {
  font-size: 11px;
  color: #999;
  margin: 0;
}
.left-panel :deep(.el-divider--horizontal) {
  margin: 8px 0;
}

@media (max-width: 900px) {
  .toggle-btn {
    display: block;
  }
  .left-panel {
    position: fixed;
    left: 0;
    top: 56px;
    bottom: 0;
    z-index: 20;
    width: 300px;
    box-shadow: 2px 0 12px rgba(0,0,0,0.1);
  }
  .left-panel.collapsed {
    display: none;
  }
}
</style>
