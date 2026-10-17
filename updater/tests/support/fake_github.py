# -*- coding: utf-8 -*-
"""TEST-ONLY local stand-in for the GitHub releases API and release-asset host (L-3). Never shipped.

Serves on 127.0.0.1 only. The test-only worker maps the product's https URLs onto it through
hooks.network_rewrite: https://api.github.com/<p> -> <base>/api/<p>, https://<host>/<p> ->
<base>/cdn/<host>/<p>. Each case sets `pages` (listing responses by page number) and `assets`
(asset id -> bytes and behavior); every request is logged with its headers.

Response spec (listing pages, asset API responses):
  {"json": obj} | {"raw": bytes} with optional "status", "headers", and "mode":
  "truncate" (declares the full length, sends half, closes) | "sleep" (waits "seconds" first).
Asset entry: {"data": bytes, "api": "redirect"|"direct"|"offsite"|"http_redirect"|"api_redirect"|"status:N",
              "cdn": "ok"|"truncate"|"extra"|"replace"|"redirect_again"|"sleep", "cdn_data": bytes, "seconds": s}
"""
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

REPO = "chadchan3d/sfm-character-tools"
OLD_REPO = "chadchan3d/sfm-animation-groups-master"
CDN = "objects.githubusercontent.com"


class Fake(object):
    def __init__(self):
        self.pages = {}
        self.assets = {}
        self.log = []
        self.lock = threading.Lock()
        self.server = None
        self.base = None

    def reset(self):
        with self.lock:
            self.pages, self.assets, self.log = {}, {}, []

    def start(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_GET(self):
                try:
                    fake.handle(self)
                except (ConnectionError, OSError):
                    pass  # the client gave up (timeout cases)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]
        return self

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    # ------------------------------------------------------------ responses
    @staticmethod
    def _send(h, status=200, body=b"", headers=None, mode=None, seconds=0):
        if mode == "sleep":
            time.sleep(seconds)
        h.send_response(status)
        hdrs = dict(headers or {})
        hdrs.setdefault("Content-Length", str(len(body)))
        hdrs.setdefault("Connection", "close")
        for k, v in hdrs.items():
            h.send_header(k, v)
        h.end_headers()
        h.wfile.write(body[:len(body) // 2] if mode == "truncate" else body)
        h.wfile.flush()
        h.close_connection = True

    def _spec(self, h, spec):
        body = spec["raw"] if "raw" in spec else json.dumps(spec.get("json", [])).encode("utf-8")
        self._send(h, spec.get("status", 200), body, spec.get("headers"), spec.get("mode"), spec.get("seconds", 0))

    def handle(self, h):
        u = urlsplit(h.path)
        with self.lock:
            self.log.append({"path": h.path, "headers": {k.lower(): v for k, v in h.headers.items()}})
            pages, assets = self.pages, self.assets
        if u.path == "/api/repos/%s/releases" % REPO:
            page = int(parse_qs(u.query).get("page", ["1"])[0])
            return self._spec(h, pages.get(page, {"json": []}))
        m = re.match(r"^/api/repos/%s/releases/assets/(\d+)$" % re.escape(REPO), u.path)
        if m and int(m.group(1)) in assets:
            aid = int(m.group(1))
            a = assets[aid]
            mode = a.get("api", "redirect")
            loc = {"redirect": "https://%s/assets/%d" % (CDN, aid),
                   "offsite": "https://downloads.example.invalid/assets/%d" % aid,
                   "http_redirect": "http://%s/assets/%d" % (CDN, aid),
                   "api_redirect": "https://api.github.com/repos/%s/releases/assets/%d" % (OLD_REPO, aid)}.get(mode)
            if loc:
                return self._send(h, 302, b"", {"Location": loc})
            if mode == "direct":
                return self._send(h, 200, a["data"])
            if mode.startswith("status:"):
                return self._send(h, int(mode[7:]), b"{}")
        m = re.match(r"^/cdn/([^/]+)/assets/(\d+)$", u.path)
        if m and int(m.group(2)) in assets:
            aid = int(m.group(2))
            a = assets[aid]
            cdn = a.get("cdn", "ok")
            if cdn == "redirect_again":
                return self._send(h, 302, b"", {"Location": "https://%s/assets/%d" % (CDN, aid)})
            if cdn == "extra":
                return self._send(h, 200, a["data"] + b"\n")
            if cdn == "replace":
                return self._send(h, 200, a["cdn_data"])
            if cdn in ("truncate", "sleep"):
                return self._send(h, 200, a["data"], mode=cdn, seconds=a.get("seconds", 0))
            return self._send(h, 200, a["data"])
        return self._send(h, 404, b'{"message":"Not Found"}')


def release_json(rid, tag, files, repo=REPO, prerelease=False, draft=False, sizes=None, state="uploaded"):
    """A GitHub release object whose assets are `files` (name -> bytes); returns (obj, {aid: bytes})."""
    assets, data = [], {}
    for i, (name, body) in enumerate(sorted(files.items())):
        aid = rid * 100 + i
        data[aid] = body
        assets.append({"url": "https://api.github.com/repos/%s/releases/assets/%d" % (repo, aid), "id": aid,
                       "name": name, "size": (sizes or {}).get(name, len(body)), "state": state,
                       "content_type": "application/octet-stream",
                       "browser_download_url": "https://github.com/%s/releases/download/%s/%s" % (repo, tag, name)})
    obj = {"url": "https://api.github.com/repos/%s/releases/%d" % (repo, rid), "id": rid, "tag_name": tag,
           "name": tag, "draft": draft, "prerelease": prerelease, "assets": assets,
           "html_url": "https://github.com/%s/releases/tag/%s" % (repo, tag)}
    return obj, data
