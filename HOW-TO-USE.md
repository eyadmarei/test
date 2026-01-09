# How to Use the Web Testing Agent

This guide shows you exactly how to access and use the testing agent.

## 🚀 Quick Start - 3 Easy Ways to Use

### Option 1: NPM Command (Recommended)

```bash
npm run dev test -- --url "https://example.com" --scenario "Your test description here"
```

**Real Examples:**
```bash
# Test a website loads
npm run dev test -- --url "https://github.com" --scenario "Verify the homepage loads"

# Test search functionality
npm run dev test -- --url "https://google.com" --scenario "Search for web testing and verify results"

# Test form submission
npm run dev test -- --url "https://example.com/contact" --scenario "Fill out contact form and submit"
```

### Option 2: Simple Node Script

```bash
node agent.js "https://example.com" "Your test scenario"
```

**Examples:**
```bash
node agent.js "https://github.com" "Click on Explore button"
node agent.js "https://amazon.com" "Search for laptop and click first result"
```

### Option 3: Bash Script (Linux/Mac)

```bash
./run-test.sh "https://example.com" "Your test scenario"
```

### Option 4: Use Pre-made Test Files

```bash
npm run dev test -- --file examples/example-google-search.json
npm run dev test -- --file examples/example-form-test.json
```

## 📋 Command Options

### Basic Command Structure
```bash
npm run dev test -- [OPTIONS]
```

### Available Options

| Option | Description | Example |
|--------|-------------|---------|
| `--url <url>` | Website URL to test | `--url https://example.com` |
| `--scenario <text>` | What to test (in plain English) | `--scenario "Test login form"` |
| `--file <path>` | Use a JSON test file | `--file my-test.json` |
| `--headless <true/false>` | Show/hide browser | `--headless false` |
| `--timeout <ms>` | Max time to wait | `--timeout 60000` |

### Combined Example
```bash
npm run dev test -- \
  --url "https://example.com" \
  --scenario "Test checkout process" \
  --headless false \
  --timeout 60000
```

## 💡 What Can You Test?

The agent understands plain English! Here are example scenarios:

### Navigation Tests
```bash
"Navigate to the about page"
"Click on the pricing link and verify it loads"
"Go to the contact page and check it displays"
```

### Form Tests
```bash
"Fill in the email field with test@example.com and submit"
"Complete the registration form with sample data"
"Enter username and password and click login"
```

### Search Tests
```bash
"Search for laptop and verify results appear"
"Type 'web testing' in search box and click search"
"Use the search feature to find documentation"
```

### Verification Tests
```bash
"Verify the homepage has a title"
"Check that the footer contains copyright text"
"Ensure the login button is visible"
```

### E-commerce Tests
```bash
"Add product to cart and verify cart count increases"
"Click on first product and check product details display"
"Navigate to shopping cart and verify items are listed"
```

## 📁 Creating Your Own Test Files

Create a JSON file (e.g., `my-test.json`):

```json
{
  "url": "https://your-website.com",
  "description": "Test description",
  "steps": [
    "Navigate to homepage",
    "Click on login button",
    "Fill in credentials",
    "Submit form",
    "Verify dashboard loads"
  ]
}
```

Run it:
```bash
npm run dev test -- --file my-test.json
```

## 🎯 Example Use Cases

### Test 1: Verify Website Loads
```bash
npm run dev test -- \
  --url "https://your-site.com" \
  --scenario "Verify the homepage loads successfully"
```

### Test 2: Test Login Flow
```bash
npm run dev test -- \
  --url "https://your-site.com/login" \
  --scenario "Enter email test@example.com, password demo123, and click login button"
```

### Test 3: Test Search Feature
```bash
npm run dev test -- \
  --url "https://your-site.com" \
  --scenario "Click search icon, type 'products', press enter, and verify results display"
```

### Test 4: See Browser in Action
```bash
npm run dev test -- \
  --url "https://your-site.com" \
  --scenario "Navigate through the main menu items" \
  --headless false
```

## 📊 Understanding Results

After running a test, you'll see:

```
✓ Running Test: Your scenario
ℹ URL: https://example.com
ℹ Generated 5 test steps
→ Step 1/5: Navigate to https://example.com
✓ Step completed
→ Step 2/5: Click on button
✓ Step completed
...

Test Results:
✓ All tests passed!
ℹ Duration: 3500ms
ℹ Screenshots: 1
  - ./screenshots/final-result-1234567890.png
```

## 🔧 Troubleshooting

### "ANTHROPIC_API_KEY is required"
**Solution:** Your `.env` file is already configured, but verify it exists:
```bash
cat .env
```

### "Browser not installed"
**Solution:** Run:
```bash
npm run install-browsers
```

### Test fails on specific selector
**Solution:** Use `--headless false` to see what's happening:
```bash
npm run dev test -- --url "https://example.com" --scenario "Your test" --headless false
```

### Timeout errors
**Solution:** Increase timeout:
```bash
npm run dev test -- --url "https://example.com" --scenario "Your test" --timeout 120000
```

## 🎓 Tips for Writing Good Scenarios

### ✅ Good Scenarios (Clear and Specific)
- "Click the login button and verify the form appears"
- "Fill in email field with test@example.com and submit"
- "Search for 'laptop' and verify results contain products"

### ❌ Bad Scenarios (Too Vague)
- "Test the website"
- "Check if it works"
- "Do stuff"

### 💡 Best Practices
1. Be specific about what to test
2. Mention exact text or values to use
3. Describe expected outcomes
4. Break complex tests into steps
5. Use descriptive names for JSON test files

## 🚦 Quick Reference

```bash
# Most common usage
npm run dev test -- --url "<URL>" --scenario "<WHAT TO TEST>"

# With file
npm run dev test -- --file path/to/test.json

# See browser
npm run dev test -- --url "<URL>" --scenario "<TEST>" --headless false

# Longer timeout
npm run dev test -- --url "<URL>" --scenario "<TEST>" --timeout 60000
```

## Need Help?

Run without arguments to see usage:
```bash
npm run dev test
node agent.js
./run-test.sh
```

---

**You're all set!** Just use any of the commands above to start testing. 🎉
