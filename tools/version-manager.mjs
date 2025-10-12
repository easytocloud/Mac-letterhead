#!/usr/bin/env node
import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import path from 'path';
import process from 'process';
import semver from 'semver';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const FILES = {
  init: path.join(repoRoot, 'letterhead_pdf', '__init__.py'),
  serverJson: path.join(repoRoot, 'server.json'),
  makefile: path.join(repoRoot, 'Makefile'),
  uvLock: path.join(repoRoot, 'uv.lock'),
};

async function readCurrentVersion() {
  const initContent = await readFile(FILES.init, 'utf8');
  const match = initContent.match(/__version__\s*=\s*"([^"]+)"/);
  if (!match) {
    throw new Error('Unable to determine current version from letterhead_pdf/__init__.py');
  }
  return match[1];
}

async function setVersion(newVersion) {
  if (!semver.valid(newVersion)) {
    throw new Error(`Invalid semantic version: ${newVersion}`);
  }

  await updateInit(newVersion);
  await updateServerJson(newVersion);
  await updateMakefile(newVersion);
  await bumpUvLockRevision();

  return newVersion;
}

async function updateInit(version) {
  const initContent = await readFile(FILES.init, 'utf8');
  const updated = initContent.replace(/(__version__\s*=\s*")[^"]+(")/, `$1${version}$2`);
  await writeFile(FILES.init, updated);
}

async function updateServerJson(version) {
  try {
    const serverContent = await readFile(FILES.serverJson, 'utf8');
    const updated = serverContent.replace(/("version"\s*:\s*")[^"]+(")/g, `$1${version}$2`);
    await writeFile(FILES.serverJson, updated);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

async function updateMakefile(version) {
  try {
    const makeContent = await readFile(FILES.makefile, 'utf8');
    if (!/VERSION\s*:=/.test(makeContent)) {
      return;
    }
    const updated = makeContent.replace(/(VERSION\s*:=\s*)[^\s]+/, `$1${version}`);
    await writeFile(FILES.makefile, updated);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

async function bumpUvLockRevision() {
  try {
    const uvContent = await readFile(FILES.uvLock, 'utf8');
    if (!/revision\s*=/.test(uvContent)) {
      return;
    }
    const updated = uvContent.replace(/^(revision\s*=\s*)(\d+)/m, (_match, prefix, value) => {
      const next = Number.parseInt(value, 10) + 1;
      return `${prefix}${next}`;
    });
    await writeFile(FILES.uvLock, updated);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

async function handleGet() {
  const version = await readCurrentVersion();
  process.stdout.write(`${version}\n`);
}

async function handleSet(target) {
  if (!target) {
    throw new Error('Missing version to set. Usage: node tools/version-manager.mjs set <version>');
  }
  const version = await setVersion(target);
  process.stdout.write(`${version}\n`);
}

async function handleBump(typeOrVersion, options) {
  const current = await readCurrentVersion();
  const { preid } = options;

  if (typeOrVersion && semver.valid(typeOrVersion)) {
    const version = await setVersion(typeOrVersion);
    process.stdout.write(`${version}\n`);
    return;
  }

  const releaseType = typeOrVersion || 'patch';
  const allowedTypes = new Set(['major', 'minor', 'patch', 'prerelease', 'premajor', 'preminor', 'prepatch']);
  if (!allowedTypes.has(releaseType)) {
    throw new Error(
      `Invalid release type "${releaseType}". Use one of: ${Array.from(allowedTypes).join(', ')}`
    );
  }

  const next = semver.inc(current, releaseType, preid);
  if (!next) {
    throw new Error(`Unable to calculate next version from ${current} using "${releaseType}"`);
  }

  const version = await setVersion(next);
  process.stdout.write(`${version}\n`);
}

function parseOptions(args) {
  const options = {};
  const positionals = [];

  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    if (value.startsWith('--preid=')) {
      options.preid = value.split('=')[1];
    } else if (value === '--preid') {
      options.preid = args[i + 1];
      i += 1;
    } else {
      positionals.push(value);
    }
  }

  return { positionals, options };
}

async function main() {
  const [, , command, ...rest] = process.argv;
  const { positionals, options } = parseOptions(rest);

  try {
    switch (command) {
      case 'get':
        await handleGet();
        break;
      case 'set':
        await handleSet(positionals[0]);
        break;
      case 'bump':
        await handleBump(positionals[0], options);
        break;
      default:
        throw new Error(
          'Usage: node tools/version-manager.mjs <get|set|bump> [major|minor|patch|...] [--preid beta]'
        );
    }
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

main();
