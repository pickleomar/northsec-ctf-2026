/**
 * Folio Platform — API Client
 * v2.4.1
 */

const _xns = '/v1/api'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  signup:  (username, email, password) =>
              _post(`${_xns}/auth/signup`, { username, email, password }),
  signin:  (username, password) =>
              _post(`${_xns}/auth/signin`, { username, password }),
  signout: ()                           => _post(`${_xns}/auth/signout`),
  whoami:  ()                           => _get(`${_xns}/auth/whoami`),

  requestRecovery: (username) =>
    _post(`${_xns}/auth/recover`, { username }),

  confirmRecovery: (token, password) =>
    _post(`${_xns}/auth/recover/confirm`, { token, password }),
}

// ── Projects ──────────────────────────────────────────────────────────────────
export const projectsApi = {
  list:    ()                          => _get(`${_xns}/projects`),
  getById: (id)                        => _get(`${_xns}/projects/${id}`),
  create:  (name, description, slug)   =>
              _post(`${_xns}/projects`, { name, description, preview_slug: slug }),

  /**
   * Load live preview metadata for a project.
   *
   * Uses buildPreviewEndpoint() to normalize the stored slug against the
   * catalog base path before fetching. This mirrors what the admin review
   * bot does server-side when it validates submitted previews.
   *
   * @param {string} rawSlug - The preview_slug value from the project record
   */
  fetchPreview: (rawSlug) => {
    const endpoint = buildPreviewEndpoint(rawSlug)
    if (!endpoint) return Promise.resolve(new Response('{}', { status: 204 }))
    return _get(endpoint)
  },
}

// ── Account ───────────────────────────────────────────────────────────────────
export const accountApi = {
  profile:        ()                       => _get(`${_xns}/account/profile`),
  updateProfile:  (display_name, bio, csrf) =>
    _patch(`${_xns}/account/profile`, { display_name, bio }, csrf),

  updateSecurity: (current_password, new_password, csrf) =>
    _post(`${_xns}/account/security`, { current_password, new_password }, csrf),

  notifications:       ()           => _get(`${_xns}/account/notifications`),
  updateNotifications: (notify_email, csrf) =>
    _patch(`${_xns}/account/notifications`, { notify_email }, csrf),
}

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationsApi = {
  /**
   * Fetch notification feed for the current user.
   * Items appear here only when notify_email is a @dar-lmohsinin.ma address —
   * external addresses receive notifications via SMTP only.
   * Intended payloads are operational (deck review + admin workflow updates).
   */
  feed: () => _get(`${_xns}/notifications/feed`),
}

// ── Analytics ────────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: () => _get(`${_xns}/analytics/overview`),
}

// ── Messages ──────────────────────────────────────────────────────────────────
export const messagesApi = {
  list: () => _get(`${_xns}/messages`),
}

// ── Flag ──────────────────────────────────────────────────────────────────────
export const flagApi = {
  capture: () => _get(`${_xns}/capture`),
}

// ── URL normalization ─────────────────────────────────────────────────────────

/**
 * Resolves a project preview slug into a routable API path.
 *
 * Behavior mirrors what the review bot does server-side:
 *   1. Treat the slug as a URL reference relative to the preview catalog root.
 *   2. Resolve with the browser's URL parser to normalize dots and slashes.
 *   3. Reject cross-origin results — preview slugs must stay on this origin.
 *   4. Return the resolved pathname + search, ready for fetch().
 *
 * This allows slugs like "my-deck-2024" to map to:
 *   /v1/api/projects/preview/my-deck-2024
 *
 * @param  {string} slug
 * @returns {string|null}
 */
function buildPreviewEndpoint(slug) {
  if (!slug) return null
  const catalogRoot = `${window.location.origin}${_xns}/projects/preview/`
  try {
    const resolved = new URL(slug, catalogRoot)
    if (resolved.origin !== window.location.origin) {
      // Cross-origin preview slugs are not supported
      return null
    }
    return resolved.pathname + resolved.search
  } catch {
    // Fallback: treat as a plain slug segment
    return `${_xns}/projects/preview/${encodeURIComponent(slug)}`
  }
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

function _get(url) {
  return fetch(url, {
    credentials: 'include',
    headers: { 'X-Requested-With': 'FolioClient/2' },
  })
}

function _post(url, body, csrfToken) {
  return fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'FolioClient/2',
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
}

function _patch(url, body, csrfToken) {
  return fetch(url, {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'FolioClient/2',
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
}
