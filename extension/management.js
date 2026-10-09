"use strict";
const accountId = new URL(location.href).searchParams.get("accountId");
const status = document.getElementById("status");
async function check() {
  try {
    const result = await browser.runtime.sendMessage({action: "check"});
    status.textContent = result.configured ? "Lokalny program i konfiguracja OAuth są gotowe. Połączenie z Google zostanie sprawdzone przy przesyłaniu." : result.message;
  } catch (_) { status.textContent = "Lokalny program jest niedostępny. Uruchom instalator projektu."; }
}
document.getElementById("check").addEventListener("click", check);
document.getElementById("reauthorize").addEventListener("click", async () => {
  try {
    await browser.runtime.sendMessage({action: "reauthorize"});
    status.textContent = "Otworzono Terminal. Dokończ logowanie w przeglądarce Google, potem kliknij Sprawdź połączenie.";
  } catch (_) { status.textContent = "Nie udało się otworzyć logowania. Uruchom ponownie instalator pomocnika."; }
});
document.getElementById("save").addEventListener("click", async () => {
  try {
    const enabled = document.getElementById("consent").checked;
    await browser.runtime.sendMessage({action: enabled ? "enable" : "disable", accountId});
    status.textContent = enabled ? "Konto Filelink włączone." : "Konto Filelink wyłączone.";
  } catch (error) { status.textContent = error.message; }
});
browser.storage.local.get("enabledAccounts").then(saved => {
  document.getElementById("consent").checked = Boolean(saved.enabledAccounts?.[accountId]);
});
check();
