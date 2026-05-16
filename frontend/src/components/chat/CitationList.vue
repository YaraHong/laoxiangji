<script setup lang="ts">
import type {Citation} from '@/types/chat'

defineProps<{ citations: Citation[] }>()
</script>

<template>
  <el-collapse v-if="citations.length > 0" class="citation-collapse">
    <el-collapse-item :title="`参考来源 (${citations.length})`">
      <div v-for="(c, i) in citations" :key="i" class="citation-item">
        <div class="citation-title">{{ c.title }}</div>
        <div v-if="c.snippet" class="citation-snippet">{{ c.snippet }}</div>
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.citation-collapse {
  margin-top: 8px;
  font-size: 12px;
}
.citation-item {
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}
.citation-item:last-child {
  border-bottom: none;
}
.citation-title {
  color: #666;
  font-weight: 500;
}
.citation-snippet {
  color: #999;
  margin-top: 2px;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
