<template>
  <div class="preview-view">
    <h2 class="page-header">场景预览</h2>

    <div v-if="previewStore.status === 'loading'" class="loading-overlay">
      <div class="spinner"></div>
      <span>{{ loadingMessage }}</span>
    </div>

    <div v-if="previewStore.error" class="error-block">
      {{ previewStore.error }}
    </div>

    <div v-if="previewStore.previewText" class="page-section">
      <div class="section-title">伪脚本</div>
      <div class="preview-text">{{ previewStore.previewText }}</div>
    </div>

    <div v-if="previewStore.dependencyIssues.length" class="page-section">
      <div class="section-title">变量依赖问题</div>
      <div
        v-for="(issue, idx) in previewStore.dependencyIssues"
        :key="idx"
        class="issue-item issue-warning"
      >{{ issue }}</div>
    </div>

    <div v-if="!previewStore.dependencyIssues.length && previewStore.previewText" class="page-section">
      <span class="status-badge status-success">所有变量依赖链完整</span>
    </div>

    <div class="page-section">
      <div class="section-title">修改建议</div>
      <textarea
        v-model="feedback"
        :disabled="isUpdating"
        placeholder="输入修改意见，例如：支付接口想加一个条件判断..."
        rows="3"
      ></textarea>
      <div class="btn-group">
        <button
          class="btn btn-secondary"
          @click="handleUpdate"
          :disabled="!feedback.trim() || isUpdating"
        >
          {{ isUpdating ? '修改中...' : '修改场景' }}
        </button>
      </div>
    </div>

    <div class="btn-group">
      <button class="btn btn-secondary" @click="router.push('/')" :disabled="isUpdating">返回输入</button>
      <button class="btn btn-success" @click="handleConfirm" :disabled="isUpdating">确认并生成 JMX</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';
import { usePreviewStore } from '../stores/preview';

const router = useRouter();
const store = useGenerationStore();
const previewStore = usePreviewStore();
const feedback = ref('');

const isUpdating = computed(() => previewStore.status === 'loading');
const loadingMessage = computed(() =>
  isUpdating.value ? '正在根据修改建议更新场景...' : '正在生成场景预览...'
);

async function handleUpdate() {
  try {
    const result = await previewStore.update(store.ir, feedback.value);
    if (result.ir) {
      store.ir = result.ir;
    }
    feedback.value = '';
  } catch {
    // Error is stored in previewStore.error
  }
}

function handleConfirm() {
  router.push('/edit');
}
</script>

<style scoped>
.loading-overlay {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-bg);
  border-radius: var(--radius);
  margin-bottom: var(--spacing-md);
  color: var(--color-text-secondary);
}
.error-block {
  background: #fee2e2;
  color: var(--color-error);
  padding: var(--spacing-md);
  border-radius: var(--radius);
  margin-bottom: var(--spacing-md);
}
textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>