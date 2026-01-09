# Web Testing Agent

An AI-powered web testing agent that can test applications based on natural language test scenarios. Built with TypeScript, Playwright, and Claude AI.

## Features

- **Natural Language Testing**: Describe your test scenarios in plain English
- **AI-Powered Test Generation**: Claude AI automatically generates detailed test steps
- **Browser Automation**: Uses Playwright for reliable web automation
- **Screenshot Capture**: Automatic screenshots on errors and test completion
- **Flexible Input**: Accept test scenarios via CLI arguments or JSON files
- **Detailed Reporting**: Comprehensive test results with step-by-step execution details

## Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

3. Install Playwright browsers:

```bash
npm run install-browsers
```

4. Set up your environment:

```bash
cp .env.example .env
```

5. Add your Anthropic API key to `.env`:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Command Line Interface

#### Test with URL and scenario:

```bash
npm run dev test --url https://example.com --scenario "Test the login functionality"
```

#### Test with a JSON file:

```bash
npm run dev test --file examples/example-google-search.json
```

#### Options:

- `--url <url>`: URL of the application to test
- `--scenario <scenario>`: Natural language description of the test
- `--file <file>`: JSON file containing test scenario
- `--headless <boolean>`: Run browser in headless mode (default: true)
- `--timeout <ms>`: Timeout in milliseconds (default: 30000)

### JSON Test Scenario Format

```json
{
  "url": "https://example.com",
  "description": "Test scenario description",
  "steps": [
    "Step 1 description",
    "Step 2 description",
    "Step 3 description"
  ]
}
```

## Examples

### Example 1: Google Search Test

```bash
npm run dev test --url https://www.google.com --scenario "Search for 'Playwright testing' and verify results are displayed"
```

### Example 2: Form Testing

```bash
npm run dev test --file examples/example-form-test.json
```

### Example 3: E-commerce Site Testing

```bash
npm run dev test --url https://shop.example.com --scenario "Add a product to cart, proceed to checkout, and verify cart total"
```

## How It Works

1. **Test Scenario Input**: You provide a URL and describe what you want to test
2. **AI Planning**: Claude AI analyzes your scenario and generates detailed test steps
3. **Browser Automation**: Playwright executes the test steps in a real browser
4. **Result Capture**: Screenshots and detailed results are saved
5. **Report Generation**: Comprehensive test report is displayed

## Architecture

```
src/
├── agents/
│   └── TestingAgent.ts      # Main AI testing agent
├── utils/
│   ├── browser.ts            # Browser automation utilities
│   └── logger.ts             # Logging utilities
├── types/
│   └── index.ts              # TypeScript type definitions
└── index.ts                  # CLI entry point
```

## Test Actions

The agent can perform the following actions:

- **navigate**: Navigate to a URL
- **click**: Click on an element
- **fill**: Fill in a form field
- **assert**: Verify element presence or content
- **wait**: Wait for a specified time
- **screenshot**: Capture a screenshot

## Configuration

Create a `.env` file with the following:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### AgentConfig Options

```typescript
{
  headless: boolean,          // Run browser in headless mode (default: true)
  timeout: number,            // Global timeout in ms (default: 30000)
  screenshotOnError: boolean, // Take screenshot on error (default: true)
  apiKey: string              // Anthropic API key (or use env var)
}
```

## Development

### Build the project:

```bash
npm run build
```

### Run in development mode:

```bash
npm run dev test --url <url> --scenario "<scenario>"
```

### Run compiled version:

```bash
npm start test --url <url> --scenario "<scenario>"
```

## Screenshots

Screenshots are automatically saved in the `./screenshots` directory:
- Error screenshots: `error-step-{number}-{timestamp}.png`
- Final screenshot: `final-result-{timestamp}.png`

## Error Handling

- Failed steps are logged with detailed error messages
- Screenshots are captured on errors (when enabled)
- Test execution stops at the first failed step
- Comprehensive error reporting in the final output

## Requirements

- Node.js 18+
- Anthropic API key
- Internet connection for AI and browser automation

## Use Cases

- **Regression Testing**: Quickly verify key user flows
- **Smoke Testing**: Test critical functionality after deployments
- **Exploratory Testing**: Generate test ideas from natural language descriptions
- **CI/CD Integration**: Automate testing in your deployment pipeline
- **Documentation**: Test scenarios can serve as living documentation

## Limitations

- Requires valid CSS selectors for element interaction
- Complex dynamic sites may require additional wait times
- AI-generated test plans may need refinement for edge cases
- Screenshots consume disk space over time

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT
