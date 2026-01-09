#!/usr/bin/env node

import { Command } from 'commander';
import { TestingAgent } from './agents/TestingAgent.js';
import { Logger } from './utils/logger.js';
import { TestScenario } from './types/index.js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const program = new Command();

program
  .name('web-testing-agent')
  .description('AI-powered web testing agent that can test applications based on natural language scenarios')
  .version('1.0.0');

program
  .command('test')
  .description('Run a test scenario')
  .option('-u, --url <url>', 'URL of the application to test')
  .option('-s, --scenario <scenario>', 'Test scenario description')
  .option('-f, --file <file>', 'JSON file containing test scenario')
  .option('--headless <boolean>', 'Run browser in headless mode (default: true)', 'true')
  .option('--timeout <ms>', 'Timeout in milliseconds', '30000')
  .action(async (options) => {
    try {
      let scenario: TestScenario;

      if (options.file) {
        const fileContent = await fs.readFile(options.file, 'utf-8');
        scenario = JSON.parse(fileContent);
      } else if (options.url && options.scenario) {
        scenario = {
          url: options.url,
          description: options.scenario
        };
      } else {
        Logger.error('Either provide --url and --scenario, or --file with a JSON test scenario');
        process.exit(1);
      }

      const agent = new TestingAgent({
        headless: options.headless === 'true',
        timeout: parseInt(options.timeout),
        screenshotOnError: true
      });

      const result = await agent.runTest(scenario);

      Logger.heading('Test Results');
      Logger.info(`Scenario: ${result.scenario}`);
      Logger.info(`URL: ${result.url}`);
      Logger.info(`Duration: ${result.duration}ms`);
      Logger.info(`Steps executed: ${result.steps.length}`);

      if (result.screenshots && result.screenshots.length > 0) {
        Logger.info(`Screenshots: ${result.screenshots.length}`);
        result.screenshots.forEach(s => Logger.info(`  - ${s}`));
      }

      if (result.success) {
        Logger.success('All tests passed!');
        process.exit(0);
      } else {
        Logger.error('Test failed!');
        if (result.error) {
          Logger.error(`Error: ${result.error}`);
        }

        result.steps.forEach((step, i) => {
          if (step.success) {
            Logger.success(`Step ${i + 1}: ${step.step}`);
          } else {
            Logger.error(`Step ${i + 1}: ${step.step}`);
            if (step.error) {
              Logger.error(`  ${step.error}`);
            }
            if (step.screenshot) {
              Logger.info(`  Screenshot: ${step.screenshot}`);
            }
          }
        });

        process.exit(1);
      }
    } catch (error) {
      Logger.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
  });

program
  .command('interactive')
  .description('Run agent in interactive mode')
  .action(async () => {
    Logger.heading('Web Testing Agent - Interactive Mode');
    Logger.info('This mode allows you to test web applications interactively.');
    Logger.info('Use the "test" command instead with --url and --scenario options.');
    Logger.info('Example: npm run dev test --url https://example.com --scenario "Test login functionality"');
  });

program.parse();
