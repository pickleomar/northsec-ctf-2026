export type Pose = 'idle' | 'walking' | 'beep'

export type ItemId = 'apple' | 'carrot' | 'berry' | 'snack_pack' | 'drink' | 'ball'
export type EnpcTrigger =
  | 'eat_apple'
  | 'eat_berry'
  | 'eat_carrot'
  | 'eat_snack_pack'
  | 'drink_drink'
  | 'kick_ball'
  | 'touch_enpc'

export type InventoryMap = Record<ItemId, number>

export type Thronglet = {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  desiredAngle: number
  nextWanderIn: number
  beepUntil: number
  nextTouchSpeechAt: number
  nextBallSpeechAt: number
  pose: Pose
}

export type Tree = {
  id: number
  x: number
  y: number
  r: number
}

export type BallEntity = {
  id: number
  active: boolean
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

export type HiddenModelConfig = {
  m: number
  b: number
  noise: number
  lr: number
}

export type PublicPresetConfig = {
  visuals: {
    hoverScale: number
    hoverLift: number
  }
  ambience: {
    treeDensity: number
    canopyScale: number
  }
  wander: {
    turnJitter: number
    cadenceMin: number
    cadenceMax: number
    speedBias: number
  }
}

export type RuntimeConfig = {
  hiddenModel: HiddenModelConfig
  publicPreset: PublicPresetConfig
  motion: {
    steer: number
    drag: number
    desiredSpeedMin: number
    desiredSpeedMax: number
    speedWalkThreshold: number
  }
  world: {
    throngletCount: number
    treeCount: number
    npcRadius: number
    treeRadius: number
    treeMinDist: number
    bounds: {
      padX: number
      padYTop: number
      padYBottom: number
    }
  }
  validate: {
    epsilon: number
    cooldownMs: number
  }
}

export type ValidationPayload = {
  seed: number
  model: HiddenModelConfig
  positions: Array<[number, number]>
  stage: { w: number; h: number }
  challengeToken: string
}

export type ValidationChallenge = {
  token: string
  expiresAt: number
}

export type ValidationResponse = {
  success: boolean
  score: number
  flag?: string
  message?: string
}

export type UserProfile = {
  id: number
  username: string
  bits: number
  score: number
  rank: string
  inventory: InventoryMap
}

export type ArchitectAction = {
  key: EnpcTrigger
  label: string
}

export type EnpcLesson = {
  npc_index: number
  trigger: EnpcTrigger
  phrase: string
}

export type ArchitectLessonsResponse = {
  names: string[]
  actions: ArchitectAction[]
  lessons: EnpcLesson[]
}

export type SaveLessonResponse = {
  message: string
  npc_index: number
  trigger: EnpcTrigger
  phrase: string
  bits_gained: number
  new_bits: number
  score_gained: number
  new_score: number
  new_rank: string
}

export type SwarmEvent = {
  npcId: number
  trigger: EnpcTrigger
}

export type AuthResponse = {
  token: string
  user: UserProfile
}

export type PurchaseResponse = {
  message: string
  item_id: ItemId
  bits: number
  inventory_quantity: number
}

export type FeedResponse = {
  message: string
  item_id: ItemId
  score_gained: number
  new_score: number
  new_rank: string
  inventory_quantity: number
  architect_reward_balls?: number
}
