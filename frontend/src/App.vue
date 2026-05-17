<script lang="ts" setup>
import {computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'

const route = useRoute()
const router = useRouter()

const currentPage = computed(() => {
  const name = route.name as string
  if (name === 'knowledge') return 'knowledge'
  return 'chat'
})

function handleNavigate(page: string) {
  if (page === 'chat') router.push('/')
  else if (page === 'knowledge') router.push('/knowledge')
}
</script>

<template>
  <AppHeader :page="currentPage" @navigate="handleNavigate"/>
  <router-view/>
</template>
