import { defineStore } from 'pinia';
import { ref } from 'vue';
import { parseInput, generateJMX } from '../api/client';
import type { IRDocument, PluginInfo, ValidationResult } from '../api/types';

export const useGenerationStore = defineStore('generation', () => {
  const ir = ref<IRDocument | null>(null);
  const jmx = ref<string>('');
  const filename = ref<string>('');
  const validation = ref<ValidationResult | null>(null);
  const status = ref<'idle' | 'parsing' | 'generating' | 'error'>('idle');
  const error = ref<string>('');
  const llmUsage = ref<any>(null);
  const jmeterVersion = ref<string>('5.0');
  const pluginInfo = ref<PluginInfo[]>([]);

  async function parse(
    userInput: string,
    mode: string = 'natural',
    provider?: string,
    temperature: number = 0.3,
    options: { pressureGoal?: any; allowedPlugins?: string[]; parsePreference?: string } = {},
  ) {
    status.value = 'parsing';
    error.value = '';
    try {
      const result: any = await parseInput(userInput, mode, provider, temperature, options);
      ir.value = result.ir;
      llmUsage.value = result.llm_usage;
      status.value = 'idle';
      return result;
    } catch (e: any) {
      error.value = e.message;
      status.value = 'error';
      throw e;
    }
  }

  async function generate(validate: boolean = true) {
    if (!ir.value) return;
    status.value = 'generating';
    error.value = '';
    try {
      const result: any = await generateJMX(ir.value, validate, jmeterVersion.value);
      jmx.value = result.jmx;
      filename.value = result.filename;
      validation.value = result.validation;
      pluginInfo.value = result.plugin_info || [];
      status.value = 'idle';
      return result;
    } catch (e: any) {
      error.value = e.message;
      status.value = 'error';
      throw e;
    }
  }

  function reset() {
    ir.value = null;
    jmx.value = '';
    filename.value = '';
    validation.value = null;
    pluginInfo.value = [];
    status.value = 'idle';
    error.value = '';
    llmUsage.value = null;
  }

  return { ir, jmx, filename, validation, status, error, llmUsage, jmeterVersion, pluginInfo, parse, generate, reset };
});
