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

    <div v-if="showDependencyConfirm" class="page-section warning-block">
      <div class="section-title">发现变量依赖问题</div>
      <p>继续前建议先修复以下问题：</p>
      <div v-for="(issue, idx) in pendingIssues" :key="idx" class="issue-item issue-warning">
        {{ issue }}
      </div>
      <div class="btn-group">
        <button class="btn btn-secondary" @click="showDependencyConfirm = false">返回修改</button>
        <button class="btn btn-success" @click="proceedAnyway">仍然继续</button>
      </div>
    </div>

    <div v-if="previewStore.planSummary" class="page-section">
      <div class="section-title">系统推荐压测方案</div>
      <div class="summary-grid">
        <div><strong>{{ previewStore.planSummary.thread_group_count }}</strong><span>并发模型</span></div>
        <div><strong>{{ previewStore.planSummary.scenario_count }}</strong><span>业务链路</span></div>
        <div><strong>{{ previewStore.planSummary.step_count }}</strong><span>接口步骤</span></div>
        <div><strong>{{ previewStore.planSummary.total_threads }}</strong><span>虚拟用户</span></div>
      </div>
      <div v-for="tg in previewStore.planSummary.thread_groups" :key="tg.name" class="summary-item">
        {{ tg.name }}：{{ tg.threads }} 用户，{{ tg.rampUp }} 秒启动，
        {{ tg.duration ? `持续 ${tg.duration} 秒` : '按循环次数运行' }}，负责 {{ tg.scenario_count }} 条业务链路。
      </div>
    </div>

    <div v-if="previewStore.sanityWarnings.length" class="page-section">
      <div class="section-title">合理性提醒</div>
      <div
        v-for="(warning, idx) in previewStore.sanityWarnings"
        :key="idx"
        class="issue-item"
        :class="warning.severity === 'info' ? 'issue-info' : 'issue-warning'"
      >
        <strong>{{ warning.location || warning.category }}</strong>：{{ warning.message }}
        <div v-if="warning.suggestion" class="hint">建议：{{ warning.suggestion }}</div>
      </div>
    </div>

    <div v-if="previewStore.variableChains.length" class="page-section">
      <div class="section-title">参数传递链</div>
      <div v-for="chain in previewStore.variableChains" :key="chain.variable" class="chain-item">
        <strong>{{ formatVariable(chain.variable) }}</strong>：{{ chain.source }}
        <span v-if="chain.source_step">（{{ chain.source_step }}）</span>
        <div v-if="chain.usages.length" class="hint">
          使用于：{{ chain.usages.map((u) => `${u.step}`).join(' → ') }}
        </div>
      </div>
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
const showDependencyConfirm = ref(false);
const pendingIssues = ref<string[]>([]);

const isUpdating = computed(() => previewStore.status === 'loading');
const loadingMessage = computed(() =>
  isUpdating.value ? '正在根据修改建议更新场景...' : '正在生成场景预览...'
);

function formatVariable(variable: string) {
  return '${' + variable + '}';
}

async function handleUpdate() {
  if (!store.ir) return;
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

async function handleConfirm() {
  if (!store.ir) return;
  try {
    const issues = await previewStore.check(store.ir);
    if (issues.length) {
      pendingIssues.value = issues;
      showDependencyConfirm.value = true;
      return;
    }
    router.push('/edit');
  } catch {
    // Error stored in previewStore.error
  }
}

function proceedAnyway() {
  showDependencyConfirm.value = false;
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
.warning-block {
  border: 1px solid #f59e0b;
  background: #fffbeb;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}
.summary-grid > div {
  background: var(--color-code-bg);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.summary-grid strong {
  font-size: 1.5rem;
  color: var(--color-primary);
}
.summary-grid span,
.hint {
  color: var(--color-text-muted);
  font-size: 0.8125rem;
}
.summary-item,
.chain-item {
  padding: var(--spacing-sm) 0;
  border-top: 1px solid var(--color-border);
}
.issue-info {
  background: #eff6ff;
  border-left-color: #3b82f6;
}
textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
