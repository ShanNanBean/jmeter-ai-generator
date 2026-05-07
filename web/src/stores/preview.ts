import { defineStore } from 'pinia';
import { ref } from 'vue';
import { generatePreview, updatePreview, checkDependencies } from '../api/client';
import type { PlanSummary, SanityWarning, VariableChain } from '../api/types';

export const usePreviewStore = defineStore('preview', () => {
  const previewText = ref<string>('');
  const dependencyIssues = ref<string[]>([]);
  const planSummary = ref<PlanSummary | null>(null);
  const sanityWarnings = ref<SanityWarning[]>([]);
  const variableChains = ref<VariableChain[]>([]);
  const status = ref<'idle' | 'loading' | 'error'>('idle');
  const error = ref<string>('');

  async function generate(ir: any) {
    status.value = 'loading';
    error.value = '';
    try {
      const result = await generatePreview(ir);
      previewText.value = result.preview_text;
      dependencyIssues.value = result.dependency_issues;
      planSummary.value = result.plan_summary;
      sanityWarnings.value = result.sanity_warnings || [];
      variableChains.value = result.variable_chains || [];
      status.value = 'idle';
      return result;
    } catch (e: any) {
      error.value = e.message;
      status.value = 'error';
      throw e;
    }
  }

  async function update(ir: any, feedback: string, provider?: string) {
    status.value = 'loading';
    error.value = '';
    try {
      const result = await updatePreview(ir, feedback, provider);
      previewText.value = result.preview_text;
      dependencyIssues.value = result.dependency_issues;
      planSummary.value = result.plan_summary;
      sanityWarnings.value = result.sanity_warnings || [];
      variableChains.value = result.variable_chains || [];
      status.value = 'idle';
      return result;
    } catch (e: any) {
      error.value = e.message;
      status.value = 'error';
      throw e;
    }
  }

  async function check(ir: any) {
    try {
      const result = await checkDependencies(ir);
      dependencyIssues.value = result.issues;
      variableChains.value = result.variable_chains || [];
      return result.issues;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  return { previewText, dependencyIssues, planSummary, sanityWarnings, variableChains, status, error, generate, update, check };
});