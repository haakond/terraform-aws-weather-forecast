/**
 * CloudWatch Synthetics Canary for Weather Forecast App
 * End-to-end testing of the complete user journey
 */

const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');

// Configuration from environment variables
const websiteUrl = process.env.WEBSITE_URL || '${website_url}';
const apiUrl = process.env.API_URL || '${api_url}';

const pageLoadBlueprint = async function () {
    // Configure Synthetics
    const syntheticsConfig = synthetics.getConfiguration();
    syntheticsConfig.setConfig({
        screenshotOnStepStart: true,
        screenshotOnStepSuccess: true,
        screenshotOnStepFailure: true,
        includeRequestHeaders: true,
        includeResponseHeaders: true,
        restrictedHeaders: [],
        restrictedUrlParameters: []
    });

    let page = await synthetics.getPage();

    // Test 1: Page Load and Basic Structure
    await synthetics.executeStep('pageLoad', async function () {
        log.info('Testing page load for URL: ' + websiteUrl);

        const response = await page.goto(websiteUrl, {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        if (!response) {
            throw new Error('Failed to load page');
        }

        if (response.status() !== 200) {
            throw new Error(`Page returned status ${response.status()}`);
        }

        // Verify page title
        const title = await page.title();
        if (!title.includes('Weather Forecast')) {
            throw new Error(`Unexpected page title: ${title}`);
        }

        // Verify main container is present
        const mainContainer = await page.$('.weather-container');
        if (!mainContainer) {
            throw new Error('Main weather container not found');
        }

        log.info('Page load test passed');
    });

    // Test 2: Weather Data Loading
    await synthetics.executeStep('weatherDataLoading', async function () {
        log.info('Testing weather data loading');

        // Wait for weather cards to load
        await page.waitForSelector('.weather-card', { timeout: 30000 });

        // Get all weather cards
        const weatherCards = await page.$$('.weather-card');

        if (weatherCards.length !== 4) {
            throw new Error(`Expected 4 weather cards, found ${weatherCards.length}`);
        }

        // Verify each city has weather data
        const expectedCities = ['Oslo', 'Paris', 'London', 'Barcelona'];

        for (let i = 0; i < weatherCards.length; i++) {
            const card = weatherCards[i];

            // Check city name
            const cityName = await card.$eval('.city-name', el => el.textContent);
            if (!expectedCities.includes(cityName)) {
                throw new Error(`Unexpected city: ${cityName}`);
            }

            // Check temperature is displayed
            const temperature = await card.$eval('.temperature', el => el.textContent);
            if (!temperature || !temperature.includes('°C')) {
                throw new Error(`Temperature not properly displayed for ${cityName}`);
            }

            // Check weather icon is present
            const weatherIcon = await card.$('.weather-icon');
            if (!weatherIcon) {
                throw new Error(`Weather icon not found for ${cityName}`);
            }

            // Check weather description is present
            const description = await card.$eval('.weather-description', el => el.textContent);
            if (!description) {
                throw new Error(`Weather description not found for ${cityName}`);
            }
        }

        log.info('Weather data loading test passed');
    });

    // Test 3: API Health Check
    await synthetics.executeStep('apiHealthCheck', async function () {
        log.info('Testing API health endpoint');

        const healthUrl = `${apiUrl}/health`;

        const response = await page.goto(healthUrl, {
            waitUntil: 'networkidle0',
            timeout: 15000
        });

        if (response.status() !== 200) {
            throw new Error(`Health endpoint returned status ${response.status()}`);
        }

        // Get response body
        const responseText = await page.evaluate(() => document.body.textContent);

        let healthData;
        try {
            healthData = JSON.parse(responseText);
        } catch (e) {
            throw new Error(`Invalid JSON response from health endpoint: ${responseText}`);
        }

        if (healthData.status !== 'healthy') {
            throw new Error(`API health check failed: ${healthData.status}`);
        }

        if (!healthData.timestamp) {
            throw new Error('Health response missing timestamp');
        }

        if (!healthData.version) {
            throw new Error('Health response missing version');
        }

        log.info('API health check passed');
    });

    // Test 4: Responsive Design
    await synthetics.executeStep('responsiveDesign', async function () {
        log.info('Testing responsive design');

        // Go back to main page
        await page.goto(websiteUrl, { waitUntil: 'networkidle0' });

        // Test desktop view (1920x1080)
        await page.setViewport({ width: 1920, height: 1080 });
        await page.waitForTimeout(1000);

        let weatherContainer = await page.$('.weather-container');
        if (!weatherContainer) {
            throw new Error('Weather container not visible on desktop');
        }

        // Test tablet view (768x1024)
        await page.setViewport({ width: 768, height: 1024 });
        await page.waitForTimeout(1000);

        let weatherCards = await page.$$('.weather-card');
        if (weatherCards.length !== 4) {
            throw new Error('Not all weather cards visible on tablet');
        }

        // Test mobile view (375x667)
        await page.setViewport({ width: 375, height: 667 });
        await page.waitForTimeout(1000);

        weatherCards = await page.$$('.weather-card');
        if (weatherCards.length !== 4) {
            throw new Error('Not all weather cards visible on mobile');
        }

        // Reset to desktop view
        await page.setViewport({ width: 1920, height: 1080 });

        log.info('Responsive design test passed');
    });

    // Test 5: Performance Check
    await synthetics.executeStep('performanceCheck', async function () {
        log.info('Testing performance metrics');

        // Navigate to main page and measure performance
        const response = await page.goto(websiteUrl, { waitUntil: 'networkidle0' });

        // Get performance metrics
        const performanceMetrics = await page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
            };
        });

        // Performance thresholds
        if (performanceMetrics.domContentLoaded > 3000) {
            log.warn(`DOM Content Loaded took ${performanceMetrics.domContentLoaded}ms (threshold: 3000ms)`);
        }

        if (performanceMetrics.loadComplete > 5000) {
            log.warn(`Load Complete took ${performanceMetrics.loadComplete}ms (threshold: 5000ms)`);
        }

        if (performanceMetrics.firstContentfulPaint > 2000) {
            log.warn(`First Contentful Paint took ${performanceMetrics.firstContentfulPaint}ms (threshold: 2000ms)`);
        }

        log.info(`Performance metrics - DOM: ${performanceMetrics.domContentLoaded}ms, Load: ${performanceMetrics.loadComplete}ms, FCP: ${performanceMetrics.firstContentfulPaint}ms`);
    });

    // Test 6: Accessibility Check
    await synthetics.executeStep('accessibilityCheck', async function () {
        log.info('Testing basic accessibility features');

        await page.goto(websiteUrl, { waitUntil: 'networkidle0' });

        // Check for alt text on images
        const imagesWithoutAlt = await page.$$eval('img', imgs =>
            imgs.filter(img => !img.alt || img.alt.trim() === '').length
        );

        if (imagesWithoutAlt > 0) {
            log.warn(`Found ${imagesWithoutAlt} images without alt text`);
        }

        // Check for proper heading structure
        const h1Count = await page.$$eval('h1', h1s => h1s.length);
        if (h1Count === 0) {
            throw new Error('Page missing main heading (h1)');
        }

        // Check for semantic HTML elements
        const mainElement = await page.$('main');
        if (!mainElement) {
            log.warn('Page missing main semantic element');
        }

        log.info('Accessibility check completed');
    });

    log.info('All end-to-end tests completed successfully');
};

exports.handler = async () => {
    return await synthetics.executeStep('weatherAppE2ETest', pageLoadBlueprint);
};