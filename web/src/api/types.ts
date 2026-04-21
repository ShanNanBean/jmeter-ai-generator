export interface IRDocument {
  testPlan: {
    name: string;
    variables?: { key: string; value: string }[];
  };
  threadGroups: {
    name: string;
    threads: number;
    rampUp: number;
    duration?: number;
    loop?: number;
  }[];
  scenarios: {
    name: string;
    threadGroup: string;
    steps: Step[];
    dataSources?: DataSource[];
    timers?: Timer[];
    controllers?: Controller[];
  }[];
  listeners?: Listener[];
}

export interface Step {
  type: string;
  name: string;
  method?: string;
  path?: string;
  body?: string;
  headers?: { key: string; value: string }[];
  assertions?: Assertion[];
  extractors?: Extractor[];
}

export interface Assertion {
  type: string;
  pattern?: string;
  field?: string;
  maxMs?: number;
}

export interface Extractor {
  type: string;
  variable: string;
  path?: string;
  regex?: string;
  defaultValue?: string;
}

export interface DataSource {
  type: string;
  file?: string;
  vars?: string[];
}

export interface Timer {
  type: string;
  rangeMs?: number[];
  delayMs?: number;
}

export interface Controller {
  type: string;
  name: string;
}

export interface Listener {
  type: string;
  name?: string;
  file?: string;
}

export interface ProviderInfo {
  name: string;
  model: string;
  type: string;
}

export interface ValidationIssue {
  severity: string;
  category: string;
  message: string;
  location?: string;
}

export interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
}