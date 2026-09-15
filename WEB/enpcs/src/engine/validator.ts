import type { ValidationChallenge, ValidationPayload, ValidationResponse } from '../types'

export async function fetchValidationChallenge(seed: number): Promise<ValidationChallenge> {
  const res = await fetch(`/api/challenge?seed=${encodeURIComponent(String(seed))}`)

  if (!res.ok) {
    throw new Error(`challenge HTTP ${res.status}`)
  }

  return (await res.json()) as ValidationChallenge
}

export async function validateOnServer(payload: ValidationPayload): Promise<ValidationResponse> {
  const res = await fetch('/api/validate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    return { success: false, score: Number.POSITIVE_INFINITY, message: `HTTP ${res.status}` }
  }

  return (await res.json()) as ValidationResponse
}
