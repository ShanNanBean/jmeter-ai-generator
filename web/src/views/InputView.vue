<template>
  <div class="input-view">
    <h2 class="page-header">描述你的测试场景</h2>

    <div class="mode-selector">
      <button
        class="tab-btn"
        :class="{ active: mode === 'natural' }"
        @click="mode = 'natural'"
      >自然语言</button>
      <button
        class="tab-btn"
        :class="{ active: mode === 'semi_structured' }"
        @click="mode = 'semi_structured'"
      >半结构化</button>
    </div>

    <div class="page-section">
      <label>测试场景描述</label>
      <textarea
        v-model="userInput"
        placeholder="例如：对 https://api.example.com 的登录接口做压测，50个用户并发，持续1分钟，检查响应时间不超过2秒"
        :disabled="store.status === 'parsing'"
      ></textarea>
    </div>

    <div v-if="mode === 'semi_structured'" class="page-section">
      <label>目标地址</label>
      <input type="text" v-model="baseUrl" placeholder="https://api.example.com" />
    </div>

    <div v-if="store.status === 'parsing'" class="loading-state">
      <div class="spinner"></div>
      <span>正在解析您的测试场景...</span>
    </div>

    <div v-if="store.error" class="error-message">
      {{ store.error }}
    </div>

    <div class="btn-group">
      <button
        class="btn btn-primary"
        :disabled="!userInput.trim() || store.status === 'parsing'"
        @click="handleSubmit"
      >解析场景</button>
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
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';
import { usePreviewStore } from '../stores/preview';

const router = useRouter();
const store = useGenerationStore();
const previewStore = usePreviewStore();

const userInput = ref('');
const baseUrl = ref('');
const mode = ref('natural');

const examples = [
  '对 https://api.example.com 的登录接口做压测，50个用户并发，持续1分钟，检查响应码为200，响应时间不超过2秒',
  '测试电商下单流程：1) 登录获取token 2) 浏览商品列表提取商品ID 3) 创建订单提取订单号 4) 支付，100并发持续5分钟，目标QPS 200',
];

function useExample(idx: number) {
  userInput.value = examples[idx];
}

async function handleSubmit() {
  try {
    await store.parse(userInput.value, mode.value);
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
</style>