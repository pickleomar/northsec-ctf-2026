#!/usr/bin/env python3
"""
Folio — Admin Review Bot
========================
Runs as a background service (or spawned per-project by the main app).
Authenticates as the admin account and fetches each pending project's
preview URL to confirm the deck is live before marking it as reviewed.

Usage (standalone):
    python3 bot.py --project-id 42 --base-url http://localhost:5000
"""

import argparse
import json
import logging
import sys
import time
from urllib.parse import urljoin, unquote

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ReviewBot] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('folio.bot')


class ReviewBot:
    """
    Authenticated HTTP client that reviews project preview links.

    Lifecycle:
      1. authenticate()   — POST /v1/api/auth/signin, store session cookie
      2. review(slug)     — resolve slug → fetch URL with admin session
      3. mark_reviewed()  — update project status

    The preview slug is URL-decoded before being joined with the base URL.
    This mirrors how the frontend's buildPreviewEndpoint() uses new URL() to
    normalize slugs — both decode percent-encoded characters before resolution.
    """

    PREVIEW_BASE = '/v1/api/projects/preview/'

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session  = requests.Session()
        self.session.headers.update({'User-Agent': 'Folio-ReviewBot/2.1 (internal)'})

    # ── Auth ──────────────────────────────────────────────────────────────────

    def authenticate(self) -> None:
        url = f'{self.base_url}/v1/api/auth/signin'
        r   = self.session.post(
            url,
            json={'username': self.username, 'password': self.password},
            timeout=10,
        )
        if r.status_code != 200:
            raise RuntimeError(f'Authentication failed: {r.status_code} {r.text[:200]}')
        log.info('Authenticated as %s', self.username)

    # ── Preview fetch ─────────────────────────────────────────────────────────

    def resolve_preview_url(self, raw_slug: str) -> str:
        """
        Convert a stored preview slug into a fully-qualified URL.

        Steps:
          1. URL-decode the slug (handles percent-encoded values from some clients).
          2. Join against the preview catalog base using RFC 3986 resolution.
          3. Return the resolved URL.

        Example:
          raw_slug = 'my-series-a-deck'
          → http://host/x/projects/preview/my-series-a-deck

          raw_slug = '%2e%2e/account/notifications/unsubscribe?email=x%40y.z'
          → unquote → '../account/notifications/unsubscribe?email=x@y.z'
          → urljoin → http://host/x/account/notifications/unsubscribe?email=x@y.z
        """
        catalog_base = self.base_url + self.PREVIEW_BASE
        decoded_slug = unquote(raw_slug)
        return urljoin(catalog_base, decoded_slug)

    def fetch_preview(self, raw_slug: str) -> requests.Response:
        target = self.resolve_preview_url(raw_slug)
        log.info('Fetching preview: %s  (slug=%r)', target, raw_slug)
        return self.session.get(
            target,
            timeout=10,
            allow_redirects=True,
        )

    # ── Project review ────────────────────────────────────────────────────────

    def review_project(self, project_id: int) -> dict:
        """
        Full review flow for a single project.
        Returns a summary dict with resolved URL and response status.
        """
        # 1. Load project record
        r = self.session.get(f'{self.base_url}/v1/api/projects/{project_id}', timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f'Project {project_id} not found: {r.status_code}')
        project = r.json()

        slug = project.get('preview_slug', '')
        if not slug:
            log.warning('Project %d has no preview_slug', project_id)
            return {'project_id': project_id, 'skipped': True}

        # 2. Fetch the preview (CSPT trigger point)
        resp = self.fetch_preview(slug)
        log.info('Preview response: %d for project %d', resp.status_code, project_id)

        return {
            'project_id':   project_id,
            'slug':         slug,
            'resolved_url': self.resolve_preview_url(slug),
            'status_code':  resp.status_code,
        }


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Folio Admin Review Bot')
    parser.add_argument('--base-url',    default='http://localhost:5000')
    parser.add_argument('--username',    default='admin')
    parser.add_argument('--password',    default='Adm1n_F0l10_S3cr3t!')
    parser.add_argument('--project-id',  type=int, required=True)
    parser.add_argument('--delay',       type=float, default=2.0,
                        help='Seconds to wait before reviewing (simulates human latency)')
    args = parser.parse_args()

    time.sleep(args.delay)

    bot = ReviewBot(args.base_url, args.username, args.password)
    try:
        bot.authenticate()
        result = bot.review_project(args.project_id)
        print(json.dumps(result, indent=2))
    except Exception as e:
        log.error('Bot failed: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
