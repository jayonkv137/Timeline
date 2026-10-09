#!/usr/bin/env node
/**
 * COTRACE Standalone E2E Test Runner.
 *
 * Runs workspace interaction tests (smoke.cjs and refinement.cjs) against a live
 * FastAPI server URL adhering to STANDALONE_V1_PLAN §4 (Step S2.6).
 *
 * Automatically:
 * 1. Checks if a server is already healthy on WORKSPACE_URL (default http://127.0.0.1:8765).
 * 2. If not running, ensures library reference chats are seeded and spins up the server.
 * 3. Runs smoke.cjs and refinement.cjs with WORKSPACE_URL set.
 * 4. Gracefully stops the spawned server on completion or error.
 */

const { spawn, execFileSync } = require('node:child_process');
const http = require('node:http');
const path = require('node:path');
const fs = require('node:fs');

const REPO_ROOT = path.resolve(__dirname, '../..');
const DEFAULT_URL = 'http://127.0.0.1:8765';
const TARGET_URL = process.env.WORKSPACE_URL || DEFAULT_URL;

function getPythonPath() {
  const venvPython = path.join(REPO_ROOT, '.venv', 'bin', 'python');
  if (fs.existsSync(venvPython)) return venvPython;
  if (process.env.PYTHON) return process.env.PYTHON;
  return 'python3';
}

function checkHealth(urlStr) {
  return new Promise((resolve) => {
    try {
      const u = new URL(urlStr);
      const req = http.get(
        {
          hostname: u.hostname,
          port: u.port || 80,
          path: '/api/health',
          timeout: 1000,
        },
        (res) => {
          resolve(res.statusCode === 200);
        }
      );
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    } catch {
      resolve(false);
    }
  });
}

async function waitForServer(urlStr, timeoutMs = 12000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await checkHealth(urlStr)) return true;
    await new Promise((r) => setTimeout(r, 150));
  }
  return false;
}

async function main() {
  console.log(`==> COTRACE E2E runner: testing against ${TARGET_URL}`);
  let spawnedServer = null;

  const isRunning = await checkHealth(TARGET_URL);
  if (isRunning) {
    console.log(`==> Existing server active and healthy at ${TARGET_URL}. Reusing.`);
  } else {
    const python = getPythonPath();
    console.log(`==> Ensuring reference library is seeded (${python})...`);
    try {
      execFileSync(python, [path.join(REPO_ROOT, 'scripts', 'seed_library.py')], {
        cwd: REPO_ROOT,
        stdio: 'inherit',
      });
    } catch (err) {
      console.warn(`[WARN] seed_library warning: ${err.message}`);
    }

    const u = new URL(TARGET_URL);
    const port = u.port || '8765';
    const host = u.hostname || '127.0.0.1';
    console.log(`==> Starting FastAPI backend on ${host}:${port}...`);

    spawnedServer = spawn(
      python,
      ['-m', 'uvicorn', 'server.app:app', '--host', host, '--port', port, '--log-level', 'warning'],
      {
        cwd: REPO_ROOT,
        stdio: 'inherit',
        env: { ...process.env },
      }
    );

    spawnedServer.on('error', (err) => {
      console.error('Failed to spawn server process:', err);
    });

    const ready = await waitForServer(TARGET_URL);
    if (!ready) {
      console.error(`ERROR: Server failed to start and respond at ${TARGET_URL} within timeout.`);
      if (spawnedServer && !spawnedServer.killed) spawnedServer.kill('SIGKILL');
      process.exit(1);
    }
    console.log(`==> Server healthy at ${TARGET_URL}`);
  }

  const testEnv = {
    ...process.env,
    WORKSPACE_URL: TARGET_URL.endsWith('/') ? TARGET_URL : `${TARGET_URL}/`,
  };

  const cleanup = () => {
    if (spawnedServer && !spawnedServer.killed) {
      console.log('==> Stopping background test server...');
      try {
        spawnedServer.kill('SIGTERM');
      } catch {}
    }
  };

  process.on('SIGINT', () => { cleanup(); process.exit(130); });
  process.on('SIGTERM', () => { cleanup(); process.exit(143); });

  try {
    console.log('\n--> Running Suite 1: smoke.cjs...');
    execFileSync(process.execPath, [path.join(__dirname, 'smoke.cjs')], {
      cwd: REPO_ROOT,
      env: testEnv,
      stdio: 'inherit',
    });

    console.log('\n--> Running Suite 2: refinement.cjs...');
    execFileSync(process.execPath, [path.join(__dirname, 'refinement.cjs')], {
      cwd: REPO_ROOT,
      env: testEnv,
      stdio: 'inherit',
    });

    console.log('\n==> All E2E test suites passed against server URL!');
  } catch (err) {
    console.error('\nERROR: E2E test assertion or execution failed.');
    cleanup();
    process.exit(err.status || 1);
  } finally {
    cleanup();
  }
}

main().catch((err) => {
  console.error('Unhandled runner error:', err);
  process.exit(1);
});
