import fs from 'node:fs';
import path from 'node:path';

const filePath = path.resolve(process.cwd(), 'src', 'shared', 'api', 'auth.ts');
if (!fs.existsSync(filePath)) {
  console.error(`Missing SDK file at ${filePath}`);
  process.exit(1);
}
const content = fs.readFileSync(filePath, 'utf8');
const fragments = [
  'export interface TokenPair',
  'export async function login',
  'export async function refreshToken',
  'export async function setupMfa',
];
const missing = fragments.filter((fragment) => !content.includes(fragment));
if (missing.length > 0) {
  console.error('Lint failed: missing fragments');
  missing.forEach((fragment) => console.error(`  - ${fragment}`));
  process.exit(1);
}
console.log('frontend lint check passed');
