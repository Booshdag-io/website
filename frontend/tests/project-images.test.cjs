const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

// Exercise the public API mapper with API data; no server or live network needed.
async function mappedImage(preview, avatar = 'https://avatars.githubusercontent.com/u/1') {
  const source = fs.readFileSync(path.join(__dirname, '../src/lib/data/projects.ts'), 'utf8');
  const output = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const exports = {};
  vm.runInNewContext(output, {
    exports, URL, console,
    require(name) {
      if (name === '../api') return { apiFetch: async () => ({ result: [
        { name: 'project', image_url: preview, owner: { avatar_url: avatar } },
      ] }) };
      if (name === './developers') return { PER_PAGE: 20 };
      throw new Error(`Unexpected dependency: ${name}`);
    },
  });
  return (await exports.getProjects())[0].img;
}

test('supported GitHub and local asset previews are selected', async () => {
  for (const url of ['https://github.com/user-attachments/assets/123',
    'https://raw.githubusercontent.com/a/b/main/image.png', '/assets/projects/example.png']) {
    assert.equal(await mappedImage(url), url);
  }
});

test('unsupported hosts, protocols, ports and local paths use the avatar', async () => {
  const avatar = 'https://avatars.githubusercontent.com/u/1';
  for (const url of ['https://img.shields.io/badge/test.svg', 'http://github.com/image',
    '//evil.example/image.png', '/outside/image.png', 'https://github.com:8443/image',
    'https://user:password@github.com/image', 'https://github.com.evil.example/image']) {
    assert.equal(await mappedImage(url), avatar, url);
  }
});

test('missing preview and avatar retain the existing placeholder', async () => {
  assert.equal(await mappedImage(undefined, ''), '/assets/projects/miniyotas.png');
});
