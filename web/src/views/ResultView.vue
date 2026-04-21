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
      </div>
      <div class="btn-group">
        <button class="btn btn-primary" @click="downloadJMX">下载 JMX 文件</button>
      </div>
    </div>

    <div v-if="store.validation" class="page-section">
      <div class="section-title">校验结果</div>
      <div v-if="store.validation.valid" class="status-badge status-success">
        所有校验通过
      </div>
      <div v-if="!store.validation.valid" class="status-badge status-error">
        存在问题，请检查
      </div>
      <div v-for="(issue, idx) in store.validation.issues" :key="idx"
        class="issue-item"
        :class="'issue-' + issue.severity"
      >
        <span class="issue-location" v-if="issue.location">{{ issue.location }}: </span>
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
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';

const router = useRouter();
const store = useGenerationStore();

function downloadJMX() {
  const blob = new Blob([store.jmx], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = store.filename;
  a.click();
  URL.revokeObjectURL(url);
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

.issue-location {
  font-weight: 600;
}
</style>