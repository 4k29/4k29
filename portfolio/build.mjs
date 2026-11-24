import { createHash } from 'node:crypto';
import { resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
import { readdir, readFile, rm, writeFile } from 'node:fs/promises';

const source = name => readFile(new URL('./src/' + name, import.meta.url), 'utf8');
const destination = process.argv[2] ? pathToFileURL(resolve(process.argv[2]) + sep) : new URL('./dist/', import.meta.url);
const output = name => new URL(name, destination);
const [template, ...modules] = await Promise.all(
  ['index.html', 'content.js', 'motion.js', 'app.js'].map(source),
);

// These three local modules use named declarations and one-line imports.
const code = modules.map(module => module.replace(/^import .*;\n/gm, '').replace(/^export /gm, '')).join('\n');
const bundle = '(() => {\n"use strict";\n' + code + '\n})();\n';
const bundleName = 'portfolio-' + createHash('sha256').update(bundle).digest('hex').slice(0, 12) + '.js';

const html = template.replace('<!-- portfolio-script -->', `<script defer src="./${bundleName}"></script>`);
await writeFile(output(bundleName), bundle);
await writeFile(output('index.html'), html);
const stale = (await readdir(output(''))).filter(name=>/^portfolio-[a-f0-9]{12}\.js$/.test(name) && name!==bundleName);
await Promise.all(stale.map(name=>rm(output(name))));
