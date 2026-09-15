import { useEffect, useMemo, useRef, useState } from 'react'
import idlePng from './assets/Bandoletesidle.png'
import walkingPng from './assets/Bandoleteswalking.png'
import beepPng from './assets/bandoletebeep.png'
import cutethongletsPng from './assets/cutethonglets.png'
import treePng from './assets/Tree.png'
import './NpcStage.css'

type Thronglet = {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  desiredAngle: number
  nextWanderIn: number
  // nextBeepIn is no longer used.
  // beepUntil is used both for posing + sprite swap.
  beepUntil: number
  pose: 'idle' | 'walking' | 'beep'
}

type Tree = {
  id: number
  x: number
  y: number
  r: number
}

const THRONGLET_COUNT = 30
const TREE_COUNT = 0

// Collision tuning
const NPC_RADIUS = 18
const TREE_RADIUS = 0

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function rand(min: number, max: number) {
  return min + Math.random() * (max - min)
}

function hypot(x: number, y: number) {
  return Math.sqrt(x * x + y * y)
}

function normalize(x: number, y: number) {
  const len = hypot(x, y)
  if (len < 1e-6) return { x: 0, y: 0, len: 0 }
  return { x: x / len, y: y / len, len }
}

function useImagePreload(srcs: string[]) {
  const [ready, setReady] = useState(false)
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        await Promise.all(
          srcs.map(
            (src) =>
              new Promise<void>((resolve, reject) => {
                const img = new Image()
                img.onload = () => resolve()
                img.onerror = () => reject(new Error(`Failed to load: ${src}`))
                img.src = src
              }),
          ),
        )
        if (!cancelled) setReady(true)
      } catch {
        if (!cancelled) setReady(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [srcs])
  return ready
}

function computeRandomTreesPoisson(
  w: number,
  h: number,
  count: number,
  minDist: number,
  maxTries = 6000,
) {
  const minX = 60
  const maxX = w - 60
  const minY = h * 0.22
  const maxY = h - 18

  const minDist2 = minDist * minDist
  const pts: Array<{ x: number; y: number }> = []

  // seed
  pts.push({ x: rand(minX, maxX), y: rand(minY, maxY) })

  let tries = 0
  while (pts.length < count && tries < maxTries) {
    tries++
    const cand = { x: rand(minX, maxX), y: rand(minY, maxY) }

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

  // If we couldn't reach count (small area / large minDist), fill the rest randomly.
  while (pts.length < count) pts.push({ x: rand(minX, maxX), y: rand(minY, maxY) })

  return pts
}

export default function NpcStage() {
  const stageRef = useRef<HTMLDivElement | null>(null)
  const rafRef = useRef<number | null>(null)
  const lastRef = useRef<number>(performance.now())

  const assets = useMemo(() => {
    return {
      idle: idlePng,
      walking: walkingPng,
      beep: beepPng,
      cute: cutethongletsPng,
      tree: treePng,
    }
  }, [])

  const ready = useImagePreload([assets.idle, assets.walking, assets.beep, assets.cute, assets.tree])

  const [trees] = useState<Tree[]>(() => {
    const list: Tree[] = []
    for (let i = 0; i < TREE_COUNT; i++) list.push({ id: i, x: 0, y: 0, r: TREE_RADIUS })
    return list
  })

  const throngletsRef = useRef<Thronglet[]>([])
  const frameRef = useRef(0)
  const [, forceRender] = useState(0)

  function stageSize() {
    const el = stageRef.current
    if (!el) return { w: 1, h: 1 }
    const rect = el.getBoundingClientRect()
    return { w: rect.width, h: rect.height }
  }

  // Initialize positions once.
  useEffect(() => {
    const { w, h } = stageSize()

    // trees (random but evenly spread)
    {
      const positions = computeRandomTreesPoisson(w, h, TREE_COUNT, 140)
      for (let i = 0; i < trees.length; i++) {
        trees[i].x = positions[i].x
        trees[i].y = positions[i].y
      }
    }

    // thronglets
    if (throngletsRef.current.length === 0) {
      const list: Thronglet[] = []
      for (let i = 0; i < THRONGLET_COUNT; i++) {
        const x = rand(70, w - 70)
        const y = rand(h * 0.45, h - 20)
        list.push({
          id: i,
          x,
          y,
          vx: rand(-28, 28),
          vy: rand(-18, 18),
          desiredAngle: rand(-Math.PI, Math.PI),
          nextWanderIn: rand(0.2, 1.2),
          // nextBeepIn is no longer used.
          beepUntil: 0,
          pose: 'idle',
        })
      }
      throngletsRef.current = list
    }

    forceRender((x) => x + 1)

    // Keep tree spacing on resize too.
    const onResize = () => {
      const { w: nw, h: nh } = stageSize()
      const positions = computeRandomTreesPoisson(nw, nh, TREE_COUNT, 140)
      for (let i = 0; i < trees.length; i++) {
        trees[i].x = positions[i].x
        trees[i].y = positions[i].y
      }
      for (const t of throngletsRef.current) {
        t.x = clamp(t.x, 70, nw - 70)
        t.y = clamp(t.y, nh * 0.45, nh - 20)
      }
      forceRender((x) => x + 1)
    }

    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [trees])

  useEffect(() => {
    if (!ready) return

    const step = (now: number) => {
      const dt = clamp((now - lastRef.current) / 1000, 0, 0.05)
      lastRef.current = now

      const { w, h } = stageSize()
      const thronglets = throngletsRef.current

      // --- Update motion ---
      for (const t of thronglets) {
        // Wander: occasionally pick a new desired direction.
        t.nextWanderIn -= dt
        if (t.nextWanderIn <= 0) {
          t.nextWanderIn = rand(0.6, 1.6)
          t.desiredAngle += rand(-0.95, 0.95)
        }

        const desiredSpeed = rand(18, 42)
        const dx = Math.cos(t.desiredAngle)
        const dy = Math.sin(t.desiredAngle) * 0.6
        const desired = normalize(dx, dy)
        const targetVx = desired.x * desiredSpeed
        const targetVy = desired.y * desiredSpeed

        const steer = 70
        t.vx += clamp(targetVx - t.vx, -steer * dt, steer * dt)
        t.vy += clamp(targetVy - t.vy, -steer * dt, steer * dt)

        const drag = Math.pow(0.985, dt * 60)
        t.vx *= drag
        t.vy *= drag

        t.x += t.vx * dt
        t.y += t.vy * dt

        // Bounds.
        const padX = 40
        const padYTop = 80
        const padYBottom = 18
        if (t.x < padX) {
          t.x = padX
          t.vx = Math.abs(t.vx) * 0.85
          t.desiredAngle = rand(-0.4, 0.4)
        } else if (t.x > w - padX) {
          t.x = w - padX
          t.vx = -Math.abs(t.vx) * 0.85
          t.desiredAngle = Math.PI + rand(-0.4, 0.4)
        }
        if (t.y < padYTop) {
          t.y = padYTop
          t.vy = Math.abs(t.vy) * 0.85
        } else if (t.y > h - padYBottom) {
          t.y = h - padYBottom
          t.vy = -Math.abs(t.vy) * 0.85
        }

        // Pose selection:
        // - if touching recently: beep
        // - else based on speed: walking/idle
        if (now < t.beepUntil) {
          t.pose = 'beep'
        } else {
          const speed = hypot(t.vx, t.vy)
          t.pose = speed > 16 ? 'walking' : 'idle'
        }
      }

      // --- Collisions (cheap) ---
      // NPC vs Trees: push NPCs away so they don't "walk over" trees.
      const avoidTree = NPC_RADIUS + TREE_RADIUS
      const avoidTree2 = avoidTree * avoidTree
      for (const t of thronglets) {
        for (const tr of trees) {
          const dx = t.x - tr.x
          const dy = t.y - tr.y
          const d2 = dx * dx + dy * dy
          if (d2 > 0 && d2 < avoidTree2) {
            const d = Math.sqrt(d2)
            const push = (avoidTree - d) / avoidTree
            const nx = dx / d
            const ny = dy / d
            t.x += nx * push * 24
            t.y += ny * push * 24
            t.vx += nx * push * 40 * dt
            t.vy += ny * push * 40 * dt
          }
        }
      }

      // NPC vs NPC: separate to avoid stacking/overlap.
      const avoidNpc = NPC_RADIUS * 2
      const avoidNpc2 = avoidNpc * avoidNpc
      for (let i = 0; i < thronglets.length; i++) {
        const a = thronglets[i]
        for (let j = i + 1; j < thronglets.length; j++) {
          const b = thronglets[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const d2 = dx * dx + dy * dy
          if (d2 > 0 && d2 < avoidNpc2) {
            const d = Math.sqrt(d2)
            const nx = dx / d
            const ny = dy / d
            const push = (avoidNpc - d) / avoidNpc
            const sx = nx * push * 10
            const sy = ny * push * 10
            a.x += sx
            a.y += sy
            b.x -= sx
            b.y -= sy

            // Rule 1: touching => beep
            const hitBeepUntil = now + 420
            if (a.beepUntil < hitBeepUntil) a.beepUntil = hitBeepUntil
            if (b.beepUntil < hitBeepUntil) b.beepUntil = hitBeepUntil
          }
        }
      }

      // Render throttle (~30fps): update React state every other frame.
      frameRef.current++
      if ((frameRef.current & 1) === 0) forceRender((x) => x + 1)

      rafRef.current = requestAnimationFrame(step)
    }

    rafRef.current = requestAnimationFrame(step)
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [ready, trees])

  const thronglets = throngletsRef.current

  const [hoveredNpcId, setHoveredNpcId] = useState<number | null>(null)

  return (
    <div className="npcFrame">
      <div className="npcStage" ref={stageRef} aria-label="NPC stage">
        {/* Pixel-ish ground plane */}
        <div className="npcGround" aria-hidden="true" />

        {trees.map((tr) => {
          const stageH = stageRef.current?.getBoundingClientRect().height ?? 1
          const scale = 0.75 + 0.45 * (tr.y / stageH)
          const zIndex = Math.floor(500 + tr.y)
          return (
            <div
              key={tr.id}
              className="npcTree"
              style={{
                left: tr.x,
                top: tr.y,
                zIndex,
                transform: `translate(-50%, -100%) scale(${scale.toFixed(3)})`,
                backgroundImage: `url(${assets.tree})`,
              }}
            />
          )
        })}

        {thronglets.map((t) => {
          const rect = stageRef.current?.getBoundingClientRect()
          const h = rect?.height ?? 1
          const scale = 0.82 + 0.4 * (t.y / h)
          const flip = t.vx < 0 ? -1 : 1
          const zIndex = Math.floor(1000 + t.y)
          const poseSrc = t.pose === 'beep' ? assets.beep : t.pose === 'walking' ? assets.walking : assets.idle
          const src = hoveredNpcId === t.id ? assets.cute : poseSrc

          return (
            <div
              key={t.id}
              className={`thronglet ${t.pose === 'walking' ? 'walking' : 'idle'} ${t.pose === 'beep' ? 'beep' : ''}`}
              style={{
                left: t.x,
                top: t.y,
                zIndex,
                // CSS vars used by .thronglet
                ['--scale' as any]: scale.toFixed(3),
                ['--flip' as any]: String(flip),
              }}
              aria-label={`Thronglet ${t.id + 1}`}
              onMouseEnter={() => setHoveredNpcId(t.id)}
              onMouseLeave={() => setHoveredNpcId((cur) => (cur === t.id ? null : cur))}
            >
              <img alt="" src={src} />
            </div>
          )
        })}

        {!ready ? (
          <div className="npcOverlay">Loading assets…</div>
        ) : null}
      </div>
    </div>
  )
}
