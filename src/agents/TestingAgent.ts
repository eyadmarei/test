import Anthropic from '@anthropic-ai/sdk';
import { BrowserManager } from '../utils/browser.js';
import { Logger } from '../utils/logger.js';
import { TestScenario, TestResult, StepResult, AgentConfig, TestAction } from '../types/index.js';

export class TestingAgent {
  private anthropic: Anthropic;
  private browser: BrowserManager;
  private config: AgentConfig;

  constructor(config: AgentConfig = {}) {
    this.config = {
      headless: config.headless ?? true,
      timeout: config.timeout ?? 30000,
      screenshotOnError: config.screenshotOnError ?? true,
      apiKey: config.apiKey || process.env.ANTHROPIC_API_KEY
    };

    if (!this.config.apiKey) {
      throw new Error('ANTHROPIC_API_KEY is required. Set it in .env file or pass it in config.');
    }

    this.anthropic = new Anthropic({ apiKey: this.config.apiKey });
    this.browser = new BrowserManager();
  }

  async runTest(scenario: TestScenario): Promise<TestResult> {
    const startTime = Date.now();
    const result: TestResult = {
      success: true,
      scenario: scenario.description,
      url: scenario.url,
      steps: [],
      screenshots: [],
      duration: 0
    };

    try {
      Logger.heading(`Running Test: ${scenario.description}`);
      Logger.info(`URL: ${scenario.url}`);

      await this.browser.initialize(this.config.headless);

      const testPlan = await this.generateTestPlan(scenario);
      Logger.info(`Generated ${testPlan.length} test steps`);

      for (let i = 0; i < testPlan.length; i++) {
        const action = testPlan[i];
        Logger.step(`Step ${i + 1}/${testPlan.length}: ${this.describeAction(action)}`);

        const stepResult = await this.executeAction(action);
        result.steps.push(stepResult);

        if (!stepResult.success) {
          result.success = false;
          Logger.error(`Step failed: ${stepResult.error}`);

          if (this.config.screenshotOnError) {
            const screenshot = await this.browser.screenshot(`error-step-${i + 1}`);
            stepResult.screenshot = screenshot;
            result.screenshots?.push(screenshot);
            Logger.info(`Screenshot saved: ${screenshot}`);
          }
          break;
        }

        Logger.success('Step completed');
      }

      if (result.success) {
        const finalScreenshot = await this.browser.screenshot('final-result');
        result.screenshots?.push(finalScreenshot);
        Logger.info(`Final screenshot saved: ${finalScreenshot}`);
      }

    } catch (error) {
      result.success = false;
      result.error = error instanceof Error ? error.message : String(error);
      Logger.error(`Test failed: ${result.error}`);
    } finally {
      await this.browser.close();
      result.duration = Date.now() - startTime;
    }

    return result;
  }

  private async generateTestPlan(scenario: TestScenario): Promise<TestAction[]> {
    const prompt = `You are a web testing expert. Given a test scenario, generate a detailed list of actions to test the application.

Test Scenario:
URL: ${scenario.url}
Description: ${scenario.description}
${scenario.steps ? `Expected Steps:\n${scenario.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}` : ''}

Generate a JSON array of test actions. Each action should have this structure:
{
  "type": "navigate" | "click" | "fill" | "assert" | "wait" | "screenshot",
  "selector": "CSS selector (for click, fill, assert, wait)",
  "value": "value to fill or text to assert (for fill, assert)",
  "url": "URL to navigate to (for navigate)",
  "condition": "description of what to verify (for assert)",
  "timeout": milliseconds to wait (for wait)
}

Start with a navigate action to the URL, then perform the test steps.
For assertions, use the "assert" type and specify what should be visible or verified.
Be specific with CSS selectors (prefer data-testid, id, or unique class names).

Return ONLY the JSON array, no explanations.`;

    const message = await this.anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 2000,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = message.content[0];
    if (content.type !== 'text') {
      throw new Error('Unexpected response type from AI');
    }

    const jsonMatch = content.text.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      throw new Error('Could not parse test plan from AI response');
    }

    return JSON.parse(jsonMatch[0]);
  }

  private async executeAction(action: TestAction): Promise<StepResult> {
    const stepDescription = this.describeAction(action);

    try {
      switch (action.type) {
        case 'navigate':
          if (!action.url) throw new Error('URL required for navigate action');
          await this.browser.navigate(action.url);
          break;

        case 'click':
          if (!action.selector) throw new Error('Selector required for click action');
          await this.browser.waitForSelector(action.selector);
          await this.browser.click(action.selector);
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for navigation/changes
          break;

        case 'fill':
          if (!action.selector || !action.value) throw new Error('Selector and value required for fill action');
          await this.browser.waitForSelector(action.selector);
          await this.browser.fill(action.selector, action.value);
          break;

        case 'assert':
          if (!action.selector) throw new Error('Selector required for assert action');
          await this.browser.waitForSelector(action.selector, action.timeout || 5000);
          const text = await this.browser.getText(action.selector);
          if (action.value && !text.includes(action.value)) {
            throw new Error(`Expected text "${action.value}" not found. Got: "${text}"`);
          }
          break;

        case 'wait':
          const waitTime = action.timeout || 1000;
          await new Promise(resolve => setTimeout(resolve, waitTime));
          break;

        case 'screenshot':
          await this.browser.screenshot(action.value || 'step');
          break;

        default:
          throw new Error(`Unknown action type: ${(action as any).type}`);
      }

      return {
        step: stepDescription,
        success: true
      };
    } catch (error) {
      return {
        step: stepDescription,
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  private describeAction(action: TestAction): string {
    switch (action.type) {
      case 'navigate':
        return `Navigate to ${action.url}`;
      case 'click':
        return `Click on ${action.selector}`;
      case 'fill':
        return `Fill ${action.selector} with "${action.value}"`;
      case 'assert':
        return `Verify ${action.condition || action.selector}`;
      case 'wait':
        return `Wait ${action.timeout}ms`;
      case 'screenshot':
        return `Take screenshot`;
      default:
        return `Unknown action`;
    }
  }
}
