"""Workspace-refresh ownership follow-up (split from #6423).

The workspace create follow-ups in ``promptNewFile()`` / ``promptNewFolder()``
are bound to a repaint boundary captured *before* the name dialog, and
``loadDir()`` reports whether the navigation the caller made is still the one on
screen. Together they stop a create that was answered after a conversation
switch from opening the new path (or offering to add the folder) in the
conversation that replaced it.

The behavioural half runs the real helpers from ``static/sessions.js`` in Node;
the static half pins the contracts in ``static/workspace.js`` / ``static/ui.js``
that keep them wired.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SESSIONS_JS = (REPO_ROOT / "static/sessions.js").read_text(encoding="utf-8")
WORKSPACE_JS = (REPO_ROOT / "static/workspace.js").read_text(encoding="utf-8")
UI_JS = (REPO_ROOT / "static/ui.js").read_text(encoding="utf-8")

NODE = shutil.which("node")


def _function_block(src: str, name: str) -> str:
    marker = f"function {name}("
    start = src.find(marker)
    assert start != -1, f"{name}() not found"
    params_end = src.find("){", start)
    assert params_end != -1, f"{name}() body not found"
    brace = params_end + 1
    depth = 0
    for idx in range(brace, len(src)):
        ch = src[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start : idx + 1]
    raise AssertionError(f"{name}() body did not close")


def _boundary_helpers() -> str:
    return "\n".join(
        [
            _function_block(SESSIONS_JS, "_captureContextTransitionOwner"),
            _function_block(SESSIONS_JS, "_contextTransitionOwnerIsCurrent"),
            _function_block(SESSIONS_JS, "_captureWorkspaceRepaintBoundary"),
            _function_block(SESSIONS_JS, "_workspaceRepaintBoundaryIsCurrent"),
        ]
    )


def _run_node(script: str):
    assert NODE is not None, "node is required to run the boundary helpers"
    proc = subprocess.run(
        [NODE, "-e", script], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.skipif(NODE is None, reason="node is required to run the boundary helpers")
def test_repaint_boundary_tracks_the_conversation_directory_and_tree():
    # Every case captures the boundary while conversation A is on screen, then
    # applies exactly one change and asks whether the captured follow-up may run.
    cases = [
        {"name": "same conversation"},
        {"name": "other conversation", "thenSession": "B"},
        {"name": "switch already loading", "thenLoading": "B"},
        {"name": "directory moved", "thenDir": "/ws/a/sub"},
        {"name": "tree regenerated", "thenTreeGen": 7},
        {"name": "same sid new session object", "thenNewObject": True},
    ]
    script = """
const S = { session: null, activeProfile: 'default', currentDir: '/ws/a' };
let _loadingSessionId = null;
let _wsTreeGen = 0;
__HELPERS__
const sesA = { session_id: 'A', profile: 'default', workspace: '/ws/a' };
const sesB = { session_id: 'B', profile: 'default', workspace: '/ws/b' };
const out = [];
for (const c of __CASES__) {
  S.session = sesA;
  S.currentDir = '/ws/a';
  _wsTreeGen = 0;
  _loadingSessionId = null;
  const boundary = _captureWorkspaceRepaintBoundary();
  if (c.thenSession) S.session = c.thenSession === 'B' ? sesB : sesA;
  if (c.thenLoading) _loadingSessionId = c.thenLoading;
  if (c.thenDir) S.currentDir = c.thenDir;
  if (c.thenTreeGen !== undefined) _wsTreeGen = c.thenTreeGen;
  if (c.thenNewObject) S.session = Object.assign({}, sesA);
  out.push({ name: c.name, current: _workspaceRepaintBoundaryIsCurrent(boundary) });
}
console.log(JSON.stringify(out));
""".replace("__HELPERS__", _boundary_helpers()).replace("__CASES__", json.dumps(cases))
    results = {row["name"]: row["current"] for row in _run_node(script)}
    assert results["same conversation"] is True
    assert results["other conversation"] is False
    assert results["switch already loading"] is False
    assert results["directory moved"] is False
    assert results["tree regenerated"] is False
    assert results["same sid new session object"] is False


@pytest.mark.skipif(NODE is None, reason="node is required to run the boundary helpers")
def test_boundary_without_a_tree_generation_ignores_tree_bumps():
    script = """
const S = { session: { session_id: 'A', profile: 'default' }, activeProfile: 'default', currentDir: '/ws/a' };
let _loadingSessionId = null;
let _wsTreeGen;
__HELPERS__
const boundary = _captureWorkspaceRepaintBoundary();
_wsTreeGen = 99;
console.log(JSON.stringify({ current: _workspaceRepaintBoundaryIsCurrent(boundary) }));
""".replace("__HELPERS__", _boundary_helpers())
    assert _run_node(script)["current"] is True


def test_load_dir_only_supersedes_a_real_navigation():
    block = _function_block(WORKSPACE_JS, "loadDir")
    compact = block.replace(" ", "")
    assert "constrequestedPath=String(path||'.');" in compact
    # Same-path refreshes share the navigation generation; only a new directory
    # bumps it, so two overlapping refreshes of one directory both commit.
    assert (
        "if(typeof_wsNavigationPath==='undefined'||_wsNavigationPath!==requestedPath){"
        in compact
    )
    assert "++_wsNavigationGen;" in compact
    assert "constnavigationGen=_wsNavigationGen;" in compact
    # A newer reply for the same path still counts as committed for the caller.
    assert "constisSameNavigation=()=>!!S.session" in compact
    assert "if(isSameNavigation())returntrue;" in compact
    # Older replies may not repaint a listing a newer one already applied.
    assert "requestSeq>=(typeof_wsAppliedRequestSeq==='number'?_wsAppliedRequestSeq:0)" in compact
    assert "_wsAppliedRequestSeq=requestSeq;" in compact
    # loadDir reports whether the caller's navigation is still current.
    assert "returnfalse;" in compact
    assert "returntrue;" in compact


def test_create_installers_pin_the_boundary_before_the_dialog():
    for fn in ("promptNewFile", "promptNewFolder"):
        block = _function_block(UI_JS, fn)
        capture = block.find("_captureWorkspaceRepaintBoundary()")
        dialog = block.find("await showPromptDialog({")
        assert capture != -1, f"{fn} must capture a repaint boundary"
        assert dialog != -1, f"{fn} must prompt for a name"
        assert capture < dialog, f"{fn} must pin the owner before the dialog"
        # Re-check after the answer and before the write.
        after = block.find("_workspaceRepaintBoundaryIsCurrent(repaintBoundary)", dialog)
        write = block.find("await api('/api/file/create", dialog)
        assert after != -1 and write != -1
        assert after < write, f"{fn} must re-check the boundary before writing"
        # The write stays bound to the session captured before the dialog.
        assert "session_id:session.session_id" in block
        # Post-write follow-ups gate on the boundary and on the committed refresh.
        assert (
            "if(!refreshCommitted||!_workspaceRepaintBoundaryIsCurrent(repaintBoundary))return;"
            in block
        )


def test_offscreen_create_keeps_the_tree_refresh_only():
    for fn in ("promptNewFile", "promptNewFolder"):
        block = _function_block(UI_JS, fn)
        assert "if(!_contextTransitionOwnerIsCurrent(owner)" in block
        refresh = block.find("_refreshTreeAfterOffscreenWrite(session)")
        assert refresh != -1, f"{fn} must keep the offscreen tree refresh"
        # The offscreen branch returns before the toast or the file open.
        tail = block[refresh:]
        assert tail.find("return;") != -1, f"{fn} must return after the offscreen refresh"
        assert tail.find("return;") < tail.find("showToast(")
