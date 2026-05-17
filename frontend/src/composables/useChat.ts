import {nextTick, reactive, ref} from 'vue'
import {createSession, getSession, sendMessageStream} from '@/api/chat'
import type {Citation, LeadHint, Message} from '@/types/chat'

const SESSION_KEY = 'lxg_session_id'

function loadSessionId(): number | null {
    const raw = localStorage.getItem(SESSION_KEY)
    if (raw) {
        const id = parseInt(raw, 10)
        if (!isNaN(id)) return id
    }
    return null
}

function saveSessionId(id: number) {
    localStorage.setItem(SESSION_KEY, String(id))
}

export function useChat() {
    const sessionId = ref<number | null>(loadSessionId())
    const sessionNo = ref('')
    const messages = ref<Message[]>([])
    const sending = ref(false)
    const leadHint = ref<LeadHint | null>(null)
    const transferred = ref(false)
    const error = ref<string | null>(null)
    const loading = ref(false)

    async function initSession() {
        loading.value = true
        const cachedId = loadSessionId()
        if (cachedId) {
            try {
                const {data} = await getSession(cachedId)
                sessionId.value = data.session.id
                sessionNo.value = data.session.session_no
                messages.value = data.messages.map((m) => ({
                    ...m,
                    message_type: m.message_type || 'text',
                }))
                loading.value = false
                return
            } catch {
                localStorage.removeItem(SESSION_KEY)
            }
        }
        loading.value = false
        const {data} = await createSession()
        sessionId.value = data.session_id
        sessionNo.value = data.session_no
        saveSessionId(data.session_id)
    }

    async function send(text: string) {
        if (!text.trim() || sending.value) return
        sending.value = true
        error.value = null

        if (!sessionId.value) {
            await initSession()
        }

        const tempId = -Date.now()
        const userMsg: Message = {
            id: tempId,
            session_id: sessionId.value!,
            role: 'user',
            content: text,
            message_type: 'text',
            citations: [],
            created_at: new Date().toISOString(),
        }
        messages.value.push(userMsg)
        await nextTick()
        scrollToBottom()

        const assistantTempId = tempId - 1
        const assistantMsg: Message = {
            id: assistantTempId,
            session_id: sessionId.value!,
            role: 'assistant',
            content: '',
            message_type: 'text',
            citations: [],
            created_at: new Date().toISOString(),
            isStreaming: true,
        }
        messages.value.push(assistantMsg)
        const msgIndex = messages.value.findIndex((m) => m.id === assistantTempId)

        try {
            await sendMessageStream(sessionId.value!, text, {
                onContent(fragment: string) {
                    if (msgIndex >= 0) {
                        messages.value[msgIndex].content += fragment
                        nextTick(() => scrollToBottom())
                    }
                },
                onCitations(cits: Citation[]) {
                    if (msgIndex >= 0) {
                        messages.value[msgIndex].citations = cits
                    }
                },
                onLeadHint(hint: LeadHint) {
                    leadHint.value = hint
                },
                onTransfer() {
                    transferred.value = true
                },
                onDone(messageId: number) {
                    if (msgIndex >= 0) {
                        messages.value[msgIndex].id = messageId
                        messages.value[msgIndex].isStreaming = false
                    }
                    sending.value = false
                    nextTick(() => scrollToBottom())
                },
                onError(errMsg: string) {
                    error.value = errMsg
                    messages.value = messages.value.filter(
                        (m) => m.id !== tempId && m.id !== assistantTempId,
                    )
                    sending.value = false
                },
            })
        } catch (e: unknown) {
            const errMsg = e instanceof Error ? e.message : '发送失败'
            error.value = errMsg
            messages.value = messages.value.filter(
                (m) => m.id !== tempId && m.id !== assistantTempId,
            )
            sending.value = false
        }
    }

    function requestTransfer() {
        const transferMsg: Message = {
            id: -Date.now(),
            session_id: sessionId.value || 0,
            role: 'system',
            content: '已为您转接人工客服，请稍候...',
            message_type: 'system',
            citations: [],
            created_at: new Date().toISOString(),
        }
        messages.value.push(transferMsg)
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            const el = document.getElementById('chat-messages')
            if (el) el.scrollTop = el.scrollHeight
        })
    }

    return reactive({
        sessionId,
        sessionNo,
        messages,
        sending,
        leadHint,
        transferred,
        error,
        loading,
        initSession,
        send,
        requestTransfer,
    })
}
