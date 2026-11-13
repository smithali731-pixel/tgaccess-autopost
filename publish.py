"""Publish due TG Access posts to Instagram (@tgaccess1) and the Facebook page (tgaccess).

The two accounts are NOT linked, so every item is published to each one separately and
tracked separately in state.json: a failure on one platform never repeats the other.
Meta reads the media straight from this public repository.

Environment: IG_USER_ID, FB_PAGE_ID (public ids, set in the workflow) and META_TOKEN
(secret: a long-lived user token for the "social bridge" app). The page token used for
both platforms is fetched from META_TOKEN at the start of every run, so it never goes stale
and only one secret is needed. IG_TOKEN / FB_PAGE_TOKEN, if set, are used as they are.
Optional alerts: TG_BOT_TOKEN, TG_CHAT_ID.
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE = ROOT / "schedule.json"
STATE = ROOT / "state.json"
GRAPH = "https://graph.facebook.com/v21.0"
MAX_LATE = timedelta(hours=12)   # an item later than this is skipped, so a long outage never dumps a backlog
RETRY_WAITS = (60, 180)


def log(level, msg):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z] {level} {msg}", flush=True)


def call(url, params=None, method="POST", headers=None):
    data = urllib.parse.urlencode(params or {}).encode()
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode(), method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        where = url.split("?")[0].replace(GRAPH, "")
        raise RuntimeError(f"{where}: HTTP {ex.code} {ex.read().decode()[:400]}") from None


def notify(text):
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
    if not token or not chat:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=30).read()
    except Exception as ex:
        log("WARN", f"telegram alert failed: {ex}")


def media_url(name):
    if not (ROOT / "media" / name).exists():
        raise RuntimeError(f"missing media/{name}")
    repo = os.environ.get("GITHUB_REPOSITORY", "smithali731-pixel/tgaccess-autopost")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/media/{urllib.parse.quote(name)}"


# ---------------------------------------------------------------- Instagram
def ig_wait(cid, tok, tries=60, pause=10):
    for _ in range(tries):
        st = call(f"{GRAPH}/{cid}", {"fields": "status_code,status", "access_token": tok}, "GET")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid} failed: {st}")
        time.sleep(pause)
    raise RuntimeError(f"container {cid} not ready")


def publish_ig(item):
    ig, tok = os.environ["IG_USER_ID"], os.environ["IG_TOKEN"]
    url, kind = media_url(item["media"]), item["type"]
    if kind == "reel":
        p = {"media_type": "REELS", "video_url": url, "caption": item["caption"], "share_to_feed": "true"}
    elif kind == "story":
        p = {"media_type": "STORIES", "image_url": url}
    else:
        p = {"image_url": url, "caption": item["caption"]}
    cid = call(f"{GRAPH}/{ig}/media", {**p, "access_token": tok})["id"]
    ig_wait(cid, tok)
    return call(f"{GRAPH}/{ig}/media_publish", {"creation_id": cid, "access_token": tok})["id"]


# ---------------------------------------------------------------- Facebook page
def publish_fb(item):
    page, tok = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    url, kind = media_url(item["media"]), item["type"]
    if kind == "feed":
        r = call(f"{GRAPH}/{page}/photos", {"url": url, "caption": item["caption"], "access_token": tok})
        return r.get("post_id") or r["id"]
    if kind == "story":
        photo = call(f"{GRAPH}/{page}/photos", {"url": url, "published": "false", "access_token": tok})["id"]
        r = call(f"{GRAPH}/{page}/photo_stories", {"photo_id": photo, "access_token": tok})
        return r.get("post_id") or photo
    start = call(f"{GRAPH}/{page}/video_reels", {"upload_phase": "start", "access_token": tok})
    vid = start["video_id"]
    call(start.get("upload_url") or f"https://rupload.facebook.com/video-upload/v21.0/{vid}",
         headers={"Authorization": f"OAuth {tok}", "file_url": url})
    call(f"{GRAPH}/{page}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                         "description": item["caption"], "access_token": tok})
    return vid


PLATFORMS = {"ig": (publish_ig, ("IG_USER_ID", "IG_TOKEN"), "Instagram"),
             "fb": (publish_fb, ("FB_PAGE_ID", "FB_PAGE_TOKEN"), "Facebook")}


def with_retries(fn, item, label, sleep=time.sleep):
    for n in range(len(RETRY_WAITS) + 1):
        try:
            return fn(item)
        except Exception as ex:
            log("ERROR", f"{item['id']} {label} attempt {n + 1}: {ex}")
            if n == len(RETRY_WAITS):
                notify(f"❌ TG Access: failed to publish {item['id']} on {label}\n{str(ex)[:300]}")
                raise
            sleep(RETRY_WAITS[n])


def resolve_tokens():
    """Fill IG_TOKEN and FB_PAGE_TOKEN from META_TOKEN when they are not set directly."""
    meta, page = os.environ.get("META_TOKEN"), os.environ.get("FB_PAGE_ID")
    if not meta or not page or (os.environ.get("IG_TOKEN") and os.environ.get("FB_PAGE_TOKEN")):
        return
    tok = call(f"{GRAPH}/{page}", {"fields": "access_token", "access_token": meta}, "GET")["access_token"]
    os.environ.setdefault("IG_TOKEN", tok)
    os.environ.setdefault("FB_PAGE_TOKEN", tok)


def main():
    now = datetime.now(timezone.utc)
    try:
        resolve_tokens()
    except Exception as ex:
        log("ERROR", f"could not get the page token from META_TOKEN: {ex}")
        notify(f"❌ TG Access autopost: the Meta token no longer works\n{str(ex)[:300]}")
        return 1
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    state.setdefault("done", {})
    state.setdefault("skipped", {})
    ready = {k for k, (_, env, _) in PLATFORMS.items() if all(os.environ.get(e) for e in env)}
    if not ready:
        log("INFO", "no account secrets set yet; nothing is published")
        return 0

    try:
        acct = call(f"{GRAPH}/{os.environ['IG_USER_ID']}", {"fields": "username", "access_token": os.environ["IG_TOKEN"]}, "GET") if "ig" in ready else {}
    except Exception as ex:
        acct = {}
        log("WARN", f"instagram account check failed: {ex}")
    nxt = min((x["at"] for x in schedule if datetime.fromisoformat(x["at"]) > now), default="none")
    log("INFO", f"ready for {', '.join(sorted(ready))}; instagram @{acct.get('username', '-')}; next item at {nxt}")
    failed = False
    for it in sorted(schedule, key=lambda x: x["at"]):
        at = datetime.fromisoformat(it["at"])
        if at > now:
            continue
        for plat in sorted(ready):
            key = f"{it['id']}:{plat}"
            if key in state["done"] or key in state["skipped"]:
                continue
            if now - at > MAX_LATE:
                state["skipped"][key] = {"at": now.isoformat(timespec="seconds"), "why": "more than 12h late"}
                log("WARN", f"skipped {key}: more than 12h late")
                continue
            fn, _, label = PLATFORMS[plat]
            try:
                pid = with_retries(fn, it, label)
                state["done"][key] = {"post_id": str(pid), "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                log("INFO", f"published {key} -> {pid}")
            except Exception:
                failed = True
            STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
