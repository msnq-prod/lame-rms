#!/usr/bin/env node

import { spawn } from 'node:child_process';

const steps = [
  {
    name: 'Playwright browser binaries',
    command: 'npx',
    args: ['playwright', 'install'],
  },
  {
    name: 'Playwright system dependencies',
    command: 'npx',
    args: ['playwright', 'install-deps'],
  },
];

function runStep({ name, command, args }) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'inherit', shell: false });

    child.on('error', (error) => {
      reject(new Error(`Failed to launch ${command}: ${error.message}`));
    });

    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(' ')} exited with code ${code}`));
      }
    });
  }).then(() => {
    process.stdout.write(`✔ ${name} installed\n`);
  });
}

async function main() {
  for (const step of steps) {
    process.stdout.write(`→ Installing ${step.name}\n`);
    await runStep(step);
  }
}

main().catch((error) => {
  process.stderr.write(`✖ ${error.message}\n`);
  process.exitCode = 1;
});
