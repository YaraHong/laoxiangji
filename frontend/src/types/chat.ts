export interface Citation {
  title: string
  url?: string | null
  snippet?: string | null
}

export interface LeadHint {
  should_ask: boolean
  message: string
  suggested_questions: string[]
}

export interface Message {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system' | 'human'
  content: string
  message_type: string
  confidence?: number | null
  citations: Citation[]
  created_at: string
  isStreaming?: boolean
}

export interface SessionInfo {
  id: number
  session_no: string
  channel: string
  visitor_id?: string | null
  status: string
  summary?: string | null
  last_message_at?: string | null
  created_at: string
  updated_at: string
}

export interface SessionDetail {
  session: SessionInfo
  messages: Message[]
}

export interface CreateSessionResult {
  session_id: number
  session_no: string
}
