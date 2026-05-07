const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

interface ApiFetchOptions extends RequestInit {
  timeoutMs?: number;
}

async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { timeoutMs = 30000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
    });

    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try {
        const data = await response.json();
        if (data?.detail) message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } catch {
        // Keep HTTP status message when response is not JSON.
      }
      throw new Error(message);
    }

    return response.json();
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      throw new Error('请求超时，请稍后重试');
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function post<T>(path: string, body: unknown, timeoutMs = 30000) {
  return apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    timeoutMs,
  });
}

export async function parseInput(
  userInput: string,
  mode: string = 'natural',
  provider?: string,
  temperature: number = 0.3,
  options: { pressureGoal?: any; allowedPlugins?: string[]; parsePreference?: string } = {},
) {
  return post('/generation/parse', {
    user_input: userInput,
    mode,
    provider,
    temperature,
    pressure_goal: options.pressureGoal,
    allowed_plugins: options.allowedPlugins,
    parse_preference: options.parsePreference,
  }, 120000);
}

export async function generateJMX(ir: any, validate: boolean = true, jmeterVersion: string = '5.0') {
  return post('/generation/generate', { ir, run_validation: validate, jmeter_version: jmeterVersion }, 60000);
}

export async function deriveQPS(targetQps: number, scenarioSteps?: any[], thinkTimeRange?: number[]) {
  return post('/generation/derive-qps', {
    target_qps: targetQps,
    scenario_steps: scenarioSteps,
    think_time_range: thinkTimeRange,
  });
}

export async function generatePreview(ir: any) {
  return post('/preview/generate', { ir }, 60000);
}

export async function updatePreview(ir: any, feedback: string, provider?: string, temperature: number = 0.3) {
  return post('/preview/update', { ir, feedback, provider, temperature }, 120000);
}

export async function checkDependencies(ir: any) {
  return post('/preview/dependency-check', { ir });
}

export async function validateJMX(jmx: string) {
  return post('/validation/validate', { jmx });
}

export async function checkReasonableness(ir: any) {
  return post('/validation/validate-ir-reasonable', { ir });
}

export async function getProviders() {
  return apiFetch('/config/providers');
}

export async function getComponents() {
  return apiFetch('/config/components');
}

export async function getJmeterVersions() {
  return apiFetch('/config/jmeter-versions');
}

export async function getStatus() {
  return apiFetch('/config/status');
}
