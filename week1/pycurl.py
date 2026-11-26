#!/usr/bin/env python3
"""A curl-like HTTP client that uses only the Python 3 standard library.

The response body is written to stdout (or to ``-o FILE``). Request and
response lines from ``-v`` go to stderr. Exit status is ``0`` on success,
``1`` when the transfer or the HTTP status fails, and ``2`` for bad usage.
"""

from __future__ import annotations

import argparse
import re
import ssl
import sys
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from urllib.parse import quote, urljoin, urlsplit

__version__ = "1.0"
USER_AGENT = f"pycurl/{__version__}"
MAX_REDIRECTS = 20

# Characters that may appear literally in a request target. "%" is included so
# an already-encoded URL is not encoded a second time.
_UNRESERVED = "-._~"
_SUB_DELIMS = "!$&'()*+,;="
_TARGET_SAFE = "%" + _UNRESERVED + _SUB_DELIMS + ":@"
_PATH_SAFE = _TARGET_SAFE + "/"
_QUERY_SAFE = _PATH_SAFE + "?"
_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_ENTITY_HEADERS = {"content-length", "content-type", "transfer-encoding"}
_REDIRECTS = {301, 302, 303, 307, 308}


class ClientError(Exception):
    """Expected failure that should become a non-zero exit status."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class HttpResult:
    status: int
    reason: str
    version: str
    headers: list[tuple[str, str]]
    body: bytes

    def header(self, name: str) -> str | None:
        key = name.lower()
        for header_name, value in self.headers:
            if header_name.lower() == key:
                return value
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pycurl",
        description=(
            "Curl-like HTTP client using only the Python 3 standard library. "
            "Writes the response body to stdout. HTTP status 400 or higher "
            "is an error and exits with status 1."
        ),
    )
    parser.add_argument("url", help="http or https URL to request")
    parser.add_argument(
        "-X",
        "--request",
        metavar="METHOD",
        help="HTTP method (default: GET, or POST when --data is set)",
    )
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        default=[],
        metavar="HEADER",
        help="request header 'Name: value' (repeatable; an empty value removes it)",
    )
    parser.add_argument(
        "-d",
        "--data",
        action="append",
        default=None,
        metavar="DATA",
        help="request body; @file reads a file and @- reads stdin (repeatable)",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="store_true",
        help="include the response status line and headers in the output",
    )
    parser.add_argument(
        "-I",
        "--head",
        action="store_true",
        help="send HEAD and print response headers only",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write the output to FILE instead of stdout",
    )
    parser.add_argument(
        "-L",
        "--location",
        action="store_true",
        help="follow redirects (301, 302, 303, 307, 308)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print request and response lines to stderr",
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="suppress error messages (the body is still written; -v still logs)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="socket timeout in seconds (default: wait indefinitely)",
    )
    return parser


def parse_header(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise ClientError(
            f"invalid header (expected 'Name: value'): {raw!r}",
            code=2,
        )
    name, value = raw.split(":", 1)
    name = name.strip()
    value = value.strip()
    if not _TOKEN_RE.fullmatch(name):
        raise ClientError(f"invalid header name: {name!r}", code=2)
    if "\r" in value or "\n" in value:
        raise ClientError(f"invalid header value for {name}", code=2)
    try:
        value.encode("latin-1")
    except UnicodeEncodeError as exc:
        raise ClientError(
            f"header {name} is not latin-1 encodable",
            code=2,
        ) from exc
    return name, value


def load_data(pieces: list[str] | None) -> bytes | None:
    """Return the request body, or None when ``--data`` was not given."""
    if pieces is None:
        return None
    parts: list[bytes] = []
    for piece in pieces:
        if piece.startswith("@"):
            spec = piece[1:]
            if spec == "":
                raise ClientError("missing file name after @", code=2)
            if spec == "-":
                parts.append(_read_stdin())
                continue
            try:
                with open(spec, "rb") as handle:
                    parts.append(handle.read())
            except OSError as exc:
                detail = exc.strerror or str(exc)
                raise ClientError(f"cannot read {spec!r}: {detail}", code=1) from exc
            continue
        parts.append(piece.encode("utf-8"))
    return b"&".join(parts)


def _read_stdin() -> bytes:
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is not None:
        return buffer.read()
    text = sys.stdin.read()
    if isinstance(text, bytes):
        return text
    return text.encode("utf-8")


def normalize_method(raw: str | None, has_body: bool, head: bool) -> str:
    if head:
        return "HEAD"
    if raw is None:
        return "POST" if has_body else "GET"
    method = raw.strip().upper()
    if not _TOKEN_RE.fullmatch(method):
        raise ClientError(f"invalid HTTP method: {raw!r}", code=2)
    return method


def request_target(path: str, query: str) -> str:
    encoded = quote(path or "/", safe=_PATH_SAFE)
    if not encoded.startswith("/"):
        encoded = "/" + encoded
    if query:
        return encoded + "?" + quote(query, safe=_QUERY_SAFE)
    return encoded


def parse_target(url: str) -> tuple[str, str, int, str]:
    """Split an absolute http(s) URL into scheme, host, port, and target."""
    raw = url.strip()
    if not raw:
        raise ClientError("empty URL", code=2)
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise ClientError(f"unsupported URL scheme: {scheme or '(none)'}", code=1)
    if not parts.hostname:
        raise ClientError(f"URL is missing a host: {url}", code=1)
    try:
        port = parts.port
    except ValueError as exc:
        raise ClientError(f"invalid port in URL: {url}", code=1) from exc
    if port is None:
        port = 443 if scheme == "https" else 80
    try:
        host = parts.hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ClientError(f"invalid host: {parts.hostname}", code=1) from exc
    return scheme, host, port, request_target(parts.path, parts.query)


def host_header(host: str, port: int, scheme: str) -> str:
    default_port = 443 if scheme == "https" else 80
    display = f"[{host}]" if ":" in host else host
    if port == default_port:
        return display
    return f"{display}:{port}"


def strip_entity_headers(headers: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [(name, value) for name, value in headers if name.lower() not in _ENTITY_HEADERS]


def merge_headers(
    defaults: list[tuple[str, str]],
    user: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Apply ``-H`` the way curl does.

    A later empty value removes that header. Repeating a name with a
    non-empty value keeps every value, in order.
    """
    explicit: list[tuple[str, str]] = []
    suppressed: set[str] = set()
    for name, value in user:
        key = name.lower()
        if value == "":
            explicit = [(n, v) for n, v in explicit if n.lower() != key]
            suppressed.add(key)
        else:
            suppressed.discard(key)
            explicit.append((name, value))
    explicit_names = {name.lower() for name, _ in explicit}
    kept = [
        (name, value)
        for name, value in defaults
        if name.lower() not in suppressed and name.lower() not in explicit_names
    ]
    return kept + explicit


def build_headers(
    host_value: str,
    user_headers: list[tuple[str, str]],
    body: bytes | None,
) -> list[tuple[str, str]]:
    defaults = [
        ("Host", host_value),
        ("User-Agent", USER_AGENT),
        ("Accept", "*/*"),
        ("Connection", "close"),
    ]
    filtered = [(name, value) for name, value in user_headers if name.lower() != "content-length"]
    headers = merge_headers(defaults, filtered)
    if body is None:
        return headers
    if not any(name.lower() == "content-type" for name, _ in headers):
        headers.append(("Content-Type", "application/x-www-form-urlencoded"))
    headers.append(("Content-Length", str(len(body))))
    return headers


def adjust_for_redirect(
    status: int,
    method: str,
    body: bytes | None,
    headers: list[tuple[str, str]],
) -> tuple[str, bytes | None, list[tuple[str, str]]]:
    """Match curl: 301/302 rewrite POST, and 303 rewrites every method but HEAD."""
    rewrite = (status in (301, 302) and method == "POST") or (
        status == 303 and method != "HEAD"
    )
    if not rewrite:
        return method, body, headers
    return "GET", None, strip_entity_headers(headers)


def open_connection(
    scheme: str,
    host: str,
    port: int,
    timeout: float | None,
) -> HTTPConnection:
    if scheme == "https":
        context = ssl.create_default_context()
        return HTTPSConnection(host, port, timeout=timeout, context=context)
    return HTTPConnection(host, port, timeout=timeout)


def format_version(version: int) -> str:
    major, minor = divmod(version, 10)
    return f"{major}.{minor}"


def exchange(
    scheme: str,
    host: str,
    port: int,
    target: str,
    method: str,
    headers: list[tuple[str, str]],
    body: bytes | None,
    timeout: float | None,
    verbose: bool,
) -> HttpResult:
    conn: HTTPConnection | None = None
    try:
        conn = open_connection(scheme, host, port, timeout)
        if verbose:
            print(f"* Connecting to {host} port {port}", file=sys.stderr)
        conn.connect()
        if verbose:
            print(f"* Connected to {host} port {port}", file=sys.stderr)
            print(f"> {method} {target} HTTP/1.1", file=sys.stderr)
            for name, value in headers:
                print(f"> {name}: {value}", file=sys.stderr)
            print(">", file=sys.stderr)
        conn.putrequest(method, target, skip_host=True, skip_accept_encoding=True)
        for name, value in headers:
            conn.putheader(name, value)
        if body is None:
            conn.endheaders()
        else:
            conn.endheaders(message_body=body)
        response = conn.getresponse()
        payload = response.read()
        version = format_version(response.version)
        reason = response.reason or ""
        pairs = [(str(name), str(value)) for name, value in response.getheaders()]
        if verbose:
            line = f"< HTTP/{version} {response.status}"
            if reason:
                line = f"{line} {reason}"
            print(line, file=sys.stderr)
            for name, value in pairs:
                print(f"< {name}: {value}", file=sys.stderr)
            print("<", file=sys.stderr)
        return HttpResult(
            status=response.status,
            reason=reason,
            version=version,
            headers=pairs,
            body=payload,
        )
    finally:
        if conn is not None:
            conn.close()


def perform(
    url: str,
    method: str,
    user_headers: list[tuple[str, str]],
    body: bytes | None,
    timeout: float | None,
    follow: bool,
    verbose: bool,
) -> HttpResult:
    current_url = urlsplit(url.strip())._replace(fragment="").geturl()
    hop_headers = list(user_headers)
    if method == "HEAD":
        body = None
        hop_headers = strip_entity_headers(hop_headers)

    redirects = 0
    while True:
        scheme, host, port, target = parse_target(current_url)
        headers = build_headers(host_header(host, port, scheme), hop_headers, body)
        result = exchange(
            scheme,
            host,
            port,
            target,
            method,
            headers,
            body,
            timeout,
            verbose,
        )
        location = result.header("Location")
        if not follow or result.status not in _REDIRECTS or not location:
            return result
        if redirects >= MAX_REDIRECTS:
            raise ClientError(
                f"too many redirects (maximum is {MAX_REDIRECTS})",
                code=1,
            )
        redirects += 1
        current_url = urlsplit(urljoin(current_url, location.strip()))._replace(fragment="").geturl()
        method, body, hop_headers = adjust_for_redirect(
            result.status,
            method,
            body,
            hop_headers,
        )
        if verbose:
            print(f"* Following redirect to {current_url}", file=sys.stderr)


def format_header_block(result: HttpResult) -> bytes:
    if result.reason:
        lines = [f"HTTP/{result.version} {result.status} {result.reason}"]
    else:
        lines = [f"HTTP/{result.version} {result.status}"]
    for name, value in result.headers:
        lines.append(f"{name}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1", errors="replace")


def render(result: HttpResult, include: bool, head_only: bool) -> bytes:
    parts: list[bytes] = []
    if include or head_only:
        parts.append(format_header_block(result))
    if not head_only:
        parts.append(result.body)
    return b"".join(parts)


def write_output(payload: bytes, path: str | None) -> None:
    if path is None:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return
    try:
        with open(path, "wb") as handle:
            handle.write(payload)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise ClientError(f"cannot write {path!r}: {detail}", code=1) from exc


def execute(args: argparse.Namespace) -> int:
    if args.timeout is not None and args.timeout < 0:
        raise ClientError("--timeout must be zero or greater", code=2)
    user_headers = [parse_header(item) for item in args.header]
    body = load_data(args.data)
    method = normalize_method(args.request, body is not None, args.head)
    result = perform(
        url=args.url,
        method=method,
        user_headers=user_headers,
        body=body,
        timeout=args.timeout,
        follow=args.location,
        verbose=args.verbose,
    )
    write_output(render(result, args.include, args.head), args.output)
    if result.status >= 400:
        reason = f" {result.reason}" if result.reason else ""
        raise ClientError(f"the server returned HTTP {result.status}{reason}", code=1)
    return 0


def report(silent: bool, message: str) -> None:
    if not silent and message:
        print(f"pycurl: {message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 2
    try:
        return execute(args)
    except ClientError as exc:
        report(args.silent, str(exc))
        return exc.code
    except BrokenPipeError:
        return 1
    except TimeoutError:
        report(args.silent, "operation timed out")
        return 1
    except (HTTPException, OSError, ValueError) as exc:
        report(args.silent, str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
