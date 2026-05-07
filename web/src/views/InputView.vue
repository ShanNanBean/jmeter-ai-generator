<template>
  <div class="input-view">
    <h2 class="page-header">压测需求助手</h2>

    <div class="mode-selector">
      <button class="tab-btn" :class="{ active: mode === 'natural' }" @click="mode = 'natural'">自由描述</button>
      <button class="tab-btn" :class="{ active: mode === 'semi_structured' }" @click="mode = 'semi_structured'">按要素描述</button>
    </div>

    <div class="page-section">
      <label>你想压测什么业务？</label>
      <textarea
        v-model="userInput"
        placeholder="描述接口步骤、参数传递、压测目标、数据来源、校验要求。例如：登录获取 token，查询商品提取 productId，再创建订单；目标 100 并发、持续 5 分钟。"
        :disabled="store.status === 'parsing'"
      ></textarea>
      <div class="hint">{{ userInput.length }} 字。可以直接写业务语言，不需要了解 JMeter 组件名称。</div>
    </div>

    <div v-if="mode === 'semi_structured'" class="page-section structured-grid">
      <div class="field-group">
        <label>目标地址</label>
        <input type="text" v-model="form.baseUrl" placeholder="https://api.example.com" />
      </div>
      <div class="field-group">
        <label>压测目的</label>
        <input type="text" v-model="form.purpose" placeholder="验证下单链路是否能支撑活动流量" />
      </div>
      <div class="field-group">
        <label>并发用户数</label>
        <input type="number" min="1" v-model.number="form.threads" placeholder="100" />
      </div>
      <div class="field-group">
        <label>目标 QPS</label>
        <input type="number" min="1" v-model.number="form.targetQps" placeholder="200" />
      </div>
      <div class="field-group">
        <label>持续时间（秒）</label>
        <input type="number" min="1" v-model.number="form.duration" placeholder="300" />
      </div>
      <div class="field-group">
        <label>启动时间 Ramp-up（秒）</label>
        <input type="number" min="0" v-model.number="form.rampUp" placeholder="60" />
      </div>
      <div class="field-group wide">
        <label>步骤间等待</label>
        <input type="text" v-model="form.thinkTime" placeholder="例如：每步随机等待 1-3 秒，或不等待压接口极限" />
      </div>
      <div class="field-group wide">
        <label>参数传递说明</label>
        <input type="text" v-model="form.variables" placeholder="例如：登录响应提取 token，创建订单响应提取 orderId" />
      </div>
      <div class="field-group wide">
        <label>校验要求</label>
        <input type="text" v-model="form.assertions" placeholder="例如：状态码 200，响应包含 success，响应时间小于 2 秒" />
      </div>
    </div>

    <details class="page-section">
      <summary>高级设置</summary>
      <div class="config-grid">
        <div class="field-group">
          <label>解析偏好</label>
          <select v-model="parsePreference">
            <option value="strict">严格按描述生成</option>
            <option value="balanced">自动补全常见配置</option>
            <option value="complete">尽量生成完整压测方案</option>
          </select>
        </div>
        <div class="field-group">
          <label>第三方插件策略</label>
          <select v-model="pluginPolicy">
            <option value="native">仅使用 JMeter 原生组件</option>
            <option value="allow_plugins">允许精准 QPS / 阶梯并发插件</option>
          </select>
        </div>
        <div class="field-group">
          <label>LLM Provider</label>
          <select v-model="selectedProvider" :disabled="store.status === 'parsing'">
            <option value="">默认 Provider</option>
            <option v-for="provider in configStore.providers" :key="provider.name" :value="provider.name">
              {{ provider.name }} ({{ provider.model }})
            </option>
          </select>
        </div>
      </div>
    </details>

    <div v-if="store.status === 'parsing'" class="loading-state">
      <div class="spinner"></div>
      <span>正在把业务需求转换为压测方案...</span>
    </div>

    <div v-if="store.error" class="error-message">{{ store.error }}</div>

    <div class="btn-group">
      <button class="btn btn-primary" :disabled="!userInput.trim() || store.status === 'parsing'" @click="handleSubmit">
        生成推荐压测方案
      </button>
    </div>

    <div class="example-section">
      <div class="section-title">示例场景</div>
      <div class="example-list">
        <button class="btn btn-secondary" @click="useExample(0)">简单登录压测</button>
        <button class="btn btn-secondary" @click="useExample(1)">多步骤业务流程</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';
import { usePreviewStore } from '../stores/preview';
import { useConfigStore } from '../stores/config';

const router = useRouter();
const store = useGenerationStore();
const previewStore = usePreviewStore();
const configStore = useConfigStore();

const userInput = ref('');
const mode = ref('natural');
const selectedProvider = ref('');
const parsePreference = ref<'strict' | 'balanced' | 'complete'>('balanced');
const pluginPolicy = ref<'native' | 'allow_plugins'>('native');
const form = reactive({
  baseUrl: '',
  purpose: '',
  threads: undefined as number | undefined,
  targetQps: undefined as number | undefined,
  duration: undefined as number | undefined,
  rampUp: undefined as number | undefined,
  thinkTime: '',
  variables: '',
  assertions: '',
});

onMounted(() => configStore.load());

const temperature = computed(() => {
  if (parsePreference.value === 'strict') return 0.1;
  if (parsePreference.value === 'complete') return 0.6;
  return 0.3;
});

const examples = [
  '对 https://api.example.com 的登录接口做压测，50 个用户并发，持续 1 分钟，检查响应码为 200，响应时间不超过 2 秒。',
  '测试电商下单流程：登录获取 token，浏览商品列表提取 productId，创建订单提取 orderId，最后支付。100 并发持续 5 分钟，目标 QPS 200，每步随机等待 1-3 秒。',
];

function useExample(idx: number) {
  userInput.value = examples[idx];
}

function buildStructuredText() {
  if (mode.value !== 'semi_structured') return userInput.value;
  const lines = [userInput.value];
  if (form.baseUrl) lines.push(`目标地址：${form.baseUrl}`);
  if (form.purpose) lines.push(`压测目的：${form.purpose}`);
  if (form.threads) lines.push(`并发用户数：${form.threads}`);
  if (form.targetQps) lines.push(`目标 QPS：${form.targetQps}`);
  if (form.duration) lines.push(`持续时间：${form.duration} 秒`);
  if (form.rampUp !== undefined) lines.push(`Ramp-up：${form.rampUp} 秒`);
  if (form.thinkTime) lines.push(`步骤间等待：${form.thinkTime}`);
  if (form.variables) lines.push(`参数传递：${form.variables}`);
  if (form.assertions) lines.push(`校验要求：${form.assertions}`);
  lines.push(pluginPolicy.value === 'native' ? '插件策略：仅使用 JMeter 原生组件' : '插件策略：允许使用精准 QPS 或阶梯并发插件');
  return lines.filter(Boolean).join('\n');
}

async function handleSubmit() {
  try {
    const pressureGoal = {
      threads: form.threads,
      target_qps: form.targetQps,
      duration: form.duration,
      ramp_up: form.rampUp,
      think_time: form.thinkTime,
      purpose: form.purpose,
    };
    await store.parse(buildStructuredText(), mode.value, selectedProvider.value || undefined, temperature.value, {
      pressureGoal,
      allowedPlugins: pluginPolicy.value === 'allow_plugins' ? ['throughput_shaping_timer', 'custom_thread_groups'] : [],
      parsePreference: parsePreference.value,
    });
    if (store.ir) {
      await previewStore.generate(store.ir);
      router.push('/preview');
    }
  } catch {
    // Error is stored in store.error
  }
}
</script>

<style scoped>
.error-message {
  background: #fee2e2;
  color: var(--color-error);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-md);
  font-size: 0.875rem;
}

.example-section {
  margin-top: var(--spacing-xl);
}

.example-list {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.config-grid,
.structured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-md);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.wide {
  grid-column: span 2;
}

.hint {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  margin-top: var(--spacing-xs);
}

summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}
</style>
