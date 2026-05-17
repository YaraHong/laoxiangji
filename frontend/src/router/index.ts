import {createRouter, createWebHistory} from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'chat',
            component: () => import('@/views/ChatView.vue'),
            meta: {title: '智能客服'},
        },
        {
            path: '/knowledge',
            name: 'knowledge',
            component: () => import('@/views/KnowledgeView.vue'),
            meta: {title: '知识库管理'},
        },
    ],
})

export default router
