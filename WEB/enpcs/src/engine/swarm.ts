import type { BallEntity, RuntimeConfig, SwarmEvent, Thronglet, Tree } from '../types'
import { computeLoss } from './alignment'

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function hypot(x: number, y: number) {
  return Math.sqrt(x * x + y * y)
}

function normalize(x: number, y: number) {
  const len = hypot(x, y)
  if (len < 1e-6) return { x: 0, y: 0, len: 0 }
  return { x: x / len, y: y / len, len }
}

function rand(rng: () => number, min: number, max: number) {
  return min + rng() * (max - min)
}

function computeRandomTreesPoisson(rng: () => number, w: number, h: number, count: number, minDist: number) {
  const minX = 60
  const maxX = w - 60
  const minY = h * 0.22
  const maxY = h - 18

  const minDist2 = minDist * minDist
  const pts: Array<{ x: number; y: number }> = []

  let tries = 0
  while (pts.length < count && tries < 15000) {
    tries++
    const cand = { x: rand(rng, minX, maxX), y: rand(rng, minY, maxY) }

    const relCandX = cand.x / w
    const relCandY = cand.y / h
    if (Math.abs(relCandX - relCandY) < 0.15) continue

    let ok = true
    for (let i = 0; i < pts.length; i++) {
      const dx = cand.x - pts[i].x
      const dy = cand.y - pts[i].y
      if (dx * dx + dy * dy < minDist2) {
        ok = false
        break
      }
    }
    if (ok) pts.push(cand)
  }

  while (pts.length < count) {
    pts.push({ x: rand(rng, minX, maxX), y: rand(rng, minY, maxY) })
  }

  return pts
}

export type SwarmSnapshot = {
  thronglets: Thronglet[]
  trees: Tree[]
  balls: BallEntity[]
  loss: number
  stage: { w: number; h: number }
  publicPreset: RuntimeConfig['publicPreset']
}

export class SwarmEngine {
  private rng: () => number
  public readonly seed: number
  public config: RuntimeConfig

  public thronglets: Thronglet[] = []
  public trees: Tree[] = []
  public stage = { w: 1, h: 1 }
  public balls: BallEntity[] = []
  public loss = 1
  private nextBallId = 0
  private pendingEvents: SwarmEvent[] = []

  constructor(seed: number, config: RuntimeConfig) {
    this.seed = seed
    this.rng = mulberry32(seed)
    this.config = config
  }

  init(w: number, h: number) {
    this.stage = { w, h }
    const { world } = this.config

    const pts = computeRandomTreesPoisson(this.rng, w, h, world.treeCount, world.treeMinDist)
    this.trees = pts.map((p, i) => ({ id: i, x: p.x, y: p.y, r: world.treeRadius }))

    this.thronglets = []
    for (let i = 0; i < world.throngletCount; i++) {
      this.thronglets.push({
        id: i,
        x: rand(this.rng, 70, w - 70),
        y: rand(this.rng, h * 0.2, h - 20),
        vx: rand(this.rng, -28, 28),
        vy: rand(this.rng, -18, 18),
        desiredAngle: rand(this.rng, -Math.PI, Math.PI),
        nextWanderIn: rand(this.rng, 0.2, 1.2),
        beepUntil: 0,
        nextTouchSpeechAt: 0,
        nextBallSpeechAt: 0,
        pose: 'idle',
      })
    }

    this.balls = []
    this.nextBallId = 0
    this.loss = computeLoss(this.thronglets)
  }

  resize(_w: number, _h: number) {}

  dropBall(x: number, y: number) {
    const radius = 18
    this.balls.push({
      id: this.nextBallId++,
      active: true,
      x: clamp(x, radius, this.stage.w - radius),
      y: clamp(y, 96, this.stage.h - radius),
      vx: rand(this.rng, -24, 24),
      vy: rand(this.rng, -16, 16),
      radius,
    })
  }

  triggerNpcReaction(npcId: number, durationMs = 800) {
    const target = this.thronglets.find((npc) => npc.id === npcId)
    if (!target) return
    target.beepUntil = performance.now() + durationMs
    target.pose = 'beep'
  }

  consumeEvents() {
    const events = this.pendingEvents
    this.pendingEvents = []
    return events
  }

  private queueEvent(event: SwarmEvent) {
    this.pendingEvents.push(event)
  }

  private resolveHiddenModel() {
    const probe = {} as Record<string, unknown>
    const hidden = this.config.hiddenModel

    const m = typeof probe.m === 'number' ? probe.m : hidden.m
    const b = typeof probe.b === 'number' ? probe.b : hidden.b
    const noise = typeof probe.noise === 'number' ? probe.noise : hidden.noise
    const lr = typeof probe.lr === 'number' ? probe.lr : hidden.lr

    return { m, b, noise, lr }
  }

  tick(dt: number, nowMs: number) {
    const { w, h } = this.stage
    const { motion, publicPreset, world } = this.config
    const { m, b, noise, lr } = this.resolveHiddenModel()
    const { cadenceMax, cadenceMin, turnJitter } = publicPreset.wander

    for (const t of this.thronglets) {
      t.nextWanderIn -= dt
      if (t.nextWanderIn <= 0) {
        t.nextWanderIn = rand(this.rng, cadenceMin, cadenceMax)
        t.desiredAngle += rand(this.rng, -turnJitter, turnJitter)
      }

      const desiredSpeed = rand(this.rng, motion.desiredSpeedMin, motion.desiredSpeedMax)
      const dx = Math.cos(t.desiredAngle)
      const dy = Math.sin(t.desiredAngle) * 0.6
      const desired = normalize(dx, dy)
      const targetVx = desired.x * desiredSpeed
      const targetVy = desired.y * desiredSpeed

      t.vx += clamp(targetVx - t.vx, -motion.steer * dt, motion.steer * dt)
      t.vy += clamp(targetVy - t.vy, -motion.steer * dt, motion.steer * dt)

      const drag = Math.pow(motion.drag, dt * 60)
      t.vx *= drag
      t.vy *= drag

      const targetY = m * t.x + b
      const err = targetY - t.y
      const jitter = rand(this.rng, -1, 1) * noise * 12
      t.vy += (err * lr + jitter) * dt * 60

      t.x += t.vx * dt
      t.y += t.vy * dt

      const { padX, padYTop, padYBottom } = world.bounds
      if (t.x < padX) {
        t.x = padX
        t.vx = Math.abs(t.vx) * 0.85
        t.desiredAngle = rand(this.rng, -0.4, 0.4)
      } else if (t.x > w - padX) {
        t.x = w - padX
        t.vx = -Math.abs(t.vx) * 0.85
        t.desiredAngle = Math.PI + rand(this.rng, -0.4, 0.4)
      }

      if (t.y < padYTop) {
        t.y = padYTop
        t.vy = Math.abs(t.vy) * 0.85
      } else if (t.y > h - padYBottom) {
        t.y = h - padYBottom
        t.vy = -Math.abs(t.vy) * 0.85
      }

      if (nowMs < t.beepUntil) {
        t.pose = 'beep'
      } else {
        const speed = hypot(t.vx, t.vy)
        t.pose = speed > motion.speedWalkThreshold ? 'walking' : 'idle'
      }
    }

    const avoidTree = world.npcRadius + world.treeRadius
    const avoidTree2 = avoidTree * avoidTree
    for (const t of this.thronglets) {
      for (const tr of this.trees) {
        const dx = t.x - tr.x
        const dy = t.y - tr.y
        const d2 = dx * dx + dy * dy
        if (d2 > 0 && d2 < avoidTree2) {
          const d = Math.sqrt(d2)
          const push = ((avoidTree - d) / avoidTree) * 0.15
          const nx = dx / d
          const ny = dy / d
          t.x += nx * push * 24
          t.y += ny * push * 24
          t.vx += nx * push * 40 * dt
          t.vy += ny * push * 40 * dt
        }
      }
    }

    const avoidNpc = world.npcRadius * 2
    const avoidNpc2 = avoidNpc * avoidNpc
    for (let i = 0; i < this.thronglets.length; i++) {
      const a = this.thronglets[i]
      for (let j = i + 1; j < this.thronglets.length; j++) {
        const bNpc = this.thronglets[j]
        const dx = a.x - bNpc.x
        const dy = a.y - bNpc.y
        const d2 = dx * dx + dy * dy
        if (d2 > 0 && d2 < avoidNpc2) {
          const d = Math.sqrt(d2)
          const push = ((avoidNpc - d) / avoidNpc) * 0.15
          const nx = dx / d
          const ny = dy / d
          a.x += nx * push * 24
          a.y += ny * push * 24
          a.vx += nx * push * 40 * dt
          a.vy += ny * push * 40 * dt
          bNpc.x -= nx * push * 24
          bNpc.y -= ny * push * 24
          bNpc.vx -= nx * push * 40 * dt
          bNpc.vy -= ny * push * 40 * dt

          if (nowMs >= a.nextTouchSpeechAt) {
            a.nextTouchSpeechAt = nowMs + 1200
            this.queueEvent({ npcId: a.id, trigger: 'touch_enpc' })
          }
          if (nowMs >= bNpc.nextTouchSpeechAt) {
            bNpc.nextTouchSpeechAt = nowMs + 1200
            this.queueEvent({ npcId: bNpc.id, trigger: 'touch_enpc' })
          }
        }
      }
    }

    for (const ball of this.balls) {
      if (!ball.active) continue
      ball.vx *= Math.pow(0.992, dt * 60)
      ball.vy *= Math.pow(0.992, dt * 60)
      ball.x += ball.vx * dt
      ball.y += ball.vy * dt

      if (ball.x < ball.radius) {
        ball.x = ball.radius
        ball.vx = Math.abs(ball.vx) * 0.9
      } else if (ball.x > w - ball.radius) {
        ball.x = w - ball.radius
        ball.vx = -Math.abs(ball.vx) * 0.9
      }

      if (ball.y < 92) {
        ball.y = 92
        ball.vy = Math.abs(ball.vy) * 0.9
      } else if (ball.y > h - ball.radius) {
        ball.y = h - ball.radius
        ball.vy = -Math.abs(ball.vy) * 0.9
      }

      const reach = world.npcRadius + ball.radius
      const reach2 = reach * reach
      for (const t of this.thronglets) {
        const dx = ball.x - t.x
        const dy = ball.y - (t.y - 18)
        const d2 = dx * dx + dy * dy
        if (d2 > 0 && d2 < reach2) {
          const d = Math.sqrt(d2)
          const nx = dx / d
          const ny = dy / d
          const impulse = (reach - d) * 1.1
          ball.x += nx * impulse * 0.45
          ball.y += ny * impulse * 0.45
          ball.vx += nx * (Math.abs(t.vx) + 18) * 0.18
          ball.vy += ny * (Math.abs(t.vy) + 12) * 0.18
          t.vx -= nx * 16 * dt
          t.vy -= ny * 12 * dt
          t.beepUntil = Math.max(t.beepUntil, nowMs + 180)

          if (nowMs >= t.nextBallSpeechAt) {
            t.nextBallSpeechAt = nowMs + 900
            this.queueEvent({ npcId: t.id, trigger: 'kick_ball' })
          }
        }
      }

      if (Math.abs(ball.vx) + Math.abs(ball.vy) < 2) {
        ball.vx += rand(this.rng, -6, 6) * dt
        ball.vy += rand(this.rng, -4, 4) * dt
      }
    }

    this.loss = computeLoss(this.thronglets)
  }

  snapshot(): SwarmSnapshot {
    return {
      thronglets: this.thronglets,
      trees: this.trees,
      balls: this.balls,
      loss: this.loss,
      stage: this.stage,
      publicPreset: this.config.publicPreset,
    }
  }
}
