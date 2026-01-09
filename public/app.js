// DOM Elements
const testForm = document.getElementById('testForm');
const submitBtn = document.getElementById('submitBtn');
const loadingState = document.getElementById('loadingState');
const resultsContainer = document.getElementById('resultsContainer');
const loadingMessage = document.getElementById('loadingMessage');
const progressFill = document.getElementById('progressFill');

// API Base URL
const API_URL = window.location.origin;

// Fill example scenario
window.fillExample = function(url, scenario) {
    document.getElementById('url').value = url;
    document.getElementById('scenario').value = scenario;
    // Smooth scroll to form
    testForm.scrollIntoView({ behavior: 'smooth' });
};

// Reset form
window.resetForm = function() {
    testForm.reset();
    resultsContainer.style.display = 'none';
    testForm.scrollIntoView({ behavior: 'smooth' });
};

// Handle form submission
testForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = document.getElementById('url').value;
    const scenario = document.getElementById('scenario').value;
    const headless = document.getElementById('headless').checked;

    // Hide results and show loading
    resultsContainer.style.display = 'none';
    loadingState.style.display = 'block';
    submitBtn.disabled = true;

    try {
        // Start the test
        loadingMessage.textContent = 'Sending test to agent...';
        const response = await fetch(`${API_URL}/api/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, scenario, headless })
        });

        if (!response.ok) {
            throw new Error('Failed to start test');
        }

        const { testId } = await response.json();

        loadingMessage.textContent = 'AI is generating test plan...';

        // Poll for results
        pollTestStatus(testId);
    } catch (error) {
        console.error('Error:', error);
        loadingState.style.display = 'none';
        submitBtn.disabled = false;
        alert('Failed to run test: ' + error.message);
    }
});

// Poll test status
async function pollTestStatus(testId) {
    const maxAttempts = 60; // 60 seconds max
    let attempts = 0;

    const interval = setInterval(async () => {
        attempts++;

        try {
            const response = await fetch(`${API_URL}/api/test/${testId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                clearInterval(interval);
                displayResults(data.result);
                loadingState.style.display = 'none';
                submitBtn.disabled = false;
            } else if (data.status === 'failed') {
                clearInterval(interval);
                loadingState.style.display = 'none';
                submitBtn.disabled = false;
                alert('Test failed: ' + data.error);
            } else if (data.status === 'running') {
                // Update loading message
                const messages = [
                    'AI is analyzing the test scenario...',
                    'Generating test steps...',
                    'Starting browser automation...',
                    'Executing test steps...',
                    'Capturing screenshots...',
                    'Almost done...'
                ];
                const messageIndex = Math.min(Math.floor(attempts / 5), messages.length - 1);
                loadingMessage.textContent = messages[messageIndex];
            }

            if (attempts >= maxAttempts) {
                clearInterval(interval);
                loadingState.style.display = 'none';
                submitBtn.disabled = false;
                alert('Test timeout - please try again');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000); // Poll every second
}

// Display test results
function displayResults(result) {
    // Set status
    const statusBadge = document.getElementById('resultStatus');
    if (result.success) {
        statusBadge.textContent = '✓ All Tests Passed';
        statusBadge.className = 'status-badge success';
    } else {
        statusBadge.textContent = '✗ Test Failed';
        statusBadge.className = 'status-badge failed';
    }

    // Set basic info
    document.getElementById('resultScenario').textContent = result.scenario;
    document.getElementById('resultUrl').textContent = result.url;
    document.getElementById('resultDuration').textContent = `${result.duration}ms`;
    document.getElementById('resultSteps').textContent = result.steps.length;

    // Display steps
    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '<h3>Test Steps</h3>';

    result.steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = `step-item ${step.success ? 'success' : 'failed'}`;

        const icon = step.success ? '✓' : '✗';
        const iconClass = step.success ? 'success' : 'failed';

        stepDiv.innerHTML = `
            <div class="step-header">
                <span class="step-icon">${icon}</span>
                <span>Step ${index + 1}: ${step.step}</span>
            </div>
            ${step.error ? `<div class="step-error">Error: ${step.error}</div>` : ''}
        `;

        stepsContainer.appendChild(stepDiv);
    });

    // Display screenshots
    const screenshotsContainer = document.getElementById('screenshotsContainer');
    if (result.screenshots && result.screenshots.length > 0) {
        screenshotsContainer.innerHTML = '<h3>Screenshots</h3><div class="screenshot-grid"></div>';
        const grid = screenshotsContainer.querySelector('.screenshot-grid');

        result.screenshots.forEach((screenshot, index) => {
            const filename = screenshot.split('/').pop();
            const screenshotDiv = document.createElement('div');
            screenshotDiv.className = 'screenshot-item';
            screenshotDiv.innerHTML = `
                <img src="/screenshots/${filename}" alt="Screenshot ${index + 1}" onclick="window.open(this.src)">
                <div class="screenshot-label">Screenshot ${index + 1}</div>
            `;
            grid.appendChild(screenshotDiv);
        });
    } else {
        screenshotsContainer.innerHTML = '';
    }

    // Show results
    resultsContainer.style.display = 'block';
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// Check API health on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_URL}/api/health`);
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.error('API not available:', error);
    }
});
