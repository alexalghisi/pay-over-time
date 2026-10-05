import { defineConfig, devices } from "@playwright/test";

const python = process.env.PYTHON ?? "python";
const chromiumPath = process.env.PLAYWRIGHT_CHROMIUM_PATH;

export default defineConfig({
    testDir: "e2e",
    fullyParallel: false,
    retries: process.env.CI ? 1 : 0,
    use: {
        baseURL: "http://localhost:4173",
        trace: "retain-on-failure",
        ...(chromiumPath ? { launchOptions: { executablePath: chromiumPath } } : {}),
    },
    projects: [
        { name: "desktop", use: { ...devices["Desktop Chrome"] } },
        { name: "mobile", use: { ...devices["Pixel 7"] } },
    ],
    webServer: [
        {
            command: `${python} -m uvicorn paylater.main:create_app --factory --port 8000`,
            url: "http://localhost:8000/healthz",
            env: {
                PAYLATER_DATABASE_URL: "sqlite+pysqlite:///:memory:",
                PAYLATER_CORS_ORIGINS: "http://localhost:4173",
            },
            reuseExistingServer: !process.env.CI,
        },
        {
            command: "npm run build && npm run preview -- --port 4173 --strictPort",
            url: "http://localhost:4173",
            env: { VITE_API_URL: "http://localhost:8000" },
            reuseExistingServer: !process.env.CI,
        },
    ],
});
