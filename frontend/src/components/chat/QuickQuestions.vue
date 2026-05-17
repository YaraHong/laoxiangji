<script lang="ts" setup>
import {QUICK_QUESTIONS} from '@/utils/constants'

const emit = defineEmits<{ 'select-question': [text: string] }>()
</script>

<template>
  <div class="quick-questions">
    <h3 class="section-title">快捷问题</h3>
    <div class="question-chips">
      <button
          v-for="q in QUICK_QUESTIONS"
          :key="q"
          class="chip"
          @click="emit('select-question', q)"
      >
        {{ q }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.question-chips {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chip {
  font-size: 12px;
  width: 100%;
  display: block;
  text-align: left;
  padding: 6px 14px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fff;
  color: #333;
  cursor: pointer;
  line-height: 1.5;
  font-family: inherit;
}

.chip:hover {
  color: #d4a853;
  border-color: #d4a853;
}
</style>
