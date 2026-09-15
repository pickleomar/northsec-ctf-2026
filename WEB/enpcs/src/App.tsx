import { type CSSProperties, type FormEvent, useEffect, useMemo, useState } from 'react'
import './App.css'
import appleItemPng from './assets/apple.png'
import ballItemPng from './assets/ball.png'
import idleNpcPng from './assets/Bandoletesidle.png'
import berryItemPng from './assets/berry.png'
import carrotItemPng from './assets/carrots.png'
import drinkItemPng from './assets/drink.png'
import snackPackItemPng from './assets/SnackPack.png'

import {
  ApiError,
  buyItem,
  clearToken,
  fetchArchitectLessons,
  fetchMe,
  feedItem,
  loadToken,
  loginUser,
  registerUser,
  saveArchitectLesson,
  saveToken,
} from './api'
import GameStage from './components/GameStage'
import { ARCHITECT_ACTIONS, ENPC_NAMES, getProgress, ITEM_META, ITEM_ORDER } from './gameData'
import type {
  ArchitectLessonsResponse,
  AuthResponse,
  EnpcLesson,
  EnpcTrigger,
  ItemId,
  UserProfile,
} from './types'


type RoutePath = '/' | '/game' | '/store' | '/architect-your-enpcs'
type AuthMode = 'login' | 'register'
type Toast = { id: number; message: string; tone: 'ok' | 'warn' }

const ITEM_IMAGE_MAP: Partial<Record<ItemId, string>> = {
  apple: appleItemPng,
  ball: ballItemPng,
  berry: berryItemPng,
  carrot: carrotItemPng,
  drink: drinkItemPng,
  snack_pack: snackPackItemPng,
}

const ITEM_TRIGGER_MAP: Partial<Record<ItemId, EnpcTrigger>> = {
  apple: 'eat_apple',
  berry: 'eat_berry',
  carrot: 'eat_carrot',
  snack_pack: 'eat_snack_pack',
  drink: 'drink_drink',
}

function normalizePath(pathname: string): RoutePath {
  if (pathname === '/store') return '/store'
  if (pathname === '/architect-your-enpcs') return '/architect-your-enpcs'
  if (pathname === '/game') return '/game'
  return '/'
}

function navigate(path: RoutePath, replace = false) {
  const method = replace ? 'replaceState' : 'pushState'
  window.history[method](null, '', path)
}

function updateInventory(user: UserProfile, itemId: ItemId, quantity: number) {
  return {
    ...user,
    inventory: {
      ...user.inventory,
      [itemId]: quantity,
    },
  }
}

function buildLessonsMap(lessons: EnpcLesson[]) {
  return lessons.reduce<Record<number, Partial<Record<EnpcTrigger, string>>>>((acc, lesson) => {
    acc[lesson.npc_index] = {
      ...(acc[lesson.npc_index] ?? {}),
      [lesson.trigger]: lesson.phrase,
    }
    return acc
  }, {})
}

function upsertLesson(lessons: EnpcLesson[], nextLesson: EnpcLesson) {
  const next = lessons.filter(
    (lesson) => !(lesson.npc_index === nextLesson.npc_index && lesson.trigger === nextLesson.trigger),
  )
  next.push(nextLesson)
  next.sort((a, b) => a.npc_index - b.npc_index || a.trigger.localeCompare(b.trigger))
  return next
}

export default function App() {
  const [route, setRoute] = useState<RoutePath>(() => normalizePath(window.location.pathname))
  const [token, setToken] = useState<string | null>(() => loadToken())
  const [viewer, setViewer] = useState<UserProfile | null>(null)
  const [isBooting, setIsBooting] = useState(() => loadToken() !== null)
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [authPending, setAuthPending] = useState(false)
  const [busyItemId, setBusyItemId] = useState<ItemId | null>(null)
  const [draggedItemId, setDraggedItemId] = useState<ItemId | null>(null)
  const [ballSpawn, setBallSpawn] = useState<{ x: number; y: number; nonce: number } | null>(null)
  const [manualTriggerEvent, setManualTriggerEvent] = useState<{
    npcId: number
    trigger: EnpcTrigger
    nonce: number
  } | null>(null)
  const [toast, setToast] = useState<Toast | null>(null)
  const [architectData, setArchitectData] = useState<ArchitectLessonsResponse | null>(null)
  const [architectLoading, setArchitectLoading] = useState(false)
  const [architectSaving, setArchitectSaving] = useState(false)
  const [selectedNpcIndex, setSelectedNpcIndex] = useState(0)
  const [selectedTrigger, setSelectedTrigger] = useState<EnpcTrigger>('eat_apple')
  const [architectPhrase, setArchitectPhrase] = useState('')
  const [revealedFlag, setRevealedFlag] = useState<string | null>(null)

  const progress = useMemo(() => getProgress(viewer?.score ?? 0), [viewer?.score])
  const isArchitect = viewer?.rank === 'ENPC Architect'
  const lessonsMap = useMemo(
    () => buildLessonsMap(architectData?.lessons ?? []),
    [architectData?.lessons],
  )
  const architectNames = architectData?.names ?? ENPC_NAMES
  const architectActions = architectData?.actions ?? ARCHITECT_ACTIONS
  const currentNpcName = architectNames[selectedNpcIndex] ?? ENPC_NAMES[selectedNpcIndex]

  useEffect(() => {
    const onPopState = () => setRoute(normalizePath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    if (!toast) return
    const timeoutId = window.setTimeout(() => setToast(null), 2600)
    return () => window.clearTimeout(timeoutId)
  }, [toast])

  useEffect(() => {
    if (!token) {
      setViewer(null)
      setArchitectData(null)
      setIsBooting(false)

      if (route !== '/') {
        navigate('/', true)
        setRoute('/')
      }

      return
    }

    let cancelled = false
    setIsBooting(true)

    fetchMe(token)
      .then((user) => {
        if (cancelled) return

        setViewer(user)

        if (route === '/') {
          navigate('/game', true)
          setRoute('/game')
        }
      })
      .catch(() => {
        if (cancelled) return

        clearToken()
        setToken(null)
      })
      .finally(() => {
        if (!cancelled) setIsBooting(false)
      })

    return () => {
      cancelled = true
    }
  }, [route, token])

  useEffect(() => {
    if (!viewer) return

    if (route === '/architect-your-enpcs' && viewer.rank !== 'ENPC Architect') {
      navigate('/game', true)
      setRoute('/game')
    }
  }, [route, viewer])

  useEffect(() => {
    if (!viewer || !token || viewer.rank !== 'ENPC Architect') {
      setArchitectData(null)
      return
    }

    let cancelled = false
    setArchitectLoading(true)

    fetchArchitectLessons(token)
      .then((data) => {
        if (!cancelled) setArchitectData(data)
      })
      .catch((error) => {
        if (!cancelled) {
          pushToast(
            error instanceof ApiError ? error.message : 'Failed to load architect desk',
            'warn',
          )
        }
      })
      .finally(() => {
        if (!cancelled) setArchitectLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [token, viewer?.rank])

  useEffect(() => {
    const nextPhrase = architectData?.lessons.find(
      (lesson) =>
        lesson.npc_index === selectedNpcIndex &&
        lesson.trigger === selectedTrigger,
    )?.phrase

    setArchitectPhrase(nextPhrase ?? '')
  }, [architectData, selectedNpcIndex, selectedTrigger])

  const pushToast = (message: string, tone: Toast['tone']) => {
    setToast({ id: Date.now(), message, tone })
  }

  const handleRoute = (path: RoutePath) => {
    navigate(path)
    setRoute(path)
  }

  const handleAuthSuccess = (response: AuthResponse) => {
    saveToken(response.token)
    setToken(response.token)
    setViewer(response.user)
    setUsername('')
    setPassword('')
    handleRoute('/game')
  }

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAuthPending(true)

    try {
      const response =
        authMode === 'login'
          ? await loginUser(username.trim(), password)
          : await registerUser(username.trim(), password)

      handleAuthSuccess(response)

      pushToast(
        authMode === 'login'
          ? 'Logged in.'
          : 'Registered with 65 starter bits.',
        'ok',
      )
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : 'Request failed'

      pushToast(message, 'warn')
    } finally {
      setAuthPending(false)
    }
  }

  const handleLogout = () => {
    clearToken()
    setToken(null)
    setViewer(null)
    setArchitectData(null)
    setDraggedItemId(null)
    setRevealedFlag(null)
    pushToast('Logged out.', 'ok')
  }

  const refreshViewer = async () => {
    if (!token) return

    try {
      const fresh = await fetchMe(token)
      setViewer(fresh)
    } catch {
      handleLogout()
    }
  }

  const handleBuy = async (itemId: ItemId) => {
    if (!viewer || !token) return

    setBusyItemId(itemId)

    try {
      const response = await buyItem(itemId, token)

      setViewer((current) => {
        if (!current) return current

        return updateInventory(
          {
            ...current,
            bits: response.bits,
          },
          itemId,
          response.inventory_quantity,
        )
      })

      pushToast('Added to inventory!', 'ok')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        handleLogout()
        return
      }

      pushToast(
        error instanceof ApiError ? error.message : 'Purchase failed',
        'warn',
      )
    } finally {
      setBusyItemId(null)
    }
  }

  const handleArenaDrop = async (point: {
    x: number
    y: number
    npcId: number | null
  }) => {
    if (!viewer || !token || !draggedItemId) return

    const itemId = draggedItemId
    const trigger = ITEM_TRIGGER_MAP[itemId]

    setDraggedItemId(null)
    setBusyItemId(itemId)

    try {
      const response = await feedItem(itemId, token)

      setViewer((current) => {
        if (!current) return current

        return updateInventory(
          {
            ...current,
            score: response.new_score,
            rank: response.new_rank,
          },
          itemId,
          response.inventory_quantity,
        )
      })

      if (isArchitect && trigger && point.npcId !== null) {
        setManualTriggerEvent({
          npcId: point.npcId,
          trigger,
          nonce: Date.now(),
        })
      }

      if (itemId === 'ball') {
        setBallSpawn({
          x: point.x,
          y: point.y,
          nonce: Date.now(),
        })
        pushToast('Fed! +0 pts', 'ok')
      } else {
        pushToast(`Fed! +${response.score_gained} pts`, 'ok')
      }

      if ((response.architect_reward_balls ?? 0) > 0) {
        pushToast('ENPC Architect unlocked. +15 balls added.', 'ok')
        await refreshViewer()
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        handleLogout()
        return
      }

      pushToast(
        error instanceof ApiError ? error.message : 'Feed failed',
        'warn',
      )

      await refreshViewer()
    } finally {
      setBusyItemId(null)
    }
  }

  const handleSaveLesson = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    if (!token || !viewer || viewer.rank !== 'ENPC Architect') return

    setArchitectSaving(true)

    try {
      const response = await saveArchitectLesson(
        selectedNpcIndex,
        selectedTrigger,
        architectPhrase,
        token,
      )

      setViewer((current) =>
        current
          ? {
              ...current,
              bits: response.new_bits,
              score: response.new_score,
              rank: response.new_rank,
            }
          : current,
      )

      setArchitectData((current) => {
        const base =
          current ?? {
            names: ENPC_NAMES,
            actions: ARCHITECT_ACTIONS,
            lessons: [],
          }

        return {
          ...base,
          lessons: upsertLesson(base.lessons, {
            npc_index: response.npc_index,
            trigger: response.trigger,
            phrase: response.phrase,
          }),
        }
      })

      pushToast(
        response.score_gained > 0 || response.bits_gained > 0
          ? `Lesson saved. +${response.score_gained} pts, +${response.bits_gained} bits`
          : 'Lesson updated.',
        'ok',
      )
    } catch (error) {
      pushToast(
        error instanceof ApiError
          ? error.message
          : 'Could not save lesson',
        'warn',
      )
    } finally {
      setArchitectSaving(false)
    }
  }

  if (isBooting) {
    return (
      <main className="appRoot screenShell">
        <div className="loadingCard">Booting ENPC systems...</div>
      </main>
    )
  }

  if (!viewer) {
    return (
      <main className="appRoot authRoot">
        <section className="authHero panel">
          <p className="eyebrow">ENPC GAME</p>
          <h1>Feed the arena. Rank the handler. Chase the real chain.</h1>
          <p className="authCopy">
            Every new account starts with 65 bits. Buy supplies, drag them into the field, and push your score to
            climb from ENPC Supporter to ENPC Architect.
          </p>
          <div className="authStats">
            <div>
              <strong>0-99</strong>
              <span>ENPC Supporter</span>
            </div>
            <div>
              <strong>100-199</strong>
              <span>ENPC Booster</span>
            </div>
            <div>
              <strong>200+</strong>
              <span>ENPC Architect</span>
            </div>
          </div>
        </section>

        <section className="authPanel panel">
          <div className="authTabs">
            <button className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}>
              Login
            </button>
            <button className={authMode === 'register' ? 'active' : ''} onClick={() => setAuthMode('register')}>
              Register
            </button>
          </div>

          <form className="authForm" onSubmit={handleAuthSubmit}>
            <label>
              Username
              <input value={username} maxLength={32} onChange={(event) => setUsername(event.target.value)} required />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                minLength={6}
                maxLength={72}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <button className="primaryButton" type="submit" disabled={authPending}>
              {authPending ? 'Working...' : authMode === 'login' ? 'Enter Arena' : 'Claim Starter Bits'}
            </button>
          </form>
        </section>

        {toast ? <ToastBanner toast={toast} /> : null}
      </main>
    )
  }

  return (
    <main className="appRoot screenShell">
      <header className="topBar panel">
        <button className="titleButton" onClick={() => handleRoute('/game')}>
          ENPC GAME
        </button>
        <div className="identityBlock">
          <span className="usernameText">{viewer.username}</span>
          {viewer.rank === 'ENPC Architect' ? (
            <button className="rankBadge architectBadgeButton architectGlow" onClick={() => handleRoute('/architect-your-enpcs')}>
              {viewer.rank}
            </button>
          ) : (
            <span className="rankBadge">{viewer.rank}</span>
          )}
        </div>
        <div className="bitsBadge">{viewer.bits} bits</div>
        <button className="ghostButton" onClick={handleLogout}>
          Logout
        </button>
      </header>

      {route === '/store' ? (
        <section className="storeShell">
          <div className="storeHeaderRow">
            <div>
              <p className="eyebrow">Storefront</p>
              <h2>ENPC Store</h2>
            </div>
            <button className="primaryButton" onClick={() => handleRoute('/game')}>
              Back to Game
            </button>
          </div>

          <div className="storeGrid">
            {ITEM_ORDER.map((itemId) => {
              const item = ITEM_META[itemId]
              return (
                <article key={itemId} className="storeCard panel">
                  <ItemVisual itemId={itemId} />
                  <div>
                    <h3>{item.name}</h3>
                    <p className="cardFlavor">{item.description}</p>
                  </div>
                  <div className="storeMeta">
                    <span>{item.cost} bits</span>
                    <button
                      className="primaryButton"
                      onClick={() => void handleBuy(itemId)}
                      disabled={busyItemId === itemId}
                    >
                      {busyItemId === itemId ? 'Buying...' : 'Buy'}
                    </button>
                  </div>
                </article>
              )
            })}
          </div>

          <p className="storeLore panel">Field notes: stock up before entering the arena.</p>
        </section>
      ) : route === '/architect-your-enpcs' ? (
        <section className="architectShell">
          <div className="storeHeaderRow">
            <div>
              <p className="eyebrow">Architect Desk</p>
              <h2>Architect Your ENPCs</h2>
            </div>
            <button className="primaryButton" onClick={() => handleRoute('/game')}>
              Back to Game
            </button>
          </div>

          <div className="architectLayout">
            <button
              className="architectArrow"
              type="button"
              onClick={() => setSelectedNpcIndex((current) => (current === 0 ? architectNames.length - 1 : current - 1))}
            >
              ◀
            </button>

            <section className="architectCard panel">
              <p className="eyebrow">Selected ENPC</p>
              <div className="architectNpcName">{currentNpcName}</div>
              <div className="architectAvatar">
                <img src={idleNpcPng} alt="" />
              </div>
              <span className="architectCaption">Teach this ENPC what to say when a trigger fires.</span>
            </section>

            <button
              className="architectArrow"
              type="button"
              onClick={() => setSelectedNpcIndex((current) => (current + 1) % architectNames.length)}
            >
              ▶
            </button>
          </div>

          <form className="architectTeachRow panel" onSubmit={handleSaveLesson}>
            <label className="architectInlineLabel">
              SAY
              <input
                value={architectPhrase}
                maxLength={100}
                onChange={(event) => setArchitectPhrase(event.target.value)}
                placeholder="Words or phrases to learn"
                required
              />
            </label>
            <label className="architectInlineLabel">
              WHEN
              <select value={selectedTrigger} onChange={(event) => setSelectedTrigger(event.target.value as EnpcTrigger)}>
                {architectActions.map((action) => (
                  <option key={action.key} value={action.key}>
                    {action.label}
                  </option>
                ))}
              </select>
            </label>
            <button className="primaryButton" type="submit" disabled={architectSaving || architectLoading}>
              {architectSaving ? 'Saving...' : 'Teach'}
            </button>
          </form>

          <div className="architectHintRow panel">
            <span>{architectLoading ? 'Syncing learned phrases...' : `Editing lesson for ${currentNpcName}`}</span>
            <span>{architectPhrase.length}/100 chars</span>
          </div>
        </section>
      ) : (
        <section className="gameShell">
          <div className="arenaColumn panel">
            <div className="sectionHead">
              <div>
                <p className="eyebrow">Arena</p>
                <h2>ENPC Field</h2>
              </div>
              <button className="primaryButton" onClick={() => handleRoute('/store')}>
                Visit Store
              </button>
            </div>
            <GameStage
              architectMode={isArchitect}
              draggedItemId={draggedItemId}
              ballSpawn={ballSpawn}
              lessonsMap={lessonsMap}
              manualTriggerEvent={manualTriggerEvent}
              npcNames={architectNames}
              onDropItem={(point) => void handleArenaDrop(point)}
              onFlagReveal={(flag) => setRevealedFlag(flag)}
            />
            {revealedFlag ? (
              <div className="flagReveal panel">
                <p className="eyebrow">Flag Captured</p>
                <code>{revealedFlag}</code>
              </div>
            ) : null}
          </div>

          <aside className="sidebarColumn">
            <section className="panel">
              <div className="sectionHead compact">
                <div>
                  <p className="eyebrow">Inventory</p>
                  <h2>Feed Kit</h2>
                </div>
              </div>
              <div className="feedKitGrid">
                {ITEM_ORDER.map((itemId) => {
                  const quantity = viewer.inventory[itemId] ?? 0
                  const canDrag = quantity > 0
                  return (
                    <article key={itemId} className={`feedKitSlot ${canDrag ? 'hasStock' : ''}`}>
                      <span className="feedKitCount">{quantity}</span>
                      <div
                        className={`feedKitDrag ${canDrag ? 'draggable' : 'empty'}`}
                        draggable={canDrag}
                        onDragStart={() => setDraggedItemId(itemId)}
                        onDragEnd={() => setDraggedItemId(null)}
                        aria-label={`${ITEM_META[itemId].name}: ${quantity} in inventory`}
                        title={ITEM_META[itemId].name}
                      >
                        <ItemVisual itemId={itemId} />
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>

            <section className="panel scorePanel">
              <div className="sectionHead compact">
                <div>
                  <p className="eyebrow">Progress</p>
                  <h2>Rank Track</h2>
                </div>
              </div>
              <div className="scoreValue">{viewer.score}</div>
              <div className="rankBadge wide">{viewer.rank}</div>
              <div className="rankPopoverWrap">
                <button className="rankPopoverButton" type="button">
                  Available Ranks
                </button>
                <div className="rankPopoverCard">
                  <div className={`rankTier ${viewer.score < 100 ? 'active' : ''}`}>
                    <strong>ENPC Supporter</strong>
                    <span>0-99 score</span>
                  </div>
                  <div className={`rankTier ${viewer.score >= 100 && viewer.score < 200 ? 'active' : ''}`}>
                    <strong>ENPC Booster</strong>
                    <span>100-199 score</span>
                  </div>
                  <div className={`rankTier ${viewer.score >= 200 ? 'active' : ''}`}>
                    <strong>ENPC Architect</strong>
                    <span>200+ score</span>
                  </div>
                </div>
              </div>
              <div className="progressBar" aria-label="Rank progress">
                <div className="progressFill" style={{ width: `${progress.pct}%` }} />
              </div>
              <p className="progressCopy">{progress.label}</p>
            </section>
          </aside>
        </section>
      )}

      {toast ? <ToastBanner toast={toast} /> : null}
    </main>
  )
}

function ToastBanner({ toast }: { toast: Toast }) {
  return <div className={`toast ${toast.tone}`}>{toast.message}</div>
}

function ItemVisual({ itemId }: { itemId: ItemId }) {
  const item = ITEM_META[itemId]
  const style = {
    '--glyph-accent': item.accent,
  } as CSSProperties
  const imageSrc = ITEM_IMAGE_MAP[itemId]

  return (
    <div className={`itemGlyph ${imageSrc ? 'hasImage' : ''} item-${itemId}`} style={style}>
      {imageSrc ? <img src={imageSrc} alt="" /> : item.shortLabel}
    </div>
  )
}