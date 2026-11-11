"""Opt-in, API-keyed searches for public physical-mail source candidates.

Candidates are *not* trusted. An AI response cannot subscribe anyone,
modify default sources, or serve as proof of an unsubscribe method.
"""

from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROMPT = """Find US-accessible organizations currently accepting requests for FREE PHYSICAL
postal mail addressed to the actual requester. Include commercial PRINT catalogs,
church/religious PRINT magazines, nonprofit PRINT newsletters, and political or
policy PRINT circulars. Exclude email-only services, donation-required print
subscriptions, paid trials, publications limited to children or specialized groups,
and print-at-home downloads. Each candidate MUST have (1) an official, publicly
available postal subscription or physical catalog request page, and (2) an official
published instruction for REMOVAL from PHYSICAL POSTAL mail, not just email.
Perform current web research and return ONLY a JSON array of at most 12 objects,
with string keys slug, name, category, subscribe_url, unsubscribe_url,
optout_instructions, evidence_url, notes. For each, provide official HTTPS URLs.
Specify any potentially coupled email/SMS marketing in notes. Do not invent URLs,
assert that forms were submitted, or treat your answer as verification. If a
requirement cannot be established, OMIT the candidate."""


class ProviderError(RuntimeError):
    pass


def json_post(url: str, headers: dict, payload: dict, timeout: int = 90) -> dict:
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers={
        'Content-Type': 'application/json', 'Accept': 'application/json', **headers,
    }, method='POST')
    try:
        with urlopen(req, timeout=timeout) as response:
            data = response.read(2_000_000)
    except HTTPError as exc:
        detail = exc.read(700).decode('utf-8', 'replace')
        raise ProviderError(f'AI provider HTTP {exc.code}: {detail}') from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderError(f'AI provider request failed: {exc}') from exc
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise ProviderError('AI provider returned invalid JSON') from exc


def request_candidates(provider: str, model: str, category: str = '', timeout: int = 90,
                       requester=json_post) -> tuple[str, list[str]]:
    """Return text response and provenance URLs, without exposing API keys."""
    prompt = PROMPT + (f'\nFocus primarily on: {category[:250]}.' if category else '')
    if provider == 'openai':
        key = os.getenv('OPENAI_API_KEY', '')
        if not key:
            raise ProviderError('Set OPENAI_API_KEY in your environment')
        payload = {'model': model or 'gpt-5.5', 'tools': [{'type': 'web_search'}],
                   'tool_choice': 'required', 'input': prompt, 'store': False}
        result = requester('https://api.openai.com/v1/responses',
                           {'Authorization': f'Bearer {key}'}, payload, timeout)
        chunks, citations = [], []
        for item in result.get('output', []):
            for part in item.get('content', []):
                if part.get('text'):
                    chunks.append(part['text'])
                for note in part.get('annotations', []):
                    if note.get('url'):
                        citations.append(note['url'])
        return '\n'.join(chunks), citations
    if provider == 'gemini':
        key = os.getenv('GEMINI_API_KEY', '')
        if not key:
            raise ProviderError('Set GEMINI_API_KEY in your environment')
        model = model or 'gemini-2.5-flash'
        result = requester(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                           {'x-goog-api-key': key},
                           {'contents': [{'parts': [{'text': prompt}]}], 'tools': [{'google_search': {}}]}, timeout)
        chunks, citations = [], []
        for item in result.get('candidates', []):
            chunks.extend(part.get('text', '') for part in item.get('content', {}).get('parts', []))
            citations.extend(chunk.get('web', {}).get('uri', '') for chunk in
                             item.get('groundingMetadata', {}).get('groundingChunks', []))
        return '\n'.join(chunks), [u for u in citations if u]
    if provider == 'perplexity':
        key = os.getenv('PERPLEXITY_API_KEY', '')
        if not key:
            raise ProviderError('Set PERPLEXITY_API_KEY in your environment')
        result = requester('https://api.perplexity.ai/chat/completions',
                           {'Authorization': f'Bearer {key}'},
                           {'model': model or 'sonar', 'messages': [{'role': 'user', 'content': prompt}]}, timeout)
        chunks = [item.get('message', {}).get('content', '') for item in result.get('choices', [])]
        return '\n'.join(chunks), list(result.get('citations', []))
    raise ProviderError('Supported providers: openai, gemini, perplexity')


def parse_candidates(text: str) -> list[dict]:
    """Accept raw JSON or a fenced JSON array, with an upper bound on size."""
    if len(text) > 120_000:
        raise ProviderError('Response exceeds maximum candidate size')
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.I | re.S)
    if match:
        text = match.group(1)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find('['), text.rfind(']')
        if start < 0 or end < start:
            raise ProviderError('Model did not return a JSON candidate list') from None
        try:
            value = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ProviderError('Could not parse model candidate list') from exc
    if isinstance(value, dict):
        value = value.get('sources', [])
    if not isinstance(value, list) or len(value) > 30 or any(not isinstance(x, dict) for x in value):
        raise ProviderError('Expected an array of at most 30 source objects')
    return value
