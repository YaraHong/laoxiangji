import api from './index'
import type { FAQItem, KnowledgeDocument } from '@/types/knowledge'

export function uploadDocument(file: File, docType: string) {
  const form = new FormData()
  form.append('file', file)
  form.append('doc_type', docType)
  return api.post<KnowledgeDocument>('/api/knowledge/documents', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function listDocuments() {
  return api.get<KnowledgeDocument[]>('/api/knowledge/documents')
}

export function reEmbedDocument(documentId: number) {
  return api.post(`/api/knowledge/documents/${documentId}/embed`)
}

export function toggleDocument(documentId: number, enabled: boolean) {
  return api.put(`/api/knowledge/documents/${documentId}`, { enabled })
}

export function listFAQ() {
  return api.get<FAQItem[]>('/api/knowledge/faq')
}

export function createFAQ(data: { question: string; answer: string; category: string; priority: number }) {
  return api.post<FAQItem>('/api/knowledge/faq', data)
}
