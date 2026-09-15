import type {
  ArchitectLessonsResponse,
  AuthResponse,
  FeedResponse,
  ItemId,
  PurchaseResponse,
  SaveLessonResponse,
  UserProfile,
} from './types'

const TOKEN_KEY = 'enpc_jwt_token'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function buildHeaders(token: string | null, body?: unknown) {
  const headers = new Headers()
  if (body !== undefined) headers.set('content-type', 'application/json')
  if (token) headers.set('authorization', `Bearer ${token}`)
  return headers
}

async function requestJson<T>(path: string, options: RequestInit = {}, token: string | null = loadToken()): Promise<T> {
  const res = await fetch(path, {
    ...options,
    headers: buildHeaders(token, options.body),
  })

  const data = (await res.json().catch(() => ({}))) as { error?: string; message?: string }
  if (!res.ok) {
    throw new ApiError(res.status, data.error ?? data.message ?? `HTTP ${res.status}`)
  }

  return data as T
}

export function loadToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function saveToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY)
}

export function fetchMe(token: string | null = loadToken()) {
  return requestJson<UserProfile>('/api/me', { method: 'GET' }, token)
}

export function registerUser(username: string, password: string) {
  return requestJson<AuthResponse>(
    '/api/auth/register',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    null,
  )
}

export function loginUser(username: string, password: string) {
  return requestJson<AuthResponse>(
    '/api/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    null,
  )
}

export function buyItem(itemId: ItemId, token: string | null = loadToken()) {
  return requestJson<PurchaseResponse>(
    '/api/store/buy',
    {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId }),
    },
    token,
  )
}

export function feedItem(itemId: ItemId, token: string | null = loadToken()) {
  return requestJson<FeedResponse>(
    '/api/feed',
    {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId }),
    },
    token,
  )
}

export function fetchArchitectLessons(token: string | null = loadToken()) {
  return requestJson<ArchitectLessonsResponse>('/api/architect/lessons', { method: 'GET' }, token)
}

export function saveArchitectLesson(npcIndex: number, trigger: string, phrase: string, token: string | null = loadToken()) {
  return requestJson<SaveLessonResponse>(
    '/api/architect/lessons',
    {
      method: 'POST',
      body: JSON.stringify({ npc_index: npcIndex, trigger, phrase }),
    },
    token,
  )
}
