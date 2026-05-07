<template>
  <div class="edit-view">
    <h2 class="page-header">确认并编辑 IR</h2>

    <div v-if="!ir" class="page-section empty-state">
      未找到可编辑的 IR，请返回输入页重新解析。
    </div>

    <template v-else>
      <div class="page-section">
        <div class="section-title">生成选项</div>
        <div class="field-group">
          <label>目标 JMeter 版本</label>
          <select v-model="store.jmeterVersion">
            <option v-for="version in jmeterVersions" :key="version" :value="version">
              JMeter {{ version }}
            </option>
          </select>
        </div>
      </div>

      <div class="page-section">
        <div class="section-title">测试计划</div>
        <div class="field-group">
          <label>计划名称</label>
          <input type="text" v-model="ir.testPlan.name" />
        </div>
      </div>

      <div class="page-section">
        <div class="section-title">线程组配置</div>
        <button class="btn btn-secondary btn-small" @click="addThreadGroup">新增线程组</button>
        <div v-for="(tg, idx) in ir.threadGroups" :key="idx" class="thread-group-card">
          <div class="field-row">
            <div class="field-group">
              <label>名称</label>
              <input type="text" v-model="tg.name" />
            </div>
            <div class="field-group">
              <label>线程数</label>
              <input type="number" min="1" step="1" v-model.number="tg.threads" />
            </div>
            <div class="field-group">
              <label>Ramp-up (秒)</label>
              <input type="number" min="0" step="1" v-model.number="tg.rampUp" />
            </div>
            <div class="field-group">
              <label>持续时间 (秒)</label>
              <input type="number" min="0" step="1" v-model.number="tg.duration" />
              <label>循环次数</label>
              <input type="number" min="-1" step="1" v-model.number="tg.loop" />
              <div class="hint">每个虚拟用户重复执行业务流程的轮数，-1 表示由持续时间控制。</div>
            </div>
          </div>
          <button v-if="ir.threadGroups.length > 1" class="btn btn-secondary btn-small" @click="removeThreadGroup(idx)">删除线程组</button>
          <div class="qps-row">
            <div class="field-group">
              <label>目标 QPS</label>
              <input type="number" min="1" step="1" v-model.number="targetQps[idx]" placeholder="例如 200" />
            </div>
            <button class="btn btn-secondary" @click="handleDeriveQps(idx)" :disabled="!targetQps[idx] || derivingQps === idx">
              {{ derivingQps === idx ? '推导中...' : '推导线程参数' }}
            </button>
          </div>
          <div v-if="qpsNotes[idx]" class="hint">{{ qpsNotes[idx] }}</div>
        </div>
      </div>

      <div class="page-section">
        <div class="section-title">场景步骤</div>
        <div v-for="(scenario, sIdx) in ir.scenarios" :key="sIdx">
          <div class="scenario-header">
            <strong>{{ scenario.name }}</strong>
            <div class="field-group inline-field">
              <label>归属线程组</label>
              <select v-model="scenario.threadGroup">
                <option v-for="tg in ir.threadGroups" :key="tg.name" :value="tg.name">{{ tg.name }}</option>
              </select>
            </div>
          </div>
          <div v-for="(step, stIdx) in scenario.steps" :key="stIdx" class="step-card">
            <div class="step-header">
              Step {{ stIdx + 1 }}: {{ step.name }}
            </div>
            <div class="field-row">
              <div class="field-group">
                <label>名称</label>
                <input type="text" v-model="step.name" />
              </div>
              <div class="field-group">
                <label>方法</label>
                <select v-model="step.method">
                  <option>GET</option><option>POST</option><option>PUT</option>
                  <option>DELETE</option><option>PATCH</option>
                </select>
              </div>
              <div class="field-group">
                <label>路径</label>
                <input type="text" v-model="step.path" />
              </div>
            </div>
            <div class="field-group">
              <label>请求体</label>
              <textarea v-model="step.body" rows="2" placeholder="无请求体可留空"></textarea>
            </div>

            <div class="sub-section">
              <div class="sub-header">
                <div class="section-title">等待时间 / 思考时间</div>
                <button class="btn btn-secondary btn-small" @click="addTimer(step, 'ConstantTimer')">固定等待</button>
                <button class="btn btn-secondary btn-small" @click="addTimer(step, 'UniformRandomTimer')">随机等待</button>
              </div>
              <div v-for="(timer, tIdx) in step.timers" :key="tIdx" class="sub-editor timer-editor">
                <select v-model="timer.type">
                  <option>ConstantTimer</option>
                  <option>UniformRandomTimer</option>
                </select>
                <input v-if="timer.type === 'ConstantTimer'" type="number" min="0" v-model.number="timer.delayMs" placeholder="固定等待 ms" />
                <template v-else>
                  <input type="number" min="0" v-model.number="timer.rangeMs![0]" placeholder="最小 ms" />
                  <input type="number" min="0" v-model.number="timer.rangeMs![1]" placeholder="最大 ms" />
                </template>
                <button class="btn btn-secondary btn-small" @click="removeItem(step.timers, tIdx)">删除</button>
              </div>
              <div v-if="!step.timers?.length" class="sub-item">暂无等待时间</div>
            </div>

            <div class="sub-section">
              <div class="sub-header">
                <div class="section-title">断言</div>
                <button class="btn btn-secondary btn-small" @click="addAssertion(step)">添加断言</button>
              </div>
              <div v-for="(a, aIdx) in step.assertions" :key="aIdx" class="sub-editor">
                <select v-model="a.type">
                  <option>ResponseAssertion</option>
                  <option>DurationAssertion</option>
                  <option>SizeAssertion</option>
                  <option>JSONAssertion</option>
                </select>
                <input type="text" v-model="a.pattern" placeholder="匹配内容 / JSONPath" />
                <input type="number" min="0" step="1" v-model.number="a.maxMs" placeholder="最大耗时 ms" />
                <button class="btn btn-secondary btn-small" @click="removeItem(step.assertions, aIdx)">删除</button>
              </div>
              <div v-if="!step.assertions?.length" class="sub-item">暂无断言</div>
            </div>

            <div class="sub-section">
              <div class="sub-header">
                <div class="section-title">提取器</div>
                <button class="btn btn-secondary btn-small" @click="addExtractor(step)">添加提取器</button>
              </div>
              <div v-for="(e, eIdx) in step.extractors" :key="eIdx" class="sub-editor extractor-editor">
                <select v-model="e.type">
                  <option>JSONExtractor</option>
                  <option>RegexExtractor</option>
                  <option>CSSExtractor</option>
                </select>
                <input type="text" v-model="e.variable" placeholder="变量名" />
                <input type="text" v-model="e.path" placeholder="JSONPath/CSS Path" />
                <input type="text" v-model="e.regex" placeholder="正则" />
                <input type="text" v-model="e.defaultValue" placeholder="默认值" />
                <button class="btn btn-secondary btn-small" @click="removeItem(step.extractors, eIdx)">删除</button>
              </div>
              <div v-if="!step.extractors?.length" class="sub-item">暂无提取器</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="reasonablenessIssues.length" class="page-section warning-block">
        <div class="section-title">脚本合理性检查</div>
        <div v-for="(issue, idx) in reasonablenessIssues" :key="idx" class="issue-item issue-warning">
          <strong>[{{ issue.severity }}]</strong> {{ issue.location ? `${issue.location}: ` : '' }}{{ issue.message }}
        </div>
      </div>

      <div v-if="validationErrors.length" class="error-message">
        <div v-for="error in validationErrors" :key="error">{{ error }}</div>
      </div>

      <div v-if="store.status === 'generating'" class="loading-state">
        <div class="spinner"></div>
        <span>正在生成 JMX 文件...</span>
      </div>

      <div class="btn-group">
        <button class="btn btn-secondary" @click="router.push('/preview')">返回预览</button>
        <button class="btn btn-secondary" @click="handleReasonablenessCheck">检查脚本合理性</button>
        <button class="btn btn-primary" @click="handleGenerate" :disabled="store.status === 'generating' || !canGenerate">
          生成 JMX
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';
import { useConfigStore } from '../stores/config';
import { deriveQPS, checkReasonableness } from '../api/client';
import type { Assertion, Extractor, Step, Timer, ValidationIssue } from '../api/types';

const router = useRouter();
const store = useGenerationStore();
const configStore = useConfigStore();
const targetQps = ref<Record<number, number | undefined>>({});
const qpsNotes = ref<Record<number, string>>({});
const derivingQps = ref<number | null>(null);
const reasonablenessIssues = ref<ValidationIssue[]>([]);

onMounted(() => configStore.load());

const ir = computed(() => store.ir);
const jmeterVersions = computed(() => configStore.jmeterVersions.available.length
  ? configStore.jmeterVersions.available
  : [configStore.jmeterVersions.default || '5.0']
);

const validationErrors = computed(() => {
  if (!ir.value) return ['IR 为空'];
  const errors: string[] = [];
  ir.value.threadGroups.forEach((tg, idx) => {
    if (!tg.name?.trim()) errors.push(`线程组 ${idx + 1} 名称不能为空`);
    if (!Number.isFinite(tg.threads) || tg.threads < 1) errors.push(`线程组 ${idx + 1} 线程数必须大于 0`);
    if (!Number.isFinite(tg.rampUp) || tg.rampUp < 0) errors.push(`线程组 ${idx + 1} Ramp-up 不能为负`);
    if (tg.duration !== undefined && tg.duration < 0) errors.push(`线程组 ${idx + 1} 持续时间不能为负`);
  });
  return errors;
});

const canGenerate = computed(() => validationErrors.value.length === 0);

function ensureAssertions(step: Step): Assertion[] {
  if (!step.assertions) step.assertions = [];
  return step.assertions;
}

function ensureExtractors(step: Step): Extractor[] {
  if (!step.extractors) step.extractors = [];
  return step.extractors;
}

function ensureTimers(step: Step): Timer[] {
  if (!step.timers) step.timers = [];
  return step.timers;
}

function addThreadGroup() {
  if (!ir.value) return;
  const nextIndex = ir.value.threadGroups.length + 1;
  ir.value.threadGroups.push({
    name: `线程组 ${nextIndex}`,
    threads: 10,
    rampUp: 10,
    duration: 300,
    loop: -1,
  });
}

function removeThreadGroup(index: number) {
  if (!ir.value || ir.value.threadGroups.length <= 1) return;
  const removed = ir.value.threadGroups[index];
  ir.value.threadGroups.splice(index, 1);
  const fallback = ir.value.threadGroups[0].name;
  ir.value.scenarios.forEach((scenario) => {
    if (scenario.threadGroup === removed.name) scenario.threadGroup = fallback;
  });
}

function addAssertion(step: Step) {
  ensureAssertions(step).push({ type: 'ResponseAssertion', pattern: '200' });
}

function addExtractor(step: Step) {
  ensureExtractors(step).push({ type: 'JSONExtractor', variable: 'value', path: '$.data', defaultValue: '' });
}

function addTimer(step: Step, type: 'ConstantTimer' | 'UniformRandomTimer') {
  ensureTimers(step).push(
    type === 'ConstantTimer'
      ? { type, delayMs: 1000 }
      : { type, rangeMs: [1000, 3000] },
  );
}

function removeItem(items: unknown[] | undefined, index: number) {
  items?.splice(index, 1);
}

async function handleDeriveQps(threadGroupIndex: number) {
  if (!ir.value || !targetQps.value[threadGroupIndex]) return;
  derivingQps.value = threadGroupIndex;
  try {
    const steps = ir.value.scenarios.flatMap((scenario) => scenario.steps || []);
    const result: any = await deriveQPS(targetQps.value[threadGroupIndex]!, steps);
    const threadGroup = ir.value.threadGroups[threadGroupIndex];
    threadGroup.threads = result.threads;
    threadGroup.rampUp = result.rampUp;
    threadGroup.duration = result.duration;
    threadGroup.loop = result.loop;
    qpsNotes.value[threadGroupIndex] = result.qpsNote;
  } finally {
    derivingQps.value = null;
  }
}

async function handleGenerate() {
  if (!canGenerate.value) return;
  try {
    await store.generate(true);
    router.push('/result');
  } catch {
    // Error stored in store.error
  }
}

async function handleReasonablenessCheck() {
  if (!ir.value) return;
  const result: any = await checkReasonableness(ir.value);
  reasonablenessIssues.value = result.issues || [];
}
</script>

<style scoped>
.thread-group-card {
  background: var(--color-code-bg);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);
}

.field-group {
  margin-bottom: var(--spacing-sm);
}

.field-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-sm);
}

.qps-row {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.step-card {
  background: var(--color-code-bg);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);
}

.step-header {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-primary);
  margin-bottom: var(--spacing-sm);
}

.sub-section {
  margin-top: var(--spacing-sm);
  padding-left: var(--spacing-md);
}

.sub-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
}

.sub-item {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  padding: 2px 0;
}

.sub-editor {
  display: grid;
  grid-template-columns: 160px 1fr 140px auto;
  gap: var(--spacing-xs);
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.extractor-editor {
  grid-template-columns: 150px 120px 1fr 1fr 120px auto;
}

.timer-editor {
  grid-template-columns: 150px 1fr 1fr auto;
}

.scenario-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin: var(--spacing-md) 0 var(--spacing-sm);
}

.inline-field {
  min-width: 220px;
  margin-bottom: 0;
}

.warning-block {
  border: 1px solid #f59e0b;
  background: #fffbeb;
}

.btn-small {
  padding: 4px 8px;
  font-size: 0.75rem;
}

.hint {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  margin-top: var(--spacing-xs);
}

.error-message {
  background: #fee2e2;
  color: var(--color-error);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-md);
  font-size: 0.875rem;
}

.empty-state {
  color: var(--color-text-muted);
}

select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}
</style>
