import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getStatus, getProviders } from '../api/client';

export const useConfigStore = defineStore('config', () => {
  const providers = ref<any[]>([]);
  const components = ref<string[]>([]);
  const appStatus = ref<any>(null);
  const loaded = ref(false);

  async function load() {
    if (loaded.value) return;
    try {
      const status = await getStatus();
      appStatus.value = status;
      providers.value = await getProviders();
      loaded.value = true;
    } catch (e) {
      console.error('Failed to load config:', e);
    }
  }

  return { providers, components, appStatus, loaded, load };
});