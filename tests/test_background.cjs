const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function event() { const handlers = []; return {handlers, addListener(fn) { handlers.push(fn); }}; }
const cloudFile = Object.fromEntries(['onAccountAdded', 'onAccountDeleted', 'onFileUpload', 'onFileUploadAbort', 'onFileDeleted'].map(n => [n, event()]));
cloudFile.getAllAccounts = async () => [];
cloudFile.getAccount = async id => ({id});
cloudFile.updateAccount = async () => {};
const saved = {enabledAccounts: {account: true}};
let output = [];
let failed = false;
let copied = [];
const browser = {
  cloudFile,
  storage: {local: {get: async () => saved, set: async data => Object.assign(saved, data)}},
  runtime: {id: 'test', getURL: p => `moz-extension://test/${p}`, onMessage: event(), connectNative() {
    const port = {onMessage: event(), onDisconnect: event(), disconnect() { for (const fn of port.onDisconnect.handlers) fn(); },
      postMessage(message) {
        copied.push(message.action);
        if (message.action === 'chunk') output.push(Buffer.from(message.data, 'base64'));
        const reply = {id: message.id, ok: !failed, configured: true, url: 'https://drive.google.com/open?id=synthetic'};
        queueMicrotask(() => port.onMessage.handlers.forEach(fn => fn(reply)));
      }};
    return port;
  }}
};
const context = {browser, Map, URL, Uint8Array, String, btoa: s => Buffer.from(s, 'binary').toString('base64')};
vm.runInNewContext(fs.readFileSync('extension/background.js', 'utf8'), context);
(async () => {
  const upload = cloudFile.onFileUpload.handlers[0];
  const bytes = Buffer.alloc(600000, 65);
  const file = {size: bytes.length, slice(a, b) { const x = bytes.subarray(a,b); return {arrayBuffer: async () => Uint8Array.from(x).buffer}; }};
  let result = await upload({id: 'account'}, {id: 1, name: 'sample.txt', data: file});
  assert.equal(result.url, 'https://drive.google.com/open?id=synthetic');
  assert.deepEqual(Buffer.concat(output), bytes);
  assert.equal(copied.filter(x => x === 'chunk').length, 3);
  saved.enabledAccounts.account = false;
  result = await upload({id: 'account'}, {id: 2, name: 'sample.txt', data: file});
  assert.ok(result.error);
  saved.enabledAccounts.account = true;
  failed = true;
  result = await upload({id: 'account'}, {id: 3, name: 'sample.txt', data: file});
  assert.ok(result.error);
  console.log('PASS: chunked Filelink upload and error/consent handling');
})().catch(error => { console.error(error); process.exitCode = 1; });
