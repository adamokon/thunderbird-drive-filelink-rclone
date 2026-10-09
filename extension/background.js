"use strict";
const HOST = "org.thunderbird.drive_filelink_rclone";
const LIMIT = 5 * 1024 ** 3;
const CHUNK = 256 * 1024;
const active = new Map();

function nativeSession() {
  const port = browser.runtime.connectNative(HOST);
  const pending = new Map();
  let seq = 0;
  let closed = false;
  port.onMessage.addListener(message => {
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    if (message.ok) request.resolve(message);
    else request.reject(new Error(message.error || "Błąd lokalnego programu."));
  });
  port.onDisconnect.addListener(() => {
    closed = true;
    const error = new Error(port.error?.message || "Lokalny program został rozłączony.");
    for (const request of pending.values()) request.reject(error);
    pending.clear();
  });
  return {
    call(action, fields = {}) {
      if (closed) return Promise.reject(new Error("Połączenie jest zamknięte."));
      return new Promise((resolve, reject) => {
        const id = ++seq;
        pending.set(id, {resolve, reject});
        try { port.postMessage({id, action, ...fields}); }
        catch (error) { pending.delete(id); reject(error); }
      });
    },
    close() { closed = true; port.disconnect(); }
  };
}

async function checkStatus() {
  const session = nativeSession();
  try { return await session.call("status"); }
  finally { session.close(); }
}

async function refreshAccounts(knownReady) {
  const saved = await browser.storage.local.get("enabledAccounts");
  const enabled = saved.enabledAccounts || {};
  let ready = typeof knownReady === "boolean" ? knownReady : false;
  if (typeof knownReady !== "boolean") {
    try { ready = (await checkStatus()).configured; } catch (_) { /* Not installed/configured yet. */ }
  }
  for (const account of await browser.cloudFile.getAllAccounts()) {
    await browser.cloudFile.updateAccount(account.id, {
      configured: Boolean(enabled[account.id] && ready), uploadSizeLimit: LIMIT
    });
  }
}

browser.runtime.onMessage.addListener(async (message, sender) => {
  if (sender.id !== browser.runtime.id || !sender.url || new URL(sender.url).pathname !== new URL(browser.runtime.getURL("management.html")).pathname) {
    return undefined;
  }
  if (message.action === "check") {
    const result = await checkStatus();
    await refreshAccounts(result.configured);
    return result;
  }
  if (message.action === "reauthorize") {
    const session = nativeSession();
    try { return await session.call("reauthorize"); }
    finally { session.close(); }
  }
  if (message.action === "enable" || message.action === "disable") {
    const account = await browser.cloudFile.getAccount(message.accountId);
    if (!account) throw new Error("Nie znaleziono konta Filelink.");
    if (message.action === "enable" && !(await checkStatus()).configured) {
      throw new Error("Najpierw skonfiguruj OAuth w rclone.");
    }
    const saved = await browser.storage.local.get("enabledAccounts");
    const enabledAccounts = saved.enabledAccounts || {};
    enabledAccounts[account.id] = message.action === "enable";
    await browser.storage.local.set({enabledAccounts});
    await refreshAccounts();
    return {ok: true};
  }
  return undefined;
});

browser.cloudFile.onAccountAdded.addListener(() => refreshAccounts());
browser.cloudFile.onAccountDeleted.addListener(async accountId => {
  const saved = await browser.storage.local.get("enabledAccounts");
  const enabledAccounts = saved.enabledAccounts || {};
  delete enabledAccounts[accountId];
  await browser.storage.local.set({enabledAccounts});
});

browser.cloudFile.onFileUpload.addListener(async (account, fileInfo) => {
  const saved = await browser.storage.local.get("enabledAccounts");
  if (!saved.enabledAccounts?.[account.id]) return {error: "Włącz konto w ustawieniach Filelink."};
  const key = `${account.id}:${fileInfo.id}`;
  const session = nativeSession();
  const state = {session, aborted: false};
  active.set(key, state);
  try {
    const file = fileInfo.data;
    if (file.size > LIMIT) throw new Error("Maksymalny rozmiar pliku to 5 GiB.");
    await session.call("start", {name: fileInfo.name, size: file.size, public: true});
    for (let offset = 0; offset < file.size; offset += CHUNK) {
      if (state.aborted) return {aborted: true};
      const bytes = new Uint8Array(await file.slice(offset, offset + CHUNK).arrayBuffer());
      let binary = "";
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      await session.call("chunk", {data: btoa(binary)});
    }
    const result = await session.call("finish");
    if (state.aborted) return {aborted: true};
    return {url: result.url, templateInfo: {service_name: "Google Drive"}};
  } catch (error) {
    return state.aborted ? {aborted: true} : {error: error.message};
  } finally {
    active.delete(key);
    session.close();
  }
});
browser.cloudFile.onFileUploadAbort.addListener((account, fileId) => {
  const state = active.get(`${account.id}:${fileId}`);
  if (state) { state.aborted = true; state.session.close(); }
});
// Do not revoke a link which may already have been sent or reused in another mail.
browser.cloudFile.onFileDeleted.addListener(() => {});
refreshAccounts().catch(() => {});
