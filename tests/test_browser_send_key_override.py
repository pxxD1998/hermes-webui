"""Per-browser send-key override contract.

The shared ``send_key`` preference remains server-owned.  A browser-local
choice may override it for this browser without changing the shared value.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest


REPO = Path(__file__).resolve().parents[1]
BOOT_JS = (REPO / "static" / "boot.js").read_text(encoding="utf-8")
INDEX_HTML = (REPO / "static" / "index.html").read_text(encoding="utf-8")
I18N_JS = (REPO / "static" / "i18n.js").read_text(encoding="utf-8")
PANELS_JS = (REPO / "static" / "panels.js").read_text(encoding="utf-8")
STORAGE_KEY = "hermes-browser-send-key-override"


def _function_source(name: str) -> str:
    signature = f"function {name}("
    start = BOOT_JS.index(signature)
    brace = BOOT_JS.index("{", start)
    depth = 0
    for idx in range(brace, len(BOOT_JS)):
        char = BOOT_JS[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return BOOT_JS[start : idx + 1]
    raise AssertionError(f"could not extract {name}")


def _resolve(shared: object, override: object) -> str:
    resolver = _function_source("_resolveSendKeyPreference")
    script = "\n".join(
        [
            resolver,
            f"const result=_resolveSendKeyPreference({json.dumps(shared)},{json.dumps(override)});",
            "process.stdout.write(JSON.stringify(result));",
        ]
    )
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_browser_override_resolves_observable_send_key_behavior() -> None:
    cases = [
        ("enter", "", "enter"),
        ("shift+enter", "shared", "shift+enter"),
        ("shift+enter", "enter", "enter"),
        ("enter", "ctrl+enter", "ctrl+enter"),
        ("enter", "shift+enter", "shift+enter"),
        ("shift+enter", "unexpected", "shift+enter"),
        ("unexpected", "", "enter"),
        (None, None, "enter"),
    ]
    assert [_resolve(shared, override) for shared, override, _ in cases] == [
        expected for _, _, expected in cases
    ]


def test_preferences_expose_a_browser_local_override() -> None:
    assert 'id="settingsBrowserSendKey"' in INDEX_HTML
    for key in (
        "settings_label_browser_send_key",
        "settings_browser_send_key_use_shared",
        "settings_desc_browser_send_key",
    ):
        assert f'data-i18n="{key}"' in INDEX_HTML
        assert f"{key}:" in I18N_JS
    for value in ("shared", "enter", "ctrl+enter", "shift+enter"):
        assert f'<option value="{value}"' in INDEX_HTML


def test_browser_override_is_local_and_does_not_enter_server_payload() -> None:
    payload_body = PANELS_JS.split("function _preferencesPayloadFromUi(){", 1)[1].split(
        "function _speechPreferencesPayloadFromUi(){", 1
    )[0]
    assert "settingsBrowserSendKey" not in payload_body
    assert STORAGE_KEY in PANELS_JS
    assert "localStorage.setItem" in PANELS_JS
    assert "localStorage.removeItem" in PANELS_JS
    assert "window.addEventListener('storage'" in BOOT_JS


def test_boot_resolves_shared_setting_through_browser_override() -> None:
    assert "_applySendKeyPreference(s.send_key||'enter');" in BOOT_JS
    assert "window._sendKey=_resolveSendKeyPreference(" in BOOT_JS
    assert "hermes-pref-send_key-confirmed" in BOOT_JS
    assert "hermes-pref-send_key')" not in BOOT_JS
    assert STORAGE_KEY in BOOT_JS


def test_browser_override_isolated_persistent_and_drives_enter_behavior(base_url: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # pragma: no cover - dependency-missing path
        pytest.skip("playwright is unavailable; run `playwright install chromium`")

    browser_args = ["--no-sandbox", "--disable-dev-shm-usage"]

    def wait_for_value(page: Any, expression: str, expected: object) -> None:
        for _ in range(100):
            if page.evaluate(expression) == expected:
                return
            page.wait_for_timeout(50)
        assert page.evaluate(expression) == expected

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=browser_args)
        context_a = browser.new_context()
        context_b = browser.new_context()
        context_mobile = browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True,
            is_mobile=True,
        )
        page_a = None
        page_same_context = None
        page_mobile = None
        try:
            page_a = context_a.new_page()
            page_a.goto(base_url, wait_until="domcontentloaded")
            wait_for_value(page_a, "typeof window._applySendKeyPreference", "function")
            original_send_key = page_a.evaluate("api('/api/settings').then(s=>s.send_key||'enter')")
            page_a.evaluate(
                """async () => {
                  await api('/api/settings', {
                    method: 'POST',
                    body: JSON.stringify({send_key: 'shift+enter'}),
                  });
                  window._applySendKeyPreference('shift+enter');
                  await loadSettingsPanel();
                }"""
            )
            page_a.locator("#settingsBrowserSendKey").select_option("enter", force=True)
            assert page_a.evaluate("window._sendKey") == "enter"
            assert page_a.evaluate(f"localStorage.getItem('{STORAGE_KEY}')") == "enter"

            page_same_context = context_a.new_page()
            page_same_context.goto(base_url, wait_until="domcontentloaded")
            wait_for_value(page_same_context, "window._sendKey", "enter")

            page_a.evaluate("window.__sendKeyTestCount=0;window.send=()=>{window.__sendKeyTestCount+=1;};void 0")
            page_a.locator("#msg").fill("desktop message")
            page_a.locator("#msg").press("Enter")
            assert page_a.evaluate("window.__sendKeyTestCount") == 1

            page_b = context_b.new_page()
            page_b.goto(base_url, wait_until="domcontentloaded")
            wait_for_value(page_b, "window._sendKey", "shift+enter")
            assert page_b.evaluate(f"localStorage.getItem('{STORAGE_KEY}')") is None

            page_a.reload(wait_until="domcontentloaded")
            wait_for_value(page_a, "window._sendKey", "enter")
            awaitable = page_a.evaluate("loadSettingsPanel()")
            assert awaitable is None
            page_a.locator("#settingsBrowserSendKey").select_option("shared", force=True)
            assert page_a.evaluate("window._sendKey") == "shift+enter"
            assert page_a.evaluate(f"localStorage.getItem('{STORAGE_KEY}')") is None
            wait_for_value(page_same_context, "window._sendKey", "shift+enter")

            page_a.locator("#settingsBrowserSendKey").select_option("enter", force=True)
            wait_for_value(page_same_context, "window._sendKey", "enter")
            page_a.evaluate("localStorage.clear(); window._applySendKeyPreference(window._sharedSendKey)")
            wait_for_value(page_same_context, "window._sendKey", "shift+enter")
            assert page_a.evaluate("window._sendKey") == "shift+enter"

            page_a.evaluate(
                "window.__sendKeyTestCount=0;window.__sendKeyTestStacks=[];"
                "window.send=()=>{window.__sendKeyTestCount+=1;window.__sendKeyTestStacks.push(new Error().stack);};"
                "void 0")
            page_a.locator("#msg").fill("phone-style message")
            page_a.locator("#msg").press("Enter")
            assert page_a.evaluate("window.__sendKeyTestCount") == 0, page_a.evaluate(
                "window.__sendKeyTestStacks"
            )
            assert "\n" in page_a.locator("#msg").input_value()

            page_mobile = context_mobile.new_page()
            page_mobile.goto(base_url, wait_until="domcontentloaded")
            wait_for_value(page_mobile, "typeof window._applySendKeyPreference", "function")
            page_mobile.evaluate(
                """async () => {
                  await api('/api/settings', {
                    method: 'POST',
                    body: JSON.stringify({send_key: 'enter'}),
                  });
                  window._applySendKeyPreference('enter');
                  await loadSettingsPanel();
                }"""
            )
            assert page_mobile.evaluate("matchMedia('(pointer:coarse)').matches") is True
            page_mobile.locator("#settingsBrowserSendKey").select_option("enter", force=True)
            page_mobile.evaluate("window.__sendKeyTestCount=0;window.send=()=>{window.__sendKeyTestCount+=1;};void 0")
            page_mobile.locator("#msg").fill("explicit mobile override")
            page_mobile.locator("#msg").press("Enter")
            assert page_mobile.evaluate("window.__sendKeyTestCount") == 1

            page_a.evaluate(
                """() => {
                  const originalSetItem=Storage.prototype.setItem;
                  Storage.prototype.setItem=()=>{throw new Error('storage disabled');};
                  window.__restoreStorageSetItem=()=>{Storage.prototype.setItem=originalSetItem;};
                }"""
            )
            page_a.locator("#settingsBrowserSendKey").select_option("enter", force=True)
            assert page_a.locator("#settingsBrowserSendKey").input_value() == "shared"
            assert page_a.evaluate("window._sendKey") == "shift+enter"
            page_a.evaluate("window.__restoreStorageSetItem(); void 0")
        finally:
            original_send_key = locals().get("original_send_key", "enter")
            try:
                if page_a is not None:
                    page_a.evaluate(
                        "async originalSendKey => {await api('/api/settings', {method: 'POST', "
                        "body: JSON.stringify({send_key: originalSendKey})}); "
                        "return api('/api/settings');}",
                        original_send_key,
                    )
            finally:
                if page_same_context is not None:
                    page_same_context.close()
                if page_mobile is not None:
                    page_mobile.close()
                context_a.close()
                context_b.close()
                context_mobile.close()
                browser.close()


def test_browser_override_fails_closed_on_unconfirmed_shared_changes(base_url: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # pragma: no cover - dependency-missing path
        pytest.skip("playwright is unavailable; run `playwright install chromium`")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context()
        page = context.new_page()
        original_send_key = "enter"
        try:
            page.goto(base_url, wait_until="domcontentloaded")
            original_send_key = page.evaluate("api('/api/settings').then(s=>s.send_key||'enter')")
            page.evaluate(
                """async () => {
                  await api('/api/settings', {
                    method: 'POST',
                    body: JSON.stringify({send_key: 'shift+enter'}),
                  });
                  window._applySendKeyPreference('shift+enter');
                  localStorage.setItem('hermes-pref-send_key-confirmed', 'shift+enter');
                  await loadSettingsPanel();
                  _saveBrowserSendKeyOverride('enter');
                }"""
            )

            def fail_settings_post(route: Any) -> None:
                if route.request.method == "POST":
                    route.abort()
                else:
                    route.continue_()

            page.route("**/api/settings", fail_settings_post)
            page.locator("#settingsSendKey").select_option("enter", force=True)
            page.locator("#settingsBrowserSendKey").select_option("shared", force=True)
            assert page.evaluate("window._sendKey") == "shift+enter"
            page.wait_for_timeout(500)
            assert page.evaluate("window._sendKey") == "shift+enter"
            assert page.evaluate("localStorage.getItem('hermes-pref-send_key-confirmed')") == "shift+enter"
            page.unroute("**/api/settings", fail_settings_post)

            def fail_settings_get(route: Any) -> None:
                if route.request.method == "GET":
                    route.abort()
                else:
                    route.continue_()

            page.route("**/api/settings", fail_settings_get)
            page.reload(wait_until="domcontentloaded")
            for _ in range(100):
                if page.evaluate("window._sendKey") == "shift+enter":
                    break
                page.wait_for_timeout(50)
            assert page.evaluate("window._sendKey") == "shift+enter"
            page.unroute("**/api/settings", fail_settings_get)
        finally:
            try:
                page.evaluate(
                    "async originalSendKey => api('/api/settings', {method: 'POST', "
                    "body: JSON.stringify({send_key: originalSendKey})})",
                    original_send_key,
                )
            finally:
                context.close()
                browser.close()
