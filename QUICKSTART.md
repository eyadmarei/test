# Quick Start Guide

Get started with the Web Testing Agent in 5 minutes!

## Step 1: Install Dependencies

```bash
npm install
```

## Step 2: Install Playwright Browsers

```bash
npm run install-browsers
```

## Step 3: Set Up API Key

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Get your Anthropic API key from https://console.anthropic.com/

3. Add it to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Step 4: Run Your First Test

### Option A: Test Google Search (Quick Demo)

```bash
npm run dev test --url https://www.google.com --scenario "Search for 'web testing' and verify results appear"
```

### Option B: Use Example File

```bash
npm run dev test --file examples/example-google-search.json
```

### Option C: Custom Test

```bash
npm run dev test --url https://example.com --scenario "Your test scenario here"
```

## Step 5: View Results

After the test runs, check:
- Console output for step-by-step results
- `screenshots/` folder for visual evidence
- Test duration and success/failure status

## Example Test Scenarios

### E-commerce Testing
```bash
npm run dev test --url https://amazon.com --scenario "Search for 'laptop', click the first result, and verify product details are shown"
```

### Form Testing
```bash
npm run dev test --url https://httpbin.org/forms/post --scenario "Fill out the form and submit it"
```

### Navigation Testing
```bash
npm run dev test --url https://github.com --scenario "Click on Explore, then Topics, and verify the topics page loads"
```

## Options

### Run in visible browser mode
```bash
npm run dev test --url <url> --scenario "<scenario>" --headless false
```

### Increase timeout
```bash
npm run dev test --url <url> --scenario "<scenario>" --timeout 60000
```

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY is required"
**Solution**: Make sure you've created `.env` file with your API key

### Issue: Browser doesn't launch
**Solution**: Run `npm run install-browsers`

### Issue: Test fails on selector
**Solution**: Use `--headless false` to see what's happening in the browser

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check out more examples in the `examples/` folder
3. Create your own test scenario JSON files
4. Integrate into your CI/CD pipeline

Happy Testing! 🚀
