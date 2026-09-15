import { type CSSProperties, useEffect, useMemo, useRef, useState } from 'react'
import idlePng from '../assets/Bandoletesidle.png'
import walkingPng from '../assets/Bandoleteswalking.png'
import beepPng from '../assets/bandoletebeep.png'
import annotationPng from '../assets/annotation.png'
import cutethongletsPng from '../assets/cutethonglets.png'
import treePng from '../assets/Tree.png'
import ballPng from '../assets/ball.png'
import '../NpcStage.css'

import type { SwarmSnapshot } from '../engine/swarm'

type Props = {
  snapshot: SwarmSnapshot
  npcNames?: string[]
  speechByNpcId?: Record<number, string>
  onHoverNpc?: (id: number | null) => void
  hoveredNpcId?: number | null
  targetedFeedNpcId?: number | null
  dragActive?: boolean
  onStageDragMove?: (point: { x: number; y: number }) => void
  onStageDragLeave?: () => void
  onStageDrop?: (point: { x: number; y: number }) => void
}

export default function NpcStage({
  snapshot,
  npcNames = [],
  speechByNpcId = {},
  hoveredNpcId,
  onHoverNpc,
  targetedFeedNpcId = null,
  dragActive = false,
  onStageDragMove,
  onStageDragLeave,
  onStageDrop,
}: Props) {
  const stageRef = useRef<HTMLDivElement | null>(null)

  const assets = useMemo(
    () => ({
      idle: idlePng,
      walking: walkingPng,
      beep: beepPng,
      annotation: annotationPng,
      cute: cutethongletsPng,
      tree: treePng,
      ball: ballPng,
    }),
    [],
  )

  const { thronglets, trees, balls } = snapshot

  const projectStagePoint = (clientX: number, clientY: number) => {
    if (!stageRef.current) return null
    const rect = stageRef.current.getBoundingClientRect()
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    }
  }

  return (
    <div className="npcFrame">
      <div
        className={`npcStage ${dragActive ? 'dropReady' : ''}`}
        ref={stageRef}
        aria-label="NPC stage"
        onDragOver={(event) => {
          if (!onStageDrop && !onStageDragMove) return
          event.preventDefault()
          event.dataTransfer.dropEffect = 'move'
          const point = projectStagePoint(event.clientX, event.clientY)
          if (point) onStageDragMove?.(point)
        }}
        onDragLeave={(event) => {
          if (!stageRef.current) return
          const relatedTarget = event.relatedTarget
          if (relatedTarget instanceof Node && stageRef.current.contains(relatedTarget)) return
          onStageDragLeave?.()
        }}
        onDrop={(event) => {
          if (!onStageDrop || !stageRef.current) return
          event.preventDefault()
          onStageDragLeave?.()
          const point = projectStagePoint(event.clientX, event.clientY)
          if (point) onStageDrop(point)
        }}
      >
        <div className="npcGround" aria-hidden="true" />

        {trees.map((tr) => {
          const stageH = snapshot.stage.h || 1
          const scale = (0.75 + 0.45 * (tr.y / stageH)) * snapshot.publicPreset.ambience.canopyScale
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
          const h = snapshot.stage.h || 1
          const isHovered = hoveredNpcId === t.id
          const hoverScale = isHovered ? snapshot.publicPreset.visuals.hoverScale : 1
          const hoverLift = isHovered ? snapshot.publicPreset.visuals.hoverLift : 0
          const scale = (0.82 + 0.4 * (t.y / h)) * hoverScale
          const flip = t.vx < 0 ? -1 : 1
          const zIndex = Math.floor(1000 + t.y)
          const npcName = npcNames[t.id]

          const isBeeping = targetedFeedNpcId === t.id || t.pose === 'beep'
          const poseSrc = isBeeping ? assets.beep : t.pose === 'walking' ? assets.walking : assets.idle
          const src = isHovered && !isBeeping ? assets.cute : poseSrc
          const style = {
            left: t.x,
            top: t.y - hoverLift,
            zIndex
          } as CSSProperties
          const actorStyle = {
            '--scale': scale.toFixed(3),
            '--flip': String(flip),
          } as CSSProperties

          return (
            <div
              key={t.id}
              className={`thronglet ${t.pose === 'walking' ? 'walking' : 'idle'} ${isBeeping ? 'beep' : ''}`}
              style={style}
              aria-label={npcName ? `ENPC ${t.id + 1} ${npcName}` : `ENPC ${t.id + 1}`}
              onMouseEnter={() => onHoverNpc?.(t.id)}
              onMouseLeave={() => onHoverNpc?.(null)}
            >
              {isHovered && npcName ? <div className="npcNameTag">#{t.id + 1} {npcName}</div> : null}
              {speechByNpcId[t.id] ? (
                <div className="npcSpeech" style={{ backgroundImage: `url(${assets.annotation})` }}>
                  <span className="npcSpeechText">{speechByNpcId[t.id]}</span>
                </div>
              ) : null}
              <div className="throngletActor" style={actorStyle}>
                <img alt="" src={src} />
              </div>
            </div>
          )
        })}

        {balls.map((ball) =>
          ball.active ? (
            <div
              key={ball.id}
              className="npcBall"
              style={{
                left: ball.x,
                top: ball.y,
                width: ball.radius * 2,
                height: ball.radius * 2,
                backgroundImage: `url(${assets.ball})`,
              }}
            />
          ) : null,
        )}

        {dragActive ? <div className="npcDropHint">Drop item into the arena</div> : null}
      </div>
    </div>
  )
}

export function useImagePreload(srcs: string[]) {
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
