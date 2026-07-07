import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const sourceDir = path.resolve(__dirname, '../../data/chats/fixture_pair1');
const destDir = path.resolve(__dirname, '../public/fixture');

function copyFolderSync(from, to) {
  if (!fs.existsSync(from)) {
    console.error(`Source directory does not exist: ${from}`);
    process.exit(1);
  }
  if (!fs.existsSync(to)) {
    fs.mkdirSync(to, { recursive: true });
  }
  fs.readdirSync(from).forEach(element => {
    const fromPath = path.join(from, element);
    const toPath = path.join(to, element);
    if (fs.lstatSync(fromPath).isFile()) {
      fs.copyFileSync(fromPath, toPath);
      console.log(`Copied ${element} to public/fixture/`);
    }
  });
}

console.log('Syncing fixture data...');
copyFolderSync(sourceDir, destDir);
console.log('Fixture data sync complete.');
