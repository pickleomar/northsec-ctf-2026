import type { PublicPresetConfig, RuntimeConfig } from '../types'

export function unsafeMerge<T extends Record<string, any>>(target: T, source: any): T {
  if (!source || typeof source !== 'object') return target

  for (const key of Object.keys(source)) {
    const sv = (source as any)[key]
    const tv = (target as any)[key]

    if (sv && typeof sv === 'object' && !Array.isArray(sv)) {
      if (!tv || typeof tv !== 'object') {
        ;(target as any)[key] = {}
      }
      unsafeMerge((target as any)[key], sv)
    } else {
      ;(target as any)[key] = sv
    }
  }

  return target
}

export function defaultRuntimeConfig(): RuntimeConfig {
  return {
    hiddenModel: {
      m: 0.0,
      b: 0.0,
      noise: 0.25,
      lr: 0.0,
    },
    publicPreset: {
      visuals: {
        hoverScale: 1.18,
        hoverLift: 6,
      },
      ambience: {
        treeDensity: 1,
        canopyScale: 1,
      },
      wander: {
        turnJitter: 0.95,
        cadenceMin: 0.6,
        cadenceMax: 1.6,
        speedBias: 1,
      },
    },
    motion: {
      steer: 70,
      drag: 0.985,
      desiredSpeedMin: 18,
      desiredSpeedMax: 42,
      speedWalkThreshold: 16,
    },
    world: {
      throngletCount: 10,
      treeCount: 15,
      npcRadius: 18,
      treeRadius: 26,
      treeMinDist: 140,
      bounds: {
        padX: 40,
        padYTop: 80,
        padYBottom: 18,
      },
    },
    validate: {
      epsilon: 700,
      cooldownMs: 2500,
    },
  }
}

function safeJsonParse(raw: string | null): any {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

// Hidden but reachable preset load: URL ?preset=<json> and/or localStorage realmPreset.
export function loadUserPreset(): Record<string, any> {
  const url = new URL(window.location.href)
  const raw = url.searchParams.get('preset') ?? url.searchParams.get('preference')
  const fromQuery = safeJsonParse(raw)
  const fromStorage = safeJsonParse(window.localStorage.getItem('realmPreset'))

  const out: Record<string, any> = {}
  if (fromStorage && typeof fromStorage === 'object') unsafeMerge(out, fromStorage)
  if (fromQuery && typeof fromQuery === 'object') unsafeMerge(out, fromQuery)
  return out
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function coerceNumber(value: unknown, fallback: number, min: number, max: number) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback
  return clamp(value, min, max)
}

function applyPublicPreset(cfg: RuntimeConfig, publicPreset: PublicPresetConfig) {
  cfg.publicPreset = publicPreset
  cfg.world.treeCount = Math.max(0, Math.round(cfg.world.treeCount * coerceNumber(publicPreset.ambience.treeDensity, 1, 0.4, 1.8)))
  cfg.motion.desiredSpeedMin *= coerceNumber(publicPreset.wander.speedBias, 1, 0.75, 1.35)
  cfg.motion.desiredSpeedMax *= coerceNumber(publicPreset.wander.speedBias, 1, 0.75, 1.35)
}

export function buildRuntimeConfig(): RuntimeConfig {
  const cfg = defaultRuntimeConfig()
  const preset = loadUserPreset()
  const publicPreset = structuredClone(cfg.publicPreset)

  unsafeMerge(publicPreset as any, preset)
  applyPublicPreset(cfg, publicPreset)

  return cfg
}
