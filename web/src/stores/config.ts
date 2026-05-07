import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getStatus, getProviders, getComponents, getJmeterVersions } from '../api/client';
import type { ProviderInfo } from '../api/types';

interface JmeterVersionsConfig {
  default: string;
  available: string[];
}

export const useConfigStore = defineStore('config', () => {
  const providers = ref<ProviderInfo[]>([]);
  const components = ref<string[]>([]);
  const jmeterVersions = ref<JmeterVersionsConfig>({ default: '5.0', available: ['5.0'] });
  const appStatus = ref<any>(null);
  const loaded = ref(false);

  async function load() {
    if (loaded.value) return;
    try {
      const [status, providerList, componentList, versions] = await Promise.all([
        getStatus(),
        getProviders(),
        getComponents(),
        getJmeterVersions(),
      ]);
      appStatus.value = status;
      providers.value = providerList as ProviderInfo[];
      components.value = componentList as string[];
      jmeterVersions.value = versions as JmeterVersionsConfig;
      loaded.value = true;
    } catch (e) {
      console.error('Failed to load config:', e);
    }
  }

  return { providers, components, jmeterVersions, appStatus, loaded, load };
});
