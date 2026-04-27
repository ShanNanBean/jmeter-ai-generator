const API_BASE = '/api/v1';

export async function parseInput(userInput: string, mode: string = 'natural', provider?: string) {
  const response = await fetch(`${API_BASE}/generation/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput, mode, provider }),
  });
  if (!response.ok) throw new Error(`Parse failed: ${response.statusText}`);
  return response.json();
}

export async function generateJMX(ir: any, validate: boolean = true, jmeterVersion: string = '5.0') {
  const response = await fetch(`${API_BASE}/generation/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ir, validate, jmeter_version: jmeterVersion }),
  });
  if (!response.ok) throw new Error(`Generate failed: ${response.statusText}`);
  return response.json();
}

export async function generatePreview(ir: any) {
  const response = await fetch(`${API_BASE}/preview/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ir }),
  });
  if (!response.ok) throw new Error(`Preview failed: ${response.statusText}`);
  return response.json();
}

export async function updatePreview(ir: any, feedback: string, provider?: string) {
  const response = await fetch(`${API_BASE}/preview/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ir, feedback, provider }),
  });
  if (!response.ok) throw new Error(`Update failed: ${response.statusText}`);
  return response.json();
}

export async function checkDependencies(ir: any) {
  const response = await fetch(`${API_BASE}/preview/dependency-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ir }),
  });
  if (!response.ok) throw new Error(`Dependency check failed: ${response.statusText}`);
  return response.json();
}

export async function validateJMX(jmx: string) {
  const response = await fetch(`${API_BASE}/validation/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jmx }),
  });
  if (!response.ok) throw new Error(`Validation failed: ${response.statusText}`);
  return response.json();
}

export async function getProviders() {
  const response = await fetch(`${API_BASE}/config/providers`);
  if (!response.ok) throw new Error(`Get providers failed: ${response.statusText}`);
  return response.json();
}

export async function getComponents() {
  const response = await fetch(`${API_BASE}/config/components`);
  if (!response.ok) throw new Error(`Get components failed: ${response.statusText}`);
  return response.json();
}

export async function getJmeterVersions() {
  const response = await fetch(`${API_BASE}/config/jmeter-versions`);
  if (!response.ok) throw new Error(`Get versions failed: ${response.statusText}`);
  return response.json();
}

export async function getStatus() {
  const response = await fetch(`${API_BASE}/config/status`);
  if (!response.ok) throw new Error(`Status check failed: ${response.statusText}`);
  return response.json();
}