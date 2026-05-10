export interface KnowledgeDocument {
  id: number
  title: string
  file_name: string
  doc_type: string
  version: string
  status: string
  chunk_count: number
  enabled: boolean
  uploaded_at: string
}

export interface FAQItem {
  id: number
  question: string
  answer: string
  category: string
  priority: number
  enabled: boolean
  created_at: string
}
