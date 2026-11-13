"""Write ../schedule.json: per day a story (morning), a feed post (afternoon) and a reel
(evening), Stockholm time. All 90 clock times are different from each other."""
import json, random
from datetime import timedelta
from pathlib import Path
from content import DAYS, TAGS
from render import START, names

def pool(h0, h1, step=5):
    return [f"{h:02d}:{m:02d}" for h in range(h0, h1) for m in range(0, 60, step)]

rnd = random.Random(731)
story_t = rnd.sample(pool(9, 12), 30)
post_t = rnd.sample(pool(13, 18), 30)
reel_t = rnd.sample(pool(19, 22), 30)
out = []
for i, d in enumerate(DAYS):
    day = (START + timedelta(days=i)).isoformat()
    post, vert, reel = names(i)
    cap = d["cap"] + "\n\n" + TAGS
    out += [
        {"id": f"{day}-story", "at": f"{day}T{story_t[i]}:00+01:00", "type": "story", "media": vert, "caption": ""},
        {"id": f"{day}-post", "at": f"{day}T{post_t[i]}:00+01:00", "type": "feed", "media": post, "caption": cap},
        {"id": f"{day}-reel", "at": f"{day}T{reel_t[i]}:00+01:00", "type": "reel", "media": reel, "caption": cap},
    ]
times = [x["at"][11:16] for x in out]
assert len(set(times)) == 90, "a clock time repeats"
Path(__file__).resolve().parent.parent.joinpath("schedule.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(out), "items", out[0]["at"], "->", out[-1]["at"])
