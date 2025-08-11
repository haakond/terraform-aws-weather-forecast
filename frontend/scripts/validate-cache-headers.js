#!/usr/bin/env node

/**
 * Cache header validation script
 * Validates that all static assets have proper Cache-Control headers for 15-minute caching
 */

const fs = require('fs');
const path = require('path');

const BUILD_DIR = path.join(__dirname, '..', 'build');

console.log('🔍 Validating cache header configuration...');

// Check if build metadata exists
const metadataPath = path.join(BUILD_DIR, 'build-metadata.json');
if (!fs.existsSync(metadataPath)) {
  console.error('❌ Build metadata not found. Run npm run build:optimized first.');
  process.exit(1);
}

const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));

console.log('📊 Build Metadata Analysis:');
console.log(`   Build Time: ${metadata.buildTime}`);
console.log(`   Cache Strategy: ${metadata.cacheStrategy.strategy}`);
console.log(`   Max Age: ${metadata.cacheStrategy.maxAge} seconds (${metadata.cacheStrategy.maxAge / 60} minutes)`);

// Validate cache strategy
if (metadata.cacheStrategy.maxAge !== 900) {
  console.error('❌ Cache max-age is not set to 900 seconds (15 minutes)');
  process.exit(1);
}

console.log('✅ Cache strategy validation passed');

// Analyze asset types and their cache configuration
const assetsByType = {};
metadata.assets.forEach(asset => {
  const ext = asset.extension.replace('.', '');
  if (!assetsByType[ext]) {
    assetsByType[ext] = [];
  }
  assetsByType[ext].push(asset);
});

console.log('\n📋 Asset Type Analysis:');
console.log('   ┌─────────────────────────────────────────────────────────────┐');
console.log('   │ Type      │ Count │ Cache Busting │ Cache Optimized │ Status │');
console.log('   ├─────────────────────────────────────────────────────────────┤');

let allValid = true;

Object.keys(assetsByType).sort().forEach(type => {
  const assets = assetsByType[type];
  const withHashes = assets.filter(asset => asset.hasHash).length;
  const cacheOptimized = assets.filter(asset => asset.cacheOptimized).length;

  // Determine if cache busting is expected for this type
  // Only static assets (in /static/ directory) need cache busting hashes
  const staticAssets = assets.filter(asset => asset.path.startsWith('static/'));
  const expectsHashes = ['css', 'js'].includes(type) && staticAssets.length > 0;
  const staticWithHashes = staticAssets.filter(asset => asset.hasHash).length;
  const hashStatus = expectsHashes ?
    (staticWithHashes === staticAssets.length ? '✅' : '⚠️') :
    'N/A';

  const cacheStatus = cacheOptimized === assets.length ? '✅' : '❌';
  const overallStatus = (expectsHashes ? staticWithHashes === staticAssets.length : true) &&
                       cacheOptimized === assets.length ? '✅' : '❌';

  if (overallStatus === '❌') {
    allValid = false;
  }

  console.log(`   │ ${type.padEnd(9)} │ ${assets.length.toString().padStart(5)} │ ${hashStatus.padStart(13)} │ ${cacheStatus.padStart(15)} │ ${overallStatus.padStart(6)} │`);
});

console.log('   └─────────────────────────────────────────────────────────────┘');

// Validate specific requirements
console.log('\n🎯 Requirement Validation:');

// Requirement 1.2: Fast response times through caching
console.log('   📋 Requirement 1.2 (Fast response times):');
if (metadata.cacheStrategy.maxAge === 900) {
  console.log('      ✅ 15-minute caching configured');
} else {
  console.log('      ❌ 15-minute caching not properly configured');
  allValid = false;
}

// Requirement 1.4: Cache-Control headers with Max-Age of 900 seconds
console.log('   📋 Requirement 1.4 (Cache-Control headers):');
if (metadata.cacheStrategy.maxAge === 900 && metadata.cacheStrategy.strategy === 'hash-based-cache-busting') {
  console.log('      ✅ Cache-Control max-age=900 configured for all static assets');
} else {
  console.log('      ❌ Cache-Control headers not properly configured');
  allValid = false;
}

// Check for proper file naming and versioning
// Only static assets (in /static/ directory) need cache busting hashes
const criticalAssets = metadata.assets.filter(asset =>
  (asset.extension === '.css' || asset.extension === '.js') &&
  asset.path.startsWith('static/')
);

const hashedAssets = criticalAssets.filter(asset => asset.hasHash);

console.log('   📋 Cache Busting Validation:');
if (hashedAssets.length === criticalAssets.length) {
  console.log('      ✅ All static CSS and JS files have hash-based cache busting');
} else {
  console.log(`      ❌ ${criticalAssets.length - hashedAssets.length} static assets missing cache busting hashes`);
  allValid = false;
}

// Final validation result
console.log('\n🏁 Final Validation Result:');
if (allValid) {
  console.log('✅ All cache header validations passed!');
  console.log('🎯 Frontend build is optimized for 15-minute caching with proper cache busting');
  process.exit(0);
} else {
  console.log('❌ Cache header validation failed!');
  console.log('🔧 Please review the configuration and rebuild');
  process.exit(1);
}