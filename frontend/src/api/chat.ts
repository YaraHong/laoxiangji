import api from './index'
import type {Citation, CreateSessionResult, LeadHint, SessionDetail} from '@/types/chat'

export function createSession(channel = 'web', visitorId?: string) {
    return api.post<CreateSessionResult>('/api/chat/sessions', {
        channel,
        visitor_id: visitorId || undefined,
    })
}

export function getSession(sessionId: number) {
    return api.get<SessionDetail>(`/api/chat/sessions/${sessionId}`)
}

export interface StreamCallbacks {
    onContent: (text: string) => void
    onCitations: (citations: Citation[]) => void
    onLeadHint: (leadHint: LeadHint) => void
    onTransfer: () => void
    onDone: (messageId: number) => void
    onError: (message: string) => void
}

export async function sendMessageStream(
    sessionId: number,
    content: string,
    callbacks: StreamCallbacks,
): Promise<void> {
    const response = await fetch(`/api/chat/sessions/${sessionId}/messages/stream`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content}),
    })

    if (!response.ok) {
        const errData = await response.json().catch(() => ({detail: '请求失败'}))
        callbacks.onError(errData.detail || `HTTP ${response.status}`)
        return
    }

    const reader = response.body?.getReader()
    if (!reader) {
        callbacks.onError('不支持流式响应')
        return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
        while (true) {
            const {done, value} = await reader.read()
            if (done) break

            buffer += decoder.decode(value, {stream: true})
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            let eventType = ''
            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.slice(7).trim()
                } else if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6))
                    switch (eventType) {
                        case 'content':
                            callbacks.onContent(data.text)
                            break
                        case 'citations':
                            callbacks.onCitations(data)
                            break
                        case 'lead_hint':
                            callbacks.onLeadHint(data)
                            break
                        case 'transfer':
                            callbacks.onTransfer()
                            break
                        case 'meta':
                            callbacks.onDone(data.message_id)
                            break
                        case 'error':
                            callbacks.onError(data.message)
                            break
                    }
                    eventType = ''
                }
            }
        }
    } catch (e: unknown) {
        const errMsg = e instanceof Error ? e.message : '流读取错误'
        callbacks.onError(errMsg)
    } finally {
        reader.cancel()
    }
}
