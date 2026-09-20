#!/usr/bin/env node

import { execFile } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { promisify } from 'node:util';

const run = promisify(execFile);
const root = process.cwd();
const statePath = path.join(root, '_feishu-upload-state.json');
const contentFile = '_feishu-upload-current.md';

const targetFolder = 'GkEKfSf4klXx6DdlPJ7ceKBInEq';
const parents = {
  notes: 'FKpyfrGCSlKZjWd4UFkcB73Rnzg',
  source: 'IhrbfwM86l3Uz6dHf9rcD2ZXnKc',
  textbook: 'RiQ5f4Sh0ltTumdPteQceR4AnMg',
  root: targetFolder,
};

const groups = [
  { key: 'notes', label: '精简笔记', folder: 'docs/notes' },
  { key: 'source', label: '课件原文', folder: 'docs/source' },
  { key: 'textbook', label: '教材原文', folder: 'docs/textbook' },
];

const env = {
  ...process.env,
  LARKSUITE_CLI_NO_UPDATE_NOTIFIER: '1',
  LARKSUITE_CLI_NO_SKILLS_NOTIFIER: '1',
};

function toPosix(value) {
  return value.split(path.sep).join('/');
}

function listMarkdownFiles(folder) {
  const absoluteFolder = path.join(root, folder);
  const files = [];

  function walk(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const child = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        walk(child);
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        files.push(toPosix(path.relative(root, child)));
      }
    }
  }

  walk(absoluteFolder);
  return files.sort();
}

function titleOf(file) {
  const content = fs.readFileSync(path.join(root, file), 'utf8');
  const match = content.match(/^#\s+(.+?)\s*$/m);
  if (!match) {
    throw new Error(`No H1 title found in ${file}`);
  }
  return match[1];
}

function transformMarkdown(file) {
  const source = fs.readFileSync(path.join(root, file), 'utf8');
  let content = source.replace(/<!--[\s\S]*?-->/g, '');

  content = content.replace(
    /<span\s+class=["']course-highlight["']\s*>([\s\S]*?)<\/span>/g,
    (_, inner) => `**${inner.trim()}**`,
  );
  content = content.replace(/<\/?span\b[^>]*>/g, '');

  content = content.replace(
    /\[([^\]]+)\]\((?:\/(?:notes|source|textbook|guide)\/[^)]*)\)/g,
    '$1',
  );

  const errors = [];
  content = content.replace(
    /(!\[[^\]]*\]\()(\.\/[^)]+)(\))/g,
    (whole, prefix, destination, suffix) => {
      const absolute = path.resolve(path.dirname(path.join(root, file)), destination);
      const relative = toPosix(path.relative(root, absolute));
      if (relative.startsWith('../') || path.isAbsolute(relative)) {
        errors.push(`${file}: image leaves workspace: ${destination}`);
        return whole;
      }
      if (!fs.existsSync(absolute)) {
        errors.push(`${file}: image not found: ${destination}`);
        return whole;
      }
      return `${prefix}<@./${relative}>${suffix}`;
    },
  );

  if (/<\/?span\b/i.test(content)) {
    errors.push(`${file}: unresolved span tag`);
  }
  if (/<!--/.test(content)) {
    errors.push(`${file}: unresolved HTML comment`);
  }
  if (/\]\(\/(?:notes|source|textbook|guide)\//.test(content)) {
    errors.push(`${file}: unresolved site link`);
  }

  return { content, errors };
}

function tasks() {
  const result = [];
  for (const group of groups) {
    for (const file of listMarkdownFiles(group.folder)) {
      result.push({
        file,
        title: titleOf(file),
        parent: parents[group.key],
        group: group.key,
        label: group.label,
      });
    }
  }

  result.push({
    file: 'docs/guide/introduction.md',
    title: '项目介绍',
    parent: parents.root,
    group: 'root',
    label: '项目介绍',
  });

  return result;
}

function loadState() {
  if (!fs.existsSync(statePath)) {
    return {};
  }
  return JSON.parse(fs.readFileSync(statePath, 'utf8'));
}

function saveState(state) {
  const temporary = `${statePath}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(state, null, 2)}\n`);
  fs.renameSync(temporary, statePath);
}

async function lark(args, input, timeoutMs = 10 * 60 * 1000) {
  const { stdout, stderr } = await run('lark-cli', args, {
    cwd: root,
    env,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
    timeout: timeoutMs,
    input,
  });
  return { stdout, stderr };
}

async function listFolder(folderToken) {
  const files = [];
  let pageToken = '';

  do {
    const params = { folder_token: folderToken, page_size: 200 };
    if (pageToken) {
      params.page_token = pageToken;
    }
    const { stdout } = await lark([
      'drive',
      'files',
      'list',
      '--params',
      JSON.stringify(params),
      '--as',
      'user',
      '--format',
      'json',
    ]);
    const response = JSON.parse(stdout);
    if (response.ok !== true) {
      throw new Error(`Unexpected drive files list response for ${folderToken}`);
    }
    files.push(...response.data.files);
    pageToken = response.data.has_more ? response.data.next_page_token : '';
  } while (pageToken);

  return files;
}

function retryable(error) {
  const message = String(error.message ?? error);
  return /rate limit|too many requests|temporar|network|conflict|timeout/i.test(message);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function createDocument(task, content) {
  fs.writeFileSync(path.join(root, contentFile), content);
  const args = [
    'docs',
    '+create',
    '--doc-format',
    'markdown',
    '--title',
    task.title,
    '--content',
    `@./${contentFile}`,
    '--parent-token',
    task.parent,
    '--as',
    'user',
    '--format',
    'json',
  ];

  try {
    for (let attempt = 1; attempt <= 4; attempt += 1) {
      try {
        const { stdout, stderr } = await lark(args);
        const response = JSON.parse(stdout);
        if (response.ok !== true) {
          throw new Error(`Upload failed for ${task.file}: ${stderr || stdout}`);
        }
        return response.data.document;
      } catch (error) {
        if (attempt === 4 || !retryable(error)) {
          throw error;
        }
        process.stderr.write(`Retryable failure for ${task.file}, attempt ${attempt}: ${error.message}\n`);
        await sleep(attempt * 3000);
      }
    }
  } finally {
    fs.rmSync(path.join(root, contentFile), { force: true });
  }
}

function printCheck() {
  const allTasks = tasks();
  let imageCount = 0;
  const errors = [];

  for (const task of allTasks) {
    const { content, errors: fileErrors } = transformMarkdown(task.file);
    errors.push(...fileErrors);
    imageCount += (content.match(/<@\.\/[^>]+>/g) ?? []).length;
  }

  const counts = allTasks.reduce((accumulator, task) => {
    accumulator[task.group] = (accumulator[task.group] ?? 0) + 1;
    return accumulator;
  }, {});

  console.log(JSON.stringify({
    ok: errors.length === 0,
    documents: allTasks.length,
    counts,
    images: imageCount,
    errors,
  }, null, 2));

  if (errors.length > 0) {
    process.exitCode = 1;
  }
}

function tableOfContents(state, allTasks) {
  const lines = ['# 总目录', '', '## 项目入口', ''];
  const intro = state['docs/guide/introduction.md'];
  if (intro) {
    lines.push(`- [项目介绍](${intro.url})`, '');
  }

  for (const group of groups) {
    lines.push(`## ${group.label}`, '');
    lines.push(`- [打开「${group.label}」文件夹](https://my.feishu.cn/drive/folder/${parents[group.key]})`, '');
    for (const task of allTasks.filter((item) => item.group === group.key)) {
      const uploaded = state[task.file];
      if (!uploaded) {
        throw new Error(`Missing upload state for ${task.file}`);
      }
      lines.push(`- [${task.title}](${uploaded.url})`);
    }
    lines.push('');
  }

  return `${lines.join('\n')}\n`;
}

async function upload() {
  const state = loadState();
  const allTasks = tasks();
  const remote = new Map();

  for (const [key, token] of Object.entries(parents)) {
    remote.set(key, await listFolder(token));
  }

  for (const task of allTasks) {
    if (state[task.file]) {
      continue;
    }

    const existing = remote
      .get(task.group)
      ?.find((file) => file.name === task.title && file.type === 'docx');
    if (existing) {
      state[task.file] = {
        token: existing.token,
        url: existing.url,
        title: existing.name,
        source: 'existing',
      };
      saveState(state);
      console.log(`Existing: ${task.title}`);
      continue;
    }

    const { content, errors } = transformMarkdown(task.file);
    if (errors.length > 0) {
      throw new Error(errors.join('\n'));
    }

    console.log(`Uploading ${allTasks.findIndex((item) => item.file === task.file) + 1}/${allTasks.length}: ${task.title}`);
    const document = await createDocument(task, content);
    state[task.file] = {
      token: document.document_id,
      url: document.url,
      title: task.title,
      source: 'uploaded',
    };
    saveState(state);
    console.log(`Uploaded: ${task.title}`);
  }

  if (!state['#table-of-contents']) {
    const tocTask = {
      file: '#table-of-contents',
      title: '总目录',
      parent: parents.root,
      group: 'root',
    };
    const existingToc = remote.get('root')?.find((file) => file.name === '总目录' && file.type === 'docx');
    if (existingToc) {
      state['#table-of-contents'] = {
        token: existingToc.token,
        url: existingToc.url,
        title: existingToc.name,
        source: 'existing',
      };
    } else {
      const document = await createDocument(tocTask, tableOfContents(state, allTasks));
      state['#table-of-contents'] = {
        token: document.document_id,
        url: document.url,
        title: tocTask.title,
        source: 'uploaded',
      };
    }
    saveState(state);
  }

  console.log(`Done: ${Object.keys(state).length} entries in state.`);
}

const mode = process.argv[2] ?? 'check';
if (mode === 'check') {
  printCheck();
} else if (mode === 'upload') {
  await upload();
} else {
  console.error('Usage: node _feishu-upload.mjs [check|upload]');
  process.exitCode = 2;
}
