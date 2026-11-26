#!/usr/bin/env python3
"""Offline tests for the week1 HTTP client.

They talk only to a local ``http.server`` started by this module.
"""

from __future__ import annotations

import contextlib
import os
import socket
import sys
import tempfile
import threading
import time
import traceback
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pycurl

TEXT = "你好\n".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    base_url = ""
    records: list[dict] = []
    lock = threading.Lock()

    def log_message(self, fmt: str, *args) -> None:
        return

    @classmethod
    def reset(cls) -> None:
        with cls.lock:
            cls.records.clear()

    @classmethod
    def snapshot(cls) -> list[dict]:
        with cls.lock:
            return list(cls.records)

    def _header_map(self) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        seen: set[str] = set()
        for key in self.headers.keys():
            low = key.lower()
            if low in seen:
                continue
            seen.add(low)
            values = self.headers.get_all(key) or []
            found[low] = [value.strip() for value in values]
        return found

    def _remember(self, body: bytes) -> None:
        item = {
            "method": self.command,
            "path": self.path,
            "headers": self._header_map(),
            "body": body,
        }
        with self.lock:
            self.records.append(item)

    def _read_body(self) -> bytes:
        raw = self.headers.get("Content-Length")
        if raw is None:
            return b""
        try:
            length = int(raw)
        except ValueError:
            return b""
        if length < 0:
            return b""
        return self.rfile.read(length)

    def _send(self, code: int, payload: bytes, extra: list[tuple[str, str]] | None = None) -> None:
        self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        for key, value in extra or []:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)

    def _dispatch(self) -> None:
        body = self._read_body()
        route = urlsplit(self.path).path

        if route == "/text":
            self._remember(body)
            self._send(200, TEXT, [("X-Test", "yes")])
            return
        if route == "/echo":
            self._remember(body)
            self._send(200, f"{self.command} {self.path}\n".encode() + body)
            return
        if route == "/fail":
            self._remember(body)
            self._send(404, b"missing")
            return
        if route == "/slow":
            self._remember(body)
            time.sleep(1.5)
            self._send(200, b"slow")
            return
        if route == "/only-get":
            self._remember(body)
            if self.command != "GET":
                self._send(405, b"bad-method")
            else:
                self._send(200, b"got-get")
            return
        if route == "/redirect-rel":
            self._remember(body)
            self._send(302, b"go", [("Location", "/text")])
            return
        if route == "/redirect-abs":
            self._remember(body)
            self._send(302, b"go", [("Location", self.base_url + "/text")])
            return
        if route == "/chain":
            self._remember(body)
            self._send(302, b"go", [("Location", "/redirect-rel")])
            return
        if route in ("/redirect-301", "/redirect-302"):
            self._remember(body)
            code = 301 if route.endswith("301") else 302
            self._send(code, b"go", [("Location", "/only-get")])
            return
        if route == "/redirect-303":
            self._remember(body)
            self._send(303, b"go", [("Location", "/only-get")])
            return
        if route == "/redirect-307":
            self._remember(body)
            self._send(307, b"go", [("Location", "/echo")])
            return
        if route == "/loop":
            self._remember(body)
            self._send(302, b"go", [("Location", "/loop")])
            return
        if route == "/redirect-noloc":
            self._remember(body)
            self._send(302, b"stay")
            return
        self._remember(body)
        self._send(404, b"no-route")

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = _dispatch


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionError, TimeoutError, BrokenPipeError, socket.timeout)):
            return
        traceback.print_exc(file=sys.__stderr__)


class StdoutBuffer:
    """Stand-in for ``sys.stdout`` that records binary writes."""

    encoding = "utf-8"

    def __init__(self) -> None:
        self.buffer = BytesIO()

    def write(self, data: str | bytes) -> None:
        if isinstance(data, str):
            self.buffer.write(data.encode())
        else:
            self.buffer.write(data)

    def flush(self) -> None:
        self.buffer.flush()


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Handler.reset()
        cls.server = QuietServer(("127.0.0.1", 0), Handler)
        host, port = cls.server.server_address
        cls.base = f"http://{host}:{port}"
        Handler.base_url = cls.base
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            name="pycurl-test-httpd",
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self) -> None:
        Handler.reset()

    def url(self, path: str) -> str:
        return self.base + path

    def run_client(self, args: list[str]) -> tuple[int, bytes, str]:
        stdout = StdoutBuffer()
        stderr = StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = pycurl.main(list(args))
        return code, stdout.buffer.getvalue(), stderr.getvalue()

    def test_get_prints_body(self) -> None:
        code, out, err = self.run_client([self.url("/text")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)
        recorded = Handler.snapshot()
        self.assertEqual(recorded[0]["method"], "GET")
        self.assertEqual(recorded[0]["headers"]["user-agent"], [pycurl.USER_AGENT])
        self.assertNotIn("content-length", recorded[0]["headers"])

    def test_include_response_headers(self) -> None:
        code, out, err = self.run_client(["--include", self.url("/text")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(b"HTTP/1.1 200 OK\r\n"), out)
        self.assertIn(b"\r\nX-Test: yes\r\n", out)
        self.assertTrue(out.endswith(b"\r\n\r\n" + TEXT), out)

    def test_head_prints_headers_only(self) -> None:
        code, out, err = self.run_client(["-I", self.url("/text")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(b"HTTP/1.1 200 OK\r\n"), out)
        self.assertIn(b"\r\nX-Test: yes\r\n", out)
        self.assertNotIn(TEXT, out)
        self.assertEqual(Handler.snapshot()[0]["method"], "HEAD")
        self.assertEqual(Handler.snapshot()[0]["body"], b"")

    def test_explicit_head_without_include_has_empty_body(self) -> None:
        code, out, err = self.run_client(["-X", "HEAD", self.url("/text")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertEqual(Handler.snapshot()[0]["method"], "HEAD")

    def test_head_follows_redirect(self) -> None:
        code, out, err = self.run_client(["--head", "-L", self.url("/redirect-rel")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(b"HTTP/1.1 200 OK\r\n"), out)
        self.assertNotIn(TEXT, out)
        self.assertEqual([item["method"] for item in Handler.snapshot()], ["HEAD", "HEAD"])

    def test_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "body.txt")
            code, out, err = self.run_client(["-o", path, self.url("/text")])
            self.assertEqual(err, "")
            self.assertEqual(code, 0)
            self.assertEqual(out, b"")
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), TEXT)

    def test_output_file_includes_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "all.bin")
            code, out, err = self.run_client(["-i", "--output", path, self.url("/text")])
            self.assertEqual(err, "")
            self.assertEqual(code, 0)
            self.assertEqual(out, b"")
            with open(path, "rb") as handle:
                saved = handle.read()
            self.assertTrue(saved.startswith(b"HTTP/1.1 200 OK\r\n"), saved)
            self.assertTrue(saved.endswith(b"\r\n\r\n" + TEXT), saved)

    def test_output_on_http_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "err.txt")
            code, out, err = self.run_client(["-o", path, self.url("/fail")])
            self.assertNotEqual(code, 0)
            self.assertIn("404", err)
            self.assertEqual(out, b"")
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"missing")

    def test_follow_relative_chain(self) -> None:
        code, out, err = self.run_client(["-L", self.url("/chain")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)
        self.assertEqual(
            [item["path"] for item in Handler.snapshot()],
            ["/chain", "/redirect-rel", "/text"],
        )

    def test_follow_absolute_redirect(self) -> None:
        code, out, err = self.run_client(["--location", self.url("/redirect-abs")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)
        self.assertEqual(
            [item["path"] for item in Handler.snapshot()],
            ["/redirect-abs", "/text"],
        )

    def test_no_follow_returns_redirect(self) -> None:
        code, out, err = self.run_client([self.url("/redirect-rel")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, b"go")
        self.assertEqual(len(Handler.snapshot()), 1)

        Handler.reset()
        code, out, err = self.run_client(["-i", self.url("/redirect-rel")])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(b"HTTP/1.1 302 Found\r\n"), out)
        self.assertIn(b"\r\nLocation: /text\r\n", out)
        self.assertTrue(out.endswith(b"\r\n\r\ngo"), out)

    def test_post_redirect_301_and_302_become_get(self) -> None:
        for path in ("/redirect-301", "/redirect-302"):
            with self.subTest(path=path):
                Handler.reset()
                code, out, err = self.run_client(
                    ["-L", "-d", "payload", self.url(path)]
                )
                self.assertEqual(err, "", err)
                self.assertEqual(code, 0)
                self.assertEqual(out, b"got-get")
                recorded = Handler.snapshot()
                self.assertEqual([item["method"] for item in recorded], ["POST", "GET"])
                self.assertEqual(recorded[0]["body"], b"payload")
                self.assertEqual(recorded[1]["body"], b"")
                self.assertNotIn("content-type", recorded[1]["headers"])

    def test_post_redirect_303_becomes_get(self) -> None:
        code, out, err = self.run_client(
            ["-X", "POST", "--location", "-d", "payload", self.url("/redirect-303")]
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, b"got-get")
        recorded = Handler.snapshot()
        self.assertEqual([item["method"] for item in recorded], ["POST", "GET"])
        self.assertEqual(recorded[1]["body"], b"")

    def test_post_redirect_307_preserves_body(self) -> None:
        code, out, err = self.run_client(
            ["-L", "-H", "Content-Type: text/plain", "-d", "kept", self.url("/redirect-307")]
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        recorded = Handler.snapshot()
        self.assertEqual([item["method"] for item in recorded], ["POST", "POST"])
        self.assertEqual(recorded[0]["body"], b"kept")
        self.assertEqual(recorded[1]["body"], b"kept")
        self.assertEqual(recorded[1]["headers"]["content-type"], ["text/plain"])
        self.assertTrue(out.endswith(b"kept"), out)

    def test_redirect_without_location_is_returned(self) -> None:
        code, out, err = self.run_client(["-L", self.url("/redirect-noloc")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, b"stay")
        self.assertEqual(len(Handler.snapshot()), 1)

    def test_too_many_redirects(self) -> None:
        original = pycurl.MAX_REDIRECTS
        pycurl.MAX_REDIRECTS = 2
        try:
            code, out, err = self.run_client(["-L", self.url("/loop")])
        finally:
            pycurl.MAX_REDIRECTS = original
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertIn("redirect", err.lower())
        self.assertEqual(len(Handler.snapshot()), 3)

    def test_verbose_request_and_response_lines(self) -> None:
        code, out, err = self.run_client(["-v", self.url("/text")])
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)
        self.assertIn("> GET /text HTTP/1.1", err)
        self.assertIn("> Host:", err)
        self.assertIn("< HTTP/1.1 200 OK", err)
        self.assertIn("<", err)

    def test_verbose_shows_redirect_hops(self) -> None:
        code, out, err = self.run_client(["--verbose", "-L", "-d", "x", self.url("/redirect-303")])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"got-get")
        self.assertIn("> POST /redirect-303 HTTP/1.1", err)
        self.assertIn("> GET /only-get HTTP/1.1", err)
        self.assertIn("* Following redirect to", err)

    def test_silent_still_shows_verbose_but_hides_errors(self) -> None:
        code, out, err = self.run_client(["-s", "-v", self.url("/text")])
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)
        self.assertIn("> GET /text HTTP/1.1", err)

        code, out, err = self.run_client(["--silent", self.url("/fail")])
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"missing")
        self.assertEqual(err, "")

    def test_connection_error_is_nonzero(self) -> None:
        port = _closed_port()
        code, out, err = self.run_client([f"http://127.0.0.1:{port}/"])
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertIn("pycurl:", err)

        code, out, err = self.run_client(["-s", f"http://127.0.0.1:{port}/"])
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertEqual(err, "")

    def test_timeout(self) -> None:
        code, out, err = self.run_client(["--timeout", "0.4", self.url("/slow")])
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertIn("timed out", err.lower())

    def test_timeout_allows_fast_request(self) -> None:
        code, out, err = self.run_client(["--timeout", "5", self.url("/text")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out, TEXT)

    def test_http_error_status(self) -> None:
        code, out, err = self.run_client([self.url("/fail")])
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"missing")
        self.assertIn("404", err)

    def test_methods_put_delete_patch(self) -> None:
        cases = [
            (["-X", "PUT", "--data", "put-body"], "PUT", b"put-body"),
            (["--request", "delete"], "DELETE", None),
            (["-X", "patch", "-d", "patch-body"], "PATCH", b"patch-body"),
        ]
        for args, method, body in cases:
            with self.subTest(method=method):
                Handler.reset()
                code, out, err = self.run_client([*args, self.url("/echo")])
                self.assertEqual(err, "", err)
                self.assertEqual(code, 0)
                recorded = Handler.snapshot()[0]
                self.assertEqual(recorded["method"], method)
                if body is None:
                    self.assertEqual(recorded["body"], b"")
                    self.assertNotIn("content-length", recorded["headers"])
                else:
                    self.assertEqual(recorded["body"], body)
                    self.assertEqual(recorded["headers"]["content-length"], [str(len(body))])
                self.assertTrue(out.startswith(method.encode() + b" "), out)

    def test_data_defaults_to_post_and_content_type(self) -> None:
        code, out, err = self.run_client(["-d", "name=ada", self.url("/echo")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        recorded = Handler.snapshot()[0]
        self.assertEqual(recorded["method"], "POST")
        self.assertEqual(recorded["body"], b"name=ada")
        self.assertEqual(
            recorded["headers"]["content-type"],
            ["application/x-www-form-urlencoded"],
        )
        self.assertTrue(out.endswith(b"name=ada"), out)

    def test_custom_content_type_is_kept(self) -> None:
        code, out, err = self.run_client(
            [
                "-H",
                "Content-Type: application/json",
                "--data",
                '{"name":"測試"}',
                self.url("/echo"),
            ]
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        recorded = Handler.snapshot()[0]
        self.assertEqual(recorded["headers"]["content-type"], ["application/json"])
        self.assertEqual(recorded["body"], '{"name":"測試"}'.encode())

    def test_explicit_get_with_body(self) -> None:
        code, out, err = self.run_client(["-X", "GET", "-d", "q", self.url("/echo")])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        recorded = Handler.snapshot()[0]
        self.assertEqual(recorded["method"], "GET")
        self.assertEqual(recorded["body"], b"q")

    def test_data_from_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            handle.write("欄位=值".encode())
            name = handle.name
        try:
            code, out, err = self.run_client(["-d", f"@{name}", self.url("/echo")])
        finally:
            os.unlink(name)
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(Handler.snapshot()[0]["body"], "欄位=值".encode())
        self.assertTrue(out.endswith("欄位=值".encode()), out)

    def test_data_from_stdin(self) -> None:
        class Stdin:
            def __init__(self, payload: bytes) -> None:
                self.buffer = BytesIO(payload)

        original = sys.stdin
        sys.stdin = Stdin(b"from-stdin")
        try:
            code, out, err = self.run_client(["--data", "@-", self.url("/echo")])
        finally:
            sys.stdin = original
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(Handler.snapshot()[0]["body"], b"from-stdin")
        self.assertTrue(out.endswith(b"from-stdin"), out)

    def test_multiple_data_are_joined(self) -> None:
        code, out, err = self.run_client(
            ["-d", "a=1", "-d", "b=2", self.url("/echo")]
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(Handler.snapshot()[0]["body"], b"a=1&b=2")

    def test_missing_data_file(self) -> None:
        code, out, err = self.run_client(
            ["-d", "@/no/such/pycurl-data-file", self.url("/text")]
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertIn("pycurl:", err)
        self.assertEqual(Handler.snapshot(), [])

    def test_repeatable_headers_override_and_remove(self) -> None:
        code, out, err = self.run_client(
            [
                "--header",
                "X-One: alpha",
                "-H",
                "X-Two: beta",
                "-H",
                "X-One: gamma",
                "-H",
                "User-Agent: student",
                "-H",
                "Accept:",
                self.url("/text"),
            ]
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        headers = Handler.snapshot()[0]["headers"]
        self.assertEqual(headers["x-one"], ["alpha", "gamma"])
        self.assertEqual(headers["x-two"], ["beta"])
        self.assertEqual(headers["user-agent"], ["student"])
        self.assertNotIn("accept", headers)

    def test_query_string_and_fragment(self) -> None:
        code, out, err = self.run_client([self.url("/echo?q=a+b%20c&x=1") + "#section"])
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(Handler.snapshot()[0]["path"], "/echo?q=a+b%20c&x=1")
        self.assertIn(b"GET /echo?q=a+b%20c&x=1\n", out)

    def test_missing_url(self) -> None:
        code, out, err = self.run_client([])
        self.assertEqual(code, 2)
        self.assertEqual(out, b"")
        self.assertIn("url", err.lower())

    def test_unsupported_scheme_and_missing_host(self) -> None:
        code, out, err = self.run_client(["ftp://127.0.0.1/file"])
        self.assertEqual(code, 1)
        self.assertIn("scheme", err.lower())
        self.assertEqual(Handler.snapshot(), [])

        code, out, err = self.run_client(["http://"])
        self.assertEqual(code, 1)
        self.assertIn("host", err.lower())

    def test_invalid_method_and_header(self) -> None:
        code, out, err = self.run_client(["-X", "GOT GET", self.url("/text")])
        self.assertEqual(code, 2)
        self.assertIn("method", err.lower())
        self.assertEqual(Handler.snapshot(), [])

        code, out, err = self.run_client(["-H", "Bad Header", self.url("/text")])
        self.assertEqual(code, 2)
        self.assertIn("header", err.lower())

    def test_negative_timeout(self) -> None:
        code, out, err = self.run_client(["--timeout", "-1", self.url("/text")])
        self.assertEqual(code, 2)
        self.assertIn("timeout", err.lower())
        self.assertEqual(Handler.snapshot(), [])

    def test_cannot_write_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = self.run_client(["-o", directory, self.url("/text")])
        self.assertNotEqual(code, 0)
        self.assertIn("pycurl:", err)
        self.assertEqual(out, b"")

    def test_help(self) -> None:
        code, out, err = self.run_client(["-h"])
        self.assertEqual(code, 0)
        self.assertIn(b"pycurl", out.lower())


def _closed_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


if __name__ == "__main__":
    unittest.main()
