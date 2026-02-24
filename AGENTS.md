# AGENTS.md

## Cursor Cloud specific instructions

### Overview
This is a single-service Node.js/TypeScript application — an AI-powered web testing agent. It uses Playwright for browser automation and the Anthropic Claude API for test plan generation.

### Running the application
- **Web UI (Express server):** `npm run web` — serves on port 3000
- **CLI mode:** `npm run dev test -- --url <url> --scenario "<scenario>"`
- See `README.md` for full usage details and `QUICKSTART.md` for a step-by-step guide.

### Build
- `npm run build` — runs `tsc` to compile TypeScript to `dist/`

### Key caveats
- **ANTHROPIC_API_KEY required:** The `TestingAgent` constructor throws immediately if `ANTHROPIC_API_KEY` is not set in `.env` or passed in config. The Express server starts fine without it, but test submissions will fail at runtime. Copy `.env.example` to `.env` and add a valid key.
- **Playwright browsers:** After `npm install`, you must also run `npx playwright install --with-deps chromium` to install the Chromium browser binary and its OS-level dependencies. Without this, browser automation will fail.
- **ES Modules:** The project uses `"type": "module"` in `package.json`. All imports use `.js` extensions in TypeScript source files (standard ESM convention).
- **No linter configured:** There is no ESLint or Prettier configuration in this project. TypeScript strict mode (`tsc`) is the primary code quality check.
- **No automated test suite:** There are no unit/integration test files or test runner configured. The `npm run test` script is an alias for the CLI entry point, not a test framework.
