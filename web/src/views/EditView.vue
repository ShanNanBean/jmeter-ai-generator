<template>
  <div class="edit-view">
    <h2 class="page-header">确认并编辑 IR</h2>

    <div class="page-section">
      <div class="section-title">测试计划</div>
      <div class="field-group">
        <label>计划名称</label>
        <input type="text" v-model="ir.testPlan.name" />
      </div>
    </div>

    <div class="page-section">
      <div class="section-title">线程组配置</div>
      <div v-for="(tg, idx) in ir.threadGroups" :key="idx" class="thread-group-card">
        <div class="field-row">
          <div class="field-group">
            <label>名称</label>
            <input type="text" v-model="tg.name" />
          </div>
          <div class="field-group">
            <label>线程数</label>
            <input type="text" v-model.number="tg.threads" />
          </div>
          <div class="field-group">
            <label>Ramp-up (秒)</label>
            <input type="text" v-model.number="tg.rampUp" />
          </div>
          <div class="field-group">
            <label>持续时间 (秒)</label>
            <input type="text" v-model.number="tg.duration" />
          </div>
        </div>
      </div>
    </div>

    <div class="page-section">
      <div class="section-title">场景步骤</div>
      <div v-for="(scenario, sIdx) in ir.scenarios" :key="sIdx">
        <div v-for="(step, stIdx) in scenario.steps" :key="stIdx" class="step-card">
          <div class="step-header">
            Step {{ stIdx + 1 }}: {{ step.name }}
          </div>
          <div class="field-row">
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
          <div v-if="step.body" class="field-group">
            <label>请求体</label>
            <textarea v-model="step.body" rows="2"></textarea>
          </div>
          <div v-if="step.assertions?.length" class="sub-section">
            <div class="section-title">断言</div>
            <div v-for="(a, aIdx) in step.assertions" :key="aIdx" class="sub-item">
              {{ a.type }}: {{ a.pattern || a.maxMs }}
            </div>
          </div>
          <div v-if="step.extractors?.length" class="sub-section">
            <div class="section-title">提取器</div>
            <div v-for="(e, eIdx) in step.extractors" :key="eIdx" class="sub-item">
              {{ e.variable }} ← {{ e.type }} {{ e.path || e.regex }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.status === 'generating'" class="loading-state">
      <div class="spinner"></div>
      <span>正在生成 JMX 文件...</span>
    </div>

    <div class="btn-group">
      <button class="btn btn-secondary" @click="router.push('/preview')">返回预览</button>
      <button class="btn btn-primary" @click="handleGenerate" :disabled="store.status === 'generating'">
        生成 JMX
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGenerationStore } from '../stores/generation';

const router = useRouter();
const store = useGenerationStore();

const ir = computed(() => store.ir);

async function handleGenerate() {
  try {
    await store.generate(true);
    router.push('/result');
  } catch {
    // Error stored in store.error
  }
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

.sub-item {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  padding: 2px 0;
}

select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}
</style>