<template>
  <div id="app-container">
    <header class="app-header">
      <h1 class="app-title">JMeter AI Generator</h1>
      <span class="app-subtitle">AI 驱动的 JMeter 脚本生成</span>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useConfigStore } from './stores/config';

const configStore = useConfigStore();
configStore.load();
</script>

<style scoped>
.app-container {
  max-width: var(--max-width);
  margin: 0 auto;
}

.app-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) 0;
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
}

.app-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.app-main {
  min-height: 60vh;
}
</style>