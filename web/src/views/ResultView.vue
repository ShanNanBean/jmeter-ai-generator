<template>
  <div class="result-view">
    <h2 class="page-header">生成结果</h2>

    <div v-if="store.error" class="error-block">
      {{ store.error }}
    </div>

    <div v-if="store.jmx" class="page-section">
      <div class="section-title">JMX 文件</div>
      <div class="file-info">
        <span class="filename">{{ store.filename }}</span>
        <span class="status-badge status-success">已生成</span>
        <span v-if="copyMessage" class="copy-message">{{ copyMessage }}</span>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary" @click="downloadJMX">下载 JMX 文件</button>
        <button class="btn btn-secondary" @click="copyJMX">复制 JMX</button>
        <button class="btn btn-secondary" @click="showFullPreview = !showFullPreview">
          {{ showFullPreview ? '收起预览' : '展开完整预览' }}
        </button>
      </div>
      <pre class="jmx-preview"><code>{{ displayedJmx }}</code></pre>
    </div>

    <div v-if="store.pluginInfo.length" class="page-section">
      <div class="section-title">插件依赖 / 兼容性提示</div>
      <div
        v-for="info in store.pluginInfo"
        :key="`${info.name}-${info.component || 'native'}`"
        class="issue-item"
        :class="info.required ? 'issue-warning' : 'issue-info'"
      >
        <strong>{{ info.required ? '需要插件' : '提示' }}：{{ info.name }}</strong>
        <div>{{ info.description }}</div>
      </div>
    </div>

    <div v-if="store.validation" class="page-section">
      <div class="section-title">校验结果</div>
      <div class="validation-summary">
        <span v-if="store.validation.valid" class="status-badge status-success">所有校验通过</span>
        <span v-if="!store.validation.valid" class="status-badge status-error">存在问题，请检查</span>
        <span>{{ severitySummary }}</span>
      </div>
      <div v-for="(issue, idx) in store.validation.issues" :key="idx"
        class="issue-item"
        :class="'issue-' + issue.severity"
      >
        <strong>[{{ issue.severity }}]</strong>
        <span class="issue-location" v-if="issue.location"> {{ issue.location }}: </span>
        {{ issue.message }}
      </div>
    </div>

    <div class="btn-group">
      <button class="btn btn-secondary" @click="router.push('/edit')">返回编辑</button>
      <button class="btn btn-secondary" @click="handleNew">新建场景</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';

const router = useRouter();
const store = useGenerationStore();
const showFullPreview = ref(false);
const copyMessage = ref('');

const displayedJmx = computed(() => {
  if (showFullPreview.value) return store.jmx;
  const lines = store.jmx.split('\n');
  const preview = lines.slice(0, 60).join('\n');
  return lines.length > 60 ? `${preview}\n...\n（已省略 ${lines.length - 60} 行，点击“展开完整预览”查看全部）` : preview;
});

const severitySummary = computed(() => {
  const issues = store.validation?.issues || [];
  const counts = issues.reduce<Record<string, number>>((acc, issue) => {
    acc[issue.severity] = (acc[issue.severity] || 0) + 1;
    return acc;
  }, {});
  const errors = counts.error || 0;
  const warnings = counts.warning || 0;
  return `${errors} 个错误，${warnings} 个警告`;
});

function downloadJMX() {
  const blob = new Blob([store.jmx], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = store.filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function copyJMX() {
  await navigator.clipboard.writeText(store.jmx);
  copyMessage.value = '已复制';
  window.setTimeout(() => {
    copyMessage.value = '';
  }, 1500);
}

function handleNew() {
  store.reset();
  router.push('/');
}
</script>

<style scoped>
.error-block {
  background: #fee2e2;
  color: var(--color-error);
  padding: var(--spacing-md);
  border-radius: var(--radius);
  margin-bottom: var(--spacing-md);
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.filename {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 500;
}

.copy-message {
  color: var(--color-success);
  font-size: 0.8125rem;
}

.jmx-preview {
  max-height: 520px;
  overflow: auto;
  background: var(--color-code-bg);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
  font-size: 0.75rem;
  line-height: 1.5;
  margin-top: var(--spacing-md);
}

.issue-info {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.validation-summary {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.issue-location {
  font-weight: 600;
}
</style>
