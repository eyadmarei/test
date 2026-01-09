export interface TestScenario {
  description: string;
  url: string;
  steps?: string[];
}

export interface TestAction {
  type: 'navigate' | 'click' | 'fill' | 'assert' | 'wait' | 'screenshot';
  selector?: string;
  value?: string;
  url?: string;
  condition?: string;
  timeout?: number;
}

export interface TestResult {
  success: boolean;
  scenario: string;
  url: string;
  steps: StepResult[];
  error?: string;
  screenshots?: string[];
  duration: number;
}

export interface StepResult {
  step: string;
  success: boolean;
  error?: string;
  screenshot?: string;
}

export interface AgentConfig {
  headless?: boolean;
  timeout?: number;
  screenshotOnError?: boolean;
  apiKey?: string;
}
