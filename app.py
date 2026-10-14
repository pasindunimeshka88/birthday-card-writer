import random
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

TEMPLATE = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

AGE_JOKES = [
    "{age} is just {name}'s way of saying 'I've been undefeated at aging so far.'",
    "At {age}, {name} is not old, just a limited edition.",
    "{age} candles? That's not a cake, it's a fire hazard!",
    "{name} is {age} today, which is {days:,} days of pure awesomeness (give or take a nap).",
]

HOBBY_JOKES = [
    "May your {hobby} skills keep improving, even if your knees don't.",
    "Here's hoping this year brings more {hobby} and less adulting.",
    "Nobody does {hobby} quite like you, and we've stopped asking questions.",
    "Your {hobby} obsession is the only thing getting better with age!",
]

OPENERS = ["Happy Birthday, {name}!", "Hip hip hooray, {name}!", "Another lap around the sun, {name}!"]
CLOSERS = ["Eat cake. Lots of it.", "Now go make a wish (and blame the candles).", "Party on!"]


def make_message(name: str, age: int, hobby: str) -> str:
    fields = {"name": name, "age": age, "hobby": hobby, "days": age * 365}
    parts = [
        random.choice(OPENERS),
        random.choice(AGE_JOKES),
        random.choice(HOBBY_JOKES),
        random.choice(CLOSERS),
    ]
    return " ".join(p.format(**fields) for p in parts)


def render(message: str = "", error: str = "", values=None) -> bytes:
    v = values or {}
    page = TEMPLATE
    block = ""
    if error:
        block = f'<p class="error">{escape(error)}</p>'
    elif message:
        block = f'<div class="card">{escape(message)}</div>'
    page = page.replace("{{result}}", block)
    for key in ("name", "age", "hobby"):
        page = page.replace("{{" + key + "}}", escape(v.get(key, ""), quote=True))
    return page.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(render())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(min(length, 10_000)).decode("utf-8"))
        values = {k: data.get(k, [""])[0].strip() for k in ("name", "age", "hobby")}
        if not all(values.values()):
            return self._send(render(error="Please fill in all fields.", values=values))
        try:
            age = int(values["age"])
            if not 0 < age < 150:
                raise ValueError
        except ValueError:
            return self._send(render(error="Age must be a number between 1 and 149.", values=values))
        self._send(render(make_message(values["name"], age, values["hobby"]), values=values))


if __name__ == "__main__":
    print("Open http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
