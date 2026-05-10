<script setup lang="ts">
const steps = [
  { title: '提交申请', desc: '在线填写加盟申请表' },
  { title: '资质审核', desc: '审核资金与运营经验' },
  { title: '选址评估', desc: '上门评估商圈人流量' },
  { title: '签约开店', desc: '培训+装修+开业支持' },
]
</script>

<template>
  <div class="cooperation-process">
    <h3 class="section-title">合作流程</h3>
    <el-steps direction="vertical" :space="20" :active="-1">
      <el-step v-for="(s, i) in steps" :key="i" :title="s.title" :description="s.desc" />
    </el-steps>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}
</style>
