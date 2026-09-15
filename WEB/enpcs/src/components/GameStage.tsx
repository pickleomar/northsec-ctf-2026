import { useEffect, useMemo, useRef, useState } from 'react'
import NpcStage, { useImagePreload } from './NpcStage'
import { buildRuntimeConfig } from '../engine/config'
import { SwarmEngine, type SwarmSnapshot } from '../engine/swarm'
import { fetchValidationChallenge, validateOnServer } from '../engine/validator'
import type { EnpcTrigger, ItemId } from '../types'

const ENGINE_SEED = 0x1337cafe
const NPC_TARGET_RADIUS = 68
const VALIDATION_MODEL = { m: 0, b: 0, noise: 0.25, lr: 0 }

type Props = {
  architectMode: boolean
  draggedItemId: ItemId | null
  ballSpawn: { x: number; y: number; nonce: number } | null
  lessonsMap: Record<number, Partial<Record<EnpcTrigger, string>>>
  manualTriggerEvent: { npcId: number; trigger: EnpcTrigger; nonce: number } | null
  npcNames: string[]
  onDropItem: (point: { x: number; y: number; npcId: number | null }) => void
  onFlagReveal?: (flag: string) => void
}

export default function GameStage({
  architectMode,
  draggedItemId,
  ballSpawn,
  lessonsMap,
  manualTriggerEvent,
  npcNames,
  onDropItem,
  onFlagReveal,
}: Props) {
  const runtimeConfig = useMemo(() => buildRuntimeConfig(), [])
  const engineRef = useRef<SwarmEngine | null>(null)
  const rafRef = useRef<number | null>(null)
  const lastRef = useRef<number>(performance.now())
  const lastBallNonceRef = useRef<number | null>(null)
  const lastManualNonceRef = useRef<number | null>(null)
  const lessonsMapRef = useRef(lessonsMap)
  const speechTimersRef = useRef<Map<number, number>>(new Map())
  const validationStateRef = useRef({ inFlight: false, lastAttemptAt: 0, solved: false })

  const [hoveredNpcId, setHoveredNpcId] = useState<number | null>(null)
  const [previewNpcId, setPreviewNpcId] = useState<number | null>(null)
  const [snapshot, setSnapshot] = useState<SwarmSnapshot | null>(null)
  const [speechByNpcId, setSpeechByNpcId] = useState<Record<number, string>>({})

  useEffect(() => {
    lessonsMapRef.current = lessonsMap
  }, [lessonsMap])

  const showSpeech = (npcId: number, trigger: EnpcTrigger) => {
    const text = lessonsMapRef.current[npcId]?.[trigger]
    if (!text) return

    const existingTimer = speechTimersRef.current.get(npcId)
    if (existingTimer) window.clearTimeout(existingTimer)
    setSpeechByNpcId((current) => ({ ...current, [npcId]: text }))
    const timeoutId = window.setTimeout(() => {
      setSpeechByNpcId((current) => {
        const next = { ...current }
        delete next[npcId]
        return next
      })
      speechTimersRef.current.delete(npcId)
    }, 2300)
    speechTimersRef.current.set(npcId, timeoutId)
  }

  const assetsReady = useImagePreload([
    new URL('../assets/Bandoletesidle.png', import.meta.url).pathname,
    new URL('../assets/Bandoleteswalking.png', import.meta.url).pathname,
    new URL('../assets/bandoletebeep.png', import.meta.url).pathname,
    new URL('../assets/cutethonglets.png', import.meta.url).pathname,
    new URL('../assets/Tree.png', import.meta.url).pathname,
    new URL('../assets/ball.png', import.meta.url).pathname,
    new URL('../assets/annotation.png', import.meta.url).pathname,
  ])

  useEffect(() => {
    engineRef.current = new SwarmEngine(ENGINE_SEED, runtimeConfig)

    const onResize = () => {
      const el = document.querySelector('.npcStage') as HTMLElement | null
      if (!el) return
      const rect = el.getBoundingClientRect()
      engineRef.current?.resize(rect.width, rect.height)
      if (engineRef.current) setSnapshot(engineRef.current.snapshot())
    }

    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [runtimeConfig])

  useEffect(() => {
    if (!assetsReady) return
    const eng = engineRef.current
    if (!eng) return

    const bootId = requestAnimationFrame(() => {
      const el = document.querySelector('.npcStage') as HTMLElement | null
      const rect = el?.getBoundingClientRect()
      eng.init(rect?.width || 800, rect?.height || 600)
      setSnapshot(eng.snapshot())

      const tick = (now: number) => {
        const engine = engineRef.current
        if (!engine) return

        const dt = Math.min(Math.max((now - lastRef.current) / 1000, 0), 0.05)
        lastRef.current = now
        engine.tick(dt, now)
        for (const event of engine.consumeEvents()) showSpeech(event.npcId, event.trigger)

        if (((now / 16) | 0) % 2 === 0) setSnapshot(engine.snapshot())
        rafRef.current = requestAnimationFrame(tick)
      }

      rafRef.current = requestAnimationFrame(tick)
    })

    return () => {
      cancelAnimationFrame(bootId)
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
      for (const timerId of speechTimersRef.current.values()) window.clearTimeout(timerId)
      speechTimersRef.current.clear()
    }
  }, [assetsReady])

  useEffect(() => {
    if (!ballSpawn || lastBallNonceRef.current === ballSpawn.nonce) return
    lastBallNonceRef.current = ballSpawn.nonce
    engineRef.current?.dropBall(ballSpawn.x, ballSpawn.y)
    if (engineRef.current) setSnapshot(engineRef.current.snapshot())
  }, [ballSpawn])

  useEffect(() => {
    if (!manualTriggerEvent || lastManualNonceRef.current === manualTriggerEvent.nonce) return
    lastManualNonceRef.current = manualTriggerEvent.nonce
    engineRef.current?.triggerNpcReaction(manualTriggerEvent.npcId)
    showSpeech(manualTriggerEvent.npcId, manualTriggerEvent.trigger)
  }, [manualTriggerEvent])

  useEffect(() => {
    if (!snapshot) return

    const validationState = validationStateRef.current
    if (validationState.solved || validationState.inFlight) return

    const now = Date.now()
    if (now - validationState.lastAttemptAt < runtimeConfig.validate.cooldownMs) return

    const engine = engineRef.current
    if (!engine) return

    validationState.inFlight = true
    validationState.lastAttemptAt = now

    const payloadBase = {
      seed: engine.seed,
      model: VALIDATION_MODEL,
      positions: snapshot.thronglets.map((npc) => [npc.x, npc.y] as [number, number]),
      stage: snapshot.stage,
    }

    void fetchValidationChallenge(payloadBase.seed)
      .then((challenge) =>
        validateOnServer({
          ...payloadBase,
          challengeToken: challenge.token,
        }),
      )
      .then((result) => {
        if (!result.success || !result.flag) return
        validationStateRef.current.solved = true
        onFlagReveal?.(result.flag)
      })
      .catch(() => {})
      .finally(() => {
        validationStateRef.current.inFlight = false
      })
  }, [onFlagReveal, runtimeConfig.validate.cooldownMs, snapshot])

  useEffect(() => {
    if (!architectMode || !draggedItemId || draggedItemId === 'ball') {
      setPreviewNpcId(null)
    }
  }, [architectMode, draggedItemId])

  const findTargetNpcId = (point: { x: number; y: number }) => {
    const thronglets = snapshot?.thronglets ?? []
    let npcId: number | null = null
    let best = NPC_TARGET_RADIUS * NPC_TARGET_RADIUS

    for (const npc of thronglets) {
      const dx = npc.x - point.x
      const dy = npc.y - 18 - point.y
      const dist = dx * dx + dy * dy
      if (dist <= best) {
        best = dist
        npcId = npc.id
      }
    }

    return npcId
  }

  const handleStageDragMove = (point: { x: number; y: number }) => {
    if (!architectMode || !draggedItemId || draggedItemId === 'ball') {
      setPreviewNpcId(null)
      return
    }
    setPreviewNpcId(findTargetNpcId(point))
  }

  const handleStageDrop = (point: { x: number; y: number }) => {
    const npcId = findTargetNpcId(point)
    setPreviewNpcId(null)
    onDropItem({ ...point, npcId })
  }

  return snapshot ? (
    <NpcStage
      snapshot={snapshot}
      hoveredNpcId={hoveredNpcId}
      speechByNpcId={speechByNpcId}
      onHoverNpc={setHoveredNpcId}
      npcNames={architectMode ? npcNames : []}
      targetedFeedNpcId={previewNpcId}
      dragActive={draggedItemId !== null}
      onStageDragLeave={() => setPreviewNpcId(null)}
      onStageDragMove={handleStageDragMove}
      onStageDrop={handleStageDrop}
    />
  ) : (
    <div className="npcFrame">
      <div className="npcOverlay">Loading arena...</div>
    </div>
  )
}
