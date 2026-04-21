import { defineStore } from 'pinia';
import { ref } from 'vue';
import { generatePreview, updatePreview, checkDependencies } from '../api/client';

export const usePreviewStore = defineStore('preview', () => {
  const previewText = ref<string>('');
  const dependencyIssues = ref<string[]>([]);
  const status = ref<'idle' | 'loading' | 'error'>('idle');
  const error = ref<string>('');

  async function generate(ir: any) {
    status.value = 'loading';
    error.value = '';
    try {
      const result = await generatePreview(ir);
      previewText.value = result.preview_text;
      dependencyIssues.value = result.dependency_issues;
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
      return result.issues;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  return { previewText, dependencyIssues, status, error, generate, update, check };
});