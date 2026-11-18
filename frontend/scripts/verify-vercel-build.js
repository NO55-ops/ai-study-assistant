#!/usr/bin/env node
'use strict';

/**
 * Reproduces the Vercel production build locally / in CI.
 *
 * Vercel runs `npm run build` (craco build) with CI=true, and Create React App
 * promotes every ESLint warning to an error in that mode. A developer shell with
 * CI unset (or CI=false) hides those warnings, which is how a hook-dependency
 * warning can reach Vercel and fail the deployment.
 *
 * This script pins CI=true regardless of the caller's environment, runs the real
 * production build, and additionally fails if the output still contains lint
 * warnings, so the check cannot pass while a warning slips through.
 */

const { spawnSync } = require('child_process');
const path = require('path');

const frontendDir = path.resolve(__dirname, '..');
const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';

const WARNING_PATTERNS = [
  /Compiled with warnings/i,
  /Treating warnings as errors/i,
  /^\s*Line \d+:\d+:.*react-hooks/im,
  /^\s*Line \d+:\d+:/m,
];

console.log('[verify-vercel-build] Running the production build with CI=true (warnings are errors).');
console.log('[verify-vercel-build] This takes about a minute; a clean build prints "Compiled successfully".');

const result = spawnSync(npmCommand, ['run', 'build'], {
  cwd: frontendDir,
  env: { ...process.env, CI: 'true' },
  encoding: 'utf8',
});

if (result.error) {
  console.error(`[verify-vercel-build] Could not start "npm run build": ${result.error.message}`);
  process.exit(1);
}

const stdout = result.stdout || '';
const stderr = result.stderr || '';
process.stdout.write(stdout);
process.stderr.write(stderr);

const output = `${stdout}\n${stderr}`;
const matchedWarnings = WARNING_PATTERNS.filter((pattern) => pattern.test(output));

if (result.status !== 0 || matchedWarnings.length > 0) {
  console.error('');
  console.error('[verify-vercel-build] FAILED: the production build is not clean.');
  console.error(
    '[verify-vercel-build] Fix every ESLint warning above (react-hooks/exhaustive-deps is the usual',
  );
  console.error(
    '[verify-vercel-build] culprit). Do not bypass this with CI=false, an eslint-disable comment or a',
  );
  console.error('[verify-vercel-build] weakened build configuration: Vercel will reject the same warning.');
  process.exit(result.status === 0 ? 1 : result.status || 1);
}

console.log('');
console.log('[verify-vercel-build] OK: production build completed with no ESLint warnings.');
