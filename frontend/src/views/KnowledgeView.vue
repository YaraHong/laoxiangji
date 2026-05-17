<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {ElMessage} from 'element-plus'
import {UploadFilled} from '@element-plus/icons-vue'
import {createFAQ, listDocuments, listFAQ, reEmbedDocument, toggleDocument, uploadDocument,} from '@/api/knowledge'
import type {FAQItem, KnowledgeDocument} from '@/types/knowledge'

const activeTab = ref('documents')
const documents = ref<KnowledgeDocument[]>([])
const faqs = ref<FAQItem[]>([])
const loadingDocs = ref(false)
const loadingFAQ = ref(false)

// Upload
const uploading = ref(false)
const uploadDocType = ref('招商话术')
const docTypes = ['加盟政策', 'FAQ', '招商话术', '培训支持', '门店模型']
const uploadRef = ref()

// FAQ create form
const faqForm = ref({question: '', answer: '', category: '通用', priority: 0})
const faqCreating = ref(false)

onMounted(() => {
  loadDocuments()
  loadFAQ()
})

async function loadDocuments() {
  loadingDocs.value = true
  try {
    const {data} = await listDocuments()
    documents.value = data
  } catch {
    ElMessage.error('加载文档列表失败')
  } finally {
    loadingDocs.value = false
  }
}

async function loadFAQ() {
  loadingFAQ.value = true
  try {
    const {data} = await listFAQ()
    faqs.value = data
  } catch {
    ElMessage.error('加载 FAQ 失败')
  } finally {
    loadingFAQ.value = false
  }
}

async function onUpload(file: File) {
  uploading.value = true
  try {
    await uploadDocument(file, uploadDocType.value)
    ElMessage.success(`${file.name} 上传成功`)
    uploadRef.value?.clearFiles()
    loadDocuments()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

async function onReEmbed(doc: KnowledgeDocument) {
  try {
    await reEmbedDocument(doc.id)
    ElMessage.success('向量化已启动')
    loadDocuments()
  } catch {
    ElMessage.error('向量化失败')
  }
}

async function onToggle(doc: KnowledgeDocument) {
  try {
    await toggleDocument(doc.id, !doc.enabled)
    ElMessage.success(doc.enabled ? '已禁用' : '已启用')
    loadDocuments()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function onCreateFAQ() {
  if (!faqForm.value.question || !faqForm.value.answer) {
    ElMessage.warning('请填写问题和答案')
    return
  }
  faqCreating.value = true
  try {
    await createFAQ(faqForm.value)
    ElMessage.success('FAQ 创建成功')
    faqForm.value = {question: '', answer: '', category: '通用', priority: 0}
    loadFAQ()
  } catch {
    ElMessage.error('创建失败')
  } finally {
    faqCreating.value = false
  }
}

function statusTag(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    ready: 'success',
    error: 'danger',
  }
  return map[status] || 'info'
}

function statusText(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    ready: '已就绪',
    error: '失败',
  }
  return map[status] || status
}
</script>

<template>
  <div class="knowledge-view">
    <!-- Upload area -->
    <div class="upload-section">
      <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="(f: any) => onUpload(f.raw!)"
          :show-file-list="false"
          accept=".pdf,.docx,.txt,.md"
          drag
      >
        <el-icon :size="36">
          <UploadFilled/>
        </el-icon>
        <div class="upload-text">拖拽文件到此处或<em>点击上传</em></div>
        <div class="upload-hint">支持 PDF、Word、TXT、Markdown</div>
      </el-upload>
      <div class="upload-type">
        <span class="type-label">文档类型：</span>
        <el-radio-group v-model="uploadDocType" size="small">
          <el-radio-button v-for="t in docTypes" :key="t" :value="t">{{ t }}</el-radio-button>
        </el-radio-group>
        <el-button
            v-if="uploading"
            loading
            size="small"
            style="margin-left: 12px"
            type="primary"
        >
          上传中...
        </el-button>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="kb-tabs">
      <el-tab-pane label="知识文档" name="documents">
        <el-table v-loading="loadingDocs" :data="documents" empty-text="暂无文档" stripe>
          <el-table-column label="标题" min-width="180" prop="title" show-overflow-tooltip/>
          <el-table-column label="类型" prop="doc_type" width="100"/>
          <el-table-column label="版本" prop="version" width="80"/>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusTag(row.status)" size="small">
                {{ statusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column align="center" label="Chunk 数" prop="chunk_count" width="90"/>
          <el-table-column align="center" label="启用" width="70">
            <template #default="{ row }">
              <el-switch
                  :model-value="row.enabled"
                  size="small"
                  @change="onToggle(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="170">
            <template #default="{ row }">
              {{ row.uploaded_at?.slice(0, 16).replace('T', ' ') }}
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="140">
            <template #default="{ row }">
              <el-button size="small" text @click="onReEmbed(row)">向量化</el-button>
              <el-button size="small" text type="danger" @click="onToggle(row)">
                {{ row.enabled ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="FAQ" name="faq">
        <div class="faq-create-bar">
          <el-input v-model="faqForm.question" placeholder="问题" size="small" style="width: 200px"/>
          <el-input v-model="faqForm.answer" placeholder="答案" size="small" style="width: 300px"/>
          <el-input v-model="faqForm.category" placeholder="分类" size="small" style="width: 100px"/>
          <el-button :loading="faqCreating" size="small" type="primary" @click="onCreateFAQ">
            添加 FAQ
          </el-button>
        </div>
        <el-table v-loading="loadingFAQ" :data="faqs" empty-text="暂无 FAQ" stripe>
          <el-table-column label="问题" min-width="200" prop="question" show-overflow-tooltip/>
          <el-table-column label="分类" prop="category" width="100"/>
          <el-table-column align="center" label="优先级" prop="priority" width="80"/>
          <el-table-column align="center" label="启用" width="70">
            <template #default="{ row }">
              <el-switch :model-value="row.enabled" size="small"/>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="170">
            <template #default="{ row }">
              {{ row.created_at?.slice(0, 16).replace('T', ' ') }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.knowledge-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.upload-section {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.upload-text {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.upload-text em {
  color: #d4a853;
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.upload-type {
  display: flex;
  align-items: center;
  margin-top: 12px;
}

.type-label {
  font-size: 13px;
  color: #666;
  margin-right: 8px;
}

.kb-tabs {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

:deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.faq-create-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}
</style>
