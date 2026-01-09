# Web Application Guide 🌐

The Web Testing Agent is now available as a beautiful web application! Access it through your browser instead of the command line.

## 🚀 Quick Start

### 1. Start the Web Server

```bash
npm run web
```

### 2. Open Your Browser

Navigate to:
```
http://localhost:3000
```

That's it! You now have a full web interface for testing.

## 📱 Features

### Beautiful Web Interface
- Clean, modern design with gradient backgrounds
- Responsive layout (works on mobile, tablet, desktop)
- Real-time progress updates
- Visual test results with screenshots

### Easy to Use
1. **Enter URL**: Type the website you want to test
2. **Describe Test**: Write what you want to test in plain English
3. **Click Run**: Watch the AI generate and execute tests
4. **View Results**: See detailed results with screenshots

### Example Scenarios (Click to Auto-Fill)
- Navigation testing
- Search functionality
- Form verification
- And more!

## 🎨 Web Interface Features

### Test Input Form
- **URL Field**: Enter any website URL
- **Scenario Field**: Describe your test in natural language
- **Headless Mode**: Toggle browser visibility
- **Example Scenarios**: Click to auto-fill common test patterns

### Real-Time Updates
- Animated loading spinner
- Progress messages
- Step-by-step execution tracking

### Results Display
- ✅ Success/Failure status badge
- 📊 Test statistics (duration, steps)
- 📝 Detailed step-by-step results
- 📸 Screenshot gallery
- Click screenshots to view full size

## 📖 How to Use

### Example 1: Test a Homepage

1. Enter URL: `https://github.com`
2. Enter Scenario: `Verify the homepage loads and has a navigation menu`
3. Click "Run Test"
4. Wait for results (usually 5-15 seconds)
5. View detailed results and screenshots

### Example 2: Test Search Functionality

1. Enter URL: `https://google.com`
2. Enter Scenario: `Search for 'web testing' and verify results appear`
3. Click "Run Test"
4. See each step executed with visual feedback

### Example 3: Test Form Submission

1. Enter URL: `https://example.com/contact`
2. Enter Scenario: `Fill in name with John Doe, email with test@example.com, and submit form`
3. Click "Run Test"
4. Watch the automation happen!

## 🎯 What Makes It Special

### AI-Powered
- Automatically generates test steps from your description
- Understands natural language
- No coding required!

### Visual Feedback
- See exactly what happened
- Screenshots at key points
- Error screenshots when tests fail

### User-Friendly
- No terminal needed
- Works in any browser
- Instant results

## 🔧 Configuration

### Change Port

Default port is 3000. To use a different port:

```bash
PORT=8080 npm run web
```

Then visit `http://localhost:8080`

### Headless Mode

- **Checked** (default): Faster, runs in background
- **Unchecked**: See the browser in action (if your system supports it)

## 📊 Understanding Results

### Success Indicators
- ✅ Green checkmarks
- "All Tests Passed" badge
- All steps completed

### Failure Indicators
- ❌ Red X marks
- "Test Failed" badge
- Error messages for each failed step
- Screenshots showing where it failed

### Test Information
- **Scenario**: What you asked to test
- **URL**: The website tested
- **Duration**: How long the test took
- **Steps Executed**: Number of test steps

## 🌟 Tips for Best Results

### Writing Good Scenarios

✅ **Good Examples:**
```
"Click the login button and verify login form appears"
"Fill email field with test@example.com and submit"
"Search for laptop and verify results contain products"
"Navigate to About page and check page title"
```

❌ **Avoid:**
```
"Test the site"
"Check if it works"
"Do everything"
```

### Be Specific
- Mention exact buttons, fields, or links
- Describe expected outcomes
- Use real values (emails, search terms, etc.)

### Break Complex Tests
Instead of:
```
"Test the entire checkout process"
```

Try:
```
"Add product to cart, go to checkout, and verify cart shows 1 item"
```

## 🚦 API Endpoints

The web app also provides a REST API:

### Start Test
```bash
POST /api/test
Body: {
  "url": "https://example.com",
  "scenario": "Test description",
  "headless": true
}
Response: {
  "testId": "1234567890",
  "message": "Test started"
}
```

### Get Test Status
```bash
GET /api/test/:testId
Response: {
  "status": "completed",
  "result": { ... }
}
```

### Health Check
```bash
GET /api/health
Response: {
  "status": "ok"
}
```

## 🎬 Screenshots

Screenshots are automatically saved in the `screenshots/` directory and displayed in the web interface.

- **Final Screenshot**: Taken when test completes successfully
- **Error Screenshots**: Taken when a step fails
- **Click to Enlarge**: Click any screenshot to open full size

## 🔄 Running Multiple Tests

1. Complete your first test
2. Click "Run Another Test" button
3. Form resets automatically
4. Enter new test details
5. Previous results are preserved in the browser

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Make sure dependencies are installed
npm install

# Check if port 3000 is already in use
# Use a different port
PORT=8080 npm run web
```

### Can't Access Webpage
- Make sure server is running (should see "Web Testing Agent is running!")
- Check you're using the correct URL: `http://localhost:3000`
- Try a different browser

### Tests Hang/Timeout
- Some websites may block automation
- Try increasing timeout in code
- Check network connectivity
- Try a simpler test scenario first

### No Screenshots Appear
- Screenshots require successful navigation
- Check if test reached screenshot step
- Look in `screenshots/` folder manually

## 📱 Mobile Access

The web interface is responsive and works on mobile devices!

1. Find your computer's local IP (e.g., 192.168.1.100)
2. Start server: `npm run web`
3. On mobile browser: `http://192.168.1.100:3000`

## 🎓 Advanced Usage

### Custom Timeout
Edit `src/server.ts` and change:
```typescript
timeout: 30000  // Change to desired milliseconds
```

### Custom Screenshot Behavior
Edit `src/server.ts`:
```typescript
screenshotOnError: true  // false to disable error screenshots
```

## 🎉 Benefits Over CLI

| Feature | CLI | Web App |
|---------|-----|---------|
| **Ease of Use** | Terminal commands | Click buttons |
| **Visual Feedback** | Text only | Screenshots + UI |
| **Accessibility** | Developers only | Anyone can use |
| **Results** | Text output | Rich visual display |
| **Sharing** | Copy terminal | Send link |
| **Learning Curve** | Need CLI knowledge | Intuitive interface |

## 🚀 Next Steps

1. Start the server: `npm run web`
2. Open browser to `http://localhost:3000`
3. Try the example scenarios
4. Create your own tests
5. Share with your team!

---

**Enjoy testing with a beautiful web interface!** 🎨✨
