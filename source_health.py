"""Check public source pages without submitting forms or sending personal data.

A 200 response is a transport check, not evidence of a working subscription.
The caller controls database state; this module only evaluates HTTP observations.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import ssl
from dataclasses import asdict, dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

MAX_BODY = 192 * 1024
MAX_REDIRECTS = 5
USER_AGENT = 'spamalot/2.1.0 (personal-source-health; read-only)'


@dataclass
class Observation:
    url: str
    final_url: str
    result: str  # ok, review, broken
    http_status: int | None
    reason: str
    redirect_chain: list[str]
    suggested_url: str = ''


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ''
        self._label: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href = dict(attrs).get('href', '')
            self._label = []

    def handle_data(self, data):
        if self._href:
            self._label.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._href:
            self.links.append((self._href, ' '.join(self._label)))
            self._href = ''
            self._label = []


def public_https_url(url: str, *, resolve: bool = True) -> None:
    """Reject malformed URLs and names resolving to private/link-local endpoints.

    This is a best-effort SSRF check, not a DNS-rebinding-resistant sandbox.
    Do not run against untrusted network resolvers or on a privileged host.
    """
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only unauthenticated public HTTPS URLs are allowed')
    if parsed.port not in (None, 443):
        raise ValueError('Nonstandard HTTPS ports are not allowed')
    name = parsed.hostname.rstrip('.').lower()
    if name in ('localhost',) or name.endswith(('.local', '.internal', '.localhost')):
        raise ValueError('Local-network hostname rejected')
    try:
        direct = ipaddress.ip_address(name)
    except ValueError:
        direct = None
    if direct and not direct.is_global:
        raise ValueError('Private or reserved IP address rejected')
    if not resolve:
        return
    addresses = {entry[4][0] for entry in socket.getaddrinfo(name, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise ValueError('Hostname resolved to a private or non-global IP address')


def same_organization_host(a: str, b: str) -> bool:
    """Allow redirects between a hostname and its subdomains, not rebrands.

    For different registrable domains the user must approve the replacement.
    """
    left = (urlsplit(a).hostname or '').lower().removeprefix('www.')
    right = (urlsplit(b).hostname or '').lower().removeprefix('www.')
    return left == right or left.endswith('.' + right) or right.endswith('.' + left)


def page_assessment(status: int, content_type: str, body: bytes, role: str) -> tuple[str, str]:
    if status in (404, 410):
        return 'broken', f'HTTP {status}: missing resource'
    if status in (401, 403, 406, 429):
        return 'review', f'HTTP {status}: access challenge or rate limit, not necessarily broken'
    if status >= 500 or status in (408, 425):
        return 'review', f'HTTP {status}: transient server failure'
    if not 200 <= status < 300:
        return 'review', f'Unexpected HTTP {status}'
    if not any(t in content_type for t in ('text/html', 'text/plain', 'application/pdf')):
        return 'review', f'Unexpected content type: {content_type or "unknown"}'
    if 'application/pdf' in content_type:
        return 'review', 'A PDF is not a verified interactive postal subscription/cancellation form'
    sample = unescape(re.sub(r'<[^>]+>', ' ', body.decode('utf-8', 'replace'))).lower()
    sample = re.sub(r'\s+', ' ', sample)
    if any(word in sample[:6000] for word in (
        'page not found', 'the page you requested was not found', '404 error',
        'this page doesn\'t exist', 'domain for sale', 'coming soon',
    )):
        return 'broken', 'Page appears to be a soft 404 or placeholder'
    if any(word in sample[:5000] for word in ('captcha', 'access denied', 'verify you are human', 'just a moment...')):
        return 'review', 'Possible bot challenge; manually verify in a browser'
    if len(sample.strip()) < 45:
        return 'review', 'Insufficient page text; possibly JavaScript-rendered'
    if role == 'subscribe':
        postal = ('catalog', 'print', 'postal', 'mailing address', 'mailbox', 'magazine', 'publication', 'paper')
        if not any(k in sample for k in postal):
            return 'review', 'Page reachable but no clear physical-mail wording'
    elif role == 'evidence':
        if not any(k in sample for k in ('catalog', 'postal', 'direct mail', 'mailing list', 'print', 'communications', 'privacy')):
            return 'review', 'Evidence page reachable but no likely postal opt-out wording'
    else:
        if not any(k in sample for k in ('catalog', 'postal', 'direct mail', 'mailing', 'print', 'privacy', 'contact', 'preferences')):
            return 'review', 'No clear postal cancellation instructions found automatically'
    return 'ok', 'Page reachable; substantive signup/opt-out eligibility still requires human review'


def fetch_page(url: str, *, timeout: int = 12) -> tuple[int, str, bytes, str, list[str]]:
    """GET one public page; follow only a small number of validated HTTPS redirects."""
    opener = build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    current = url
    chain = [url]
    for _ in range(MAX_REDIRECTS + 1):
        public_https_url(current)
        req = Request(current, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/pdf;q=0.7,*/*;q=0.1'})
        try:
            response = opener.open(req, timeout=timeout)
        except HTTPError as exc:
            response = exc
        with response:
            status = response.status
            location = response.headers.get('Location')
            if status in (301, 302, 303, 307, 308) and location:
                new_url = urljoin(current, location)
                public_https_url(new_url)
                if new_url in chain:
                    raise ValueError('Redirect loop')
                current = new_url
                chain.append(current)
                continue
            return status, response.headers.get('Content-Type', '').lower(), response.read(MAX_BODY), current, chain
    raise ValueError('Too many redirects')


def check_url(url: str, role: str, *, timeout: int = 12, fetcher=fetch_page) -> Observation:
    try:
        public_https_url(url, resolve=False)
        status, ctype, body, final, chain = fetcher(url, timeout=timeout)
        state, detail = page_assessment(status, ctype, body, role)
        suggestion = final if final != url and same_organization_host(url, final) and state == 'ok' else ''
        if final != url and not same_organization_host(url, final):
            state, detail = 'review', 'Redirected to a different organizational hostname; verify ownership manually'
        return Observation(url, final, state, status, detail, chain, suggestion)
    except (ValueError, OSError, URLError, TimeoutError, ssl.SSLError) as exc:
        # DNS failures and timeouts are inconclusive; avoid deleting legitimate sites.
        return Observation(url, url, 'review', None, f'{type(exc).__name__}: {exc}', [url])


def replacement_suggestions(url: str, role: str, *, timeout: int = 12, fetcher=fetch_page) -> list[str]:
    """Look for likely replacement URLs on the *official* homepage.

    Suggestions are never adopted silently: a link can lead to a digital-only
    newsletter, a third-party payment gateway, or an unrelated form.
    """
    host = urlsplit(url).hostname
    if not host:
        return []
    homepage = f'https://{host}/'
    try:
        status, ctype, html, final, _ = fetcher(homepage, timeout=timeout)
        if status != 200 or 'html' not in ctype:
            return []
        parser = PageLinks()
        parser.feed(html.decode('utf-8', 'replace'))
        keywords = {
            'subscribe': ('catalog', 'print', 'magazine', 'publication', 'request', 'subscribe'),
            'unsubscribe': ('catalog', 'mailing', 'privacy', 'preference', 'unsubscribe', 'contact'),
            'evidence': ('privacy', 'catalog', 'preferences', 'contact', 'policy'),
        }[role]
        ranked = []
        for href, label in parser.links:
            candidate = urljoin(final, href)
            try:
                public_https_url(candidate, resolve=False)
            except ValueError:
                continue
            if not same_organization_host(url, candidate):
                continue
            description = (href + ' ' + label).lower()
            score = sum(word in description for word in keywords)
            if score:
                ranked.append((-score, candidate))
        return list(dict.fromkeys(link for _, link in sorted(ranked)))[:5]
    except (ValueError, OSError, URLError, TimeoutError, ssl.SSLError):
        return []


def as_report(observation: Observation) -> dict:
    return asdict(observation)
