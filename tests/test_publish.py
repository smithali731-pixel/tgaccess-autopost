import json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import publish


def test_schedule_is_complete_and_times_never_repeat():
    s = json.loads(publish.SCHEDULE.read_text())
    assert len(s) == 90 and len({x["id"] for x in s}) == 90
    assert len({x["at"][11:16] for x in s}) == 90
    for x in s:
        assert (publish.ROOT / "media" / x["media"]).exists()
        assert x["type"] == "story" or len(x["caption"]) <= 2200


def run(tmp_path, monkeypatch, items, env, fail=()):
    monkeypatch.setattr(publish, "SCHEDULE", tmp_path / "s.json")
    monkeypatch.setattr(publish, "STATE", tmp_path / "st.json")
    (tmp_path / "s.json").write_text(json.dumps(items))
    for k in ("IG_USER_ID", "IG_TOKEN", "FB_PAGE_ID", "FB_PAGE_TOKEN", "TG_BOT_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    for k in env:
        monkeypatch.setenv(k, "x")
    calls = []
    def fake(plat):
        def f(item):
            calls.append((item["id"], plat))
            if plat in fail:
                raise RuntimeError("boom")
            return "1"
        return f
    monkeypatch.setattr(publish, "PLATFORMS", {p: (fake(p), v[1], v[2]) for p, v in publish.PLATFORMS.items()})
    monkeypatch.setattr(publish, "with_retries", lambda fn, item, label: fn(item))
    monkeypatch.setattr(publish, "call", lambda *a, **k: {"username": "test"})
    code = publish.main()
    return code, calls, json.loads((tmp_path / "st.json").read_text()) if (tmp_path / "st.json").exists() else None


def item(i, delta):
    at = datetime.now(timezone.utc) + delta
    return {"id": i, "at": at.isoformat(timespec="seconds"), "type": "feed", "media": "m.jpg", "caption": "c"}

ALL = ("IG_USER_ID", "IG_TOKEN", "FB_PAGE_ID", "FB_PAGE_TOKEN")


def test_nothing_is_published_without_secrets(tmp_path, monkeypatch):
    code, calls, _ = run(tmp_path, monkeypatch, [item("a", -timedelta(minutes=5))], ())
    assert code == 0 and calls == []


def test_due_goes_to_both_future_waits_and_old_is_skipped(tmp_path, monkeypatch):
    items = [item("due", -timedelta(minutes=5)), item("future", timedelta(hours=1)), item("old", -timedelta(hours=13))]
    code, calls, st = run(tmp_path, monkeypatch, items, ALL)
    assert code == 0 and sorted(calls) == [("due", "fb"), ("due", "ig")]
    assert set(st["skipped"]) == {"old:fb", "old:ig"}


def test_one_platform_failing_does_not_repeat_the_other(tmp_path, monkeypatch):
    items = [item("due", -timedelta(minutes=5))]
    code, calls, st = run(tmp_path, monkeypatch, items, ALL, fail=("fb",))
    assert code == 1 and set(st["done"]) == {"due:ig"}
    (tmp_path / "s.json").write_text(json.dumps(items))
    calls2 = []
    monkeypatch.setattr(publish, "PLATFORMS", {p: ((lambda it, p=p: calls2.append(p) or "2"), v[1], v[2]) for p, v in publish.PLATFORMS.items()})
    assert publish.main() == 0 and calls2 == ["fb"]


def test_page_token_is_fetched_from_meta_token(monkeypatch):
    for k in ("IG_TOKEN", "FB_PAGE_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("META_TOKEN", "user")
    monkeypatch.setenv("FB_PAGE_ID", "123")
    seen = []
    monkeypatch.setattr(publish, "call", lambda url, params=None, method="POST", headers=None: seen.append((url, params)) or {"access_token": "page"})
    publish.resolve_tokens()
    assert os.environ["IG_TOKEN"] == os.environ["FB_PAGE_TOKEN"] == "page"
    assert seen[0][0].endswith("/123") and seen[0][1]["access_token"] == "user"
