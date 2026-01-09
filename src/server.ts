import express, { Request, Response } from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { TestingAgent } from './agents/TestingAgent.js';
import { TestScenario } from './types/index.js';
import fs from 'fs/promises';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));
app.use('/screenshots', express.static(path.join(__dirname, '../screenshots')));

// Store active tests
const activeTests = new Map<string, any>();

// Health check
app.get('/api/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', message: 'Web Testing Agent API is running' });
});

// Run test endpoint
app.post('/api/test', async (req: Request, res: Response) => {
  try {
    const { url, scenario, headless = true } = req.body;

    if (!url || !scenario) {
      return res.status(400).json({
        error: 'URL and scenario are required'
      });
    }

    const testScenario: TestScenario = {
      url,
      description: scenario
    };

    const testId = Date.now().toString();

    // Store test info
    activeTests.set(testId, {
      status: 'running',
      scenario: testScenario,
      startTime: Date.now()
    });

    // Run test in background
    const agent = new TestingAgent({
      headless: headless === true || headless === 'true',
      timeout: 30000,
      screenshotOnError: true
    });

    // Return immediately with test ID
    res.json({
      testId,
      message: 'Test started',
      scenario: testScenario
    });

    // Execute test
    try {
      const result = await agent.runTest(testScenario);
      activeTests.set(testId, {
        status: 'completed',
        result,
        scenario: testScenario,
        startTime: activeTests.get(testId)?.startTime,
        endTime: Date.now()
      });
    } catch (error) {
      activeTests.set(testId, {
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        scenario: testScenario,
        startTime: activeTests.get(testId)?.startTime,
        endTime: Date.now()
      });
    }
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    });
  }
});

// Get test status
app.get('/api/test/:testId', (req: Request, res: Response) => {
  const { testId } = req.params;
  const testInfo = activeTests.get(testId);

  if (!testInfo) {
    return res.status(404).json({ error: 'Test not found' });
  }

  res.json(testInfo);
});

// List all tests
app.get('/api/tests', (req: Request, res: Response) => {
  const tests = Array.from(activeTests.entries()).map(([id, info]) => ({
    id,
    ...info
  }));
  res.json({ tests });
});

// Get screenshot
app.get('/api/screenshot/:filename', async (req: Request, res: Response) => {
  try {
    const { filename } = req.params;
    const screenshotPath = path.join(__dirname, '../screenshots', filename);
    await fs.access(screenshotPath);
    res.sendFile(screenshotPath);
  } catch (error) {
    res.status(404).json({ error: 'Screenshot not found' });
  }
});

// Serve index.html for all other routes
app.get('*', (req: Request, res: Response) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.listen(PORT, () => {
  console.log(`\n🤖 Web Testing Agent is running!`);
  console.log(`\n📱 Open your browser and visit:`);
  console.log(`   http://localhost:${PORT}`);
  console.log(`\n🛑 Press Ctrl+C to stop\n`);
});
