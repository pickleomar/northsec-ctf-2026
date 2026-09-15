import type { EnpcTrigger, ItemId } from './types'

export const ITEM_ORDER: ItemId[] = ['apple', 'carrot', 'berry', 'snack_pack', 'drink', 'ball']
export const ENPC_NAMES = ['LMRAKCHI', 'FASSI', 'CASAWI', 'MEKNESSI', 'TANJAWE', '7ERBI', 'AGADIRI', 'TETOUANI', 'FLIFLA', 'SLAWI']

export const ARCHITECT_ACTIONS: Array<{ key: EnpcTrigger; label: string }> = [
  { key: 'eat_apple', label: 'EATS AN APPLE' },
  { key: 'eat_berry', label: 'EATS A BERRY' },
  { key: 'eat_carrot', label: 'EATS A CARROT' },
  { key: 'eat_snack_pack', label: 'EATS A SNACK PACK' },
  { key: 'drink_drink', label: 'DRINKS A DRINK' },
  { key: 'kick_ball', label: 'KICKS THE BALL' },
  { key: 'touch_enpc', label: 'TOUCH ANOTHER ENPC' },
]

export const ITEM_META: Record<
  ItemId,
  {
    name: string
    shortLabel: string
    cost: number
    score: number
    description: string
    flavor: string
    accent: string
  }
> = {
  apple: {
    name: 'Apples',
    shortLabel: 'AP',
    cost: 3,
    score: 6,
    description: 'tfa7 dial a7med khamj, katssayb lik mok drinks bih',
    flavor: 'Fresh and dependable. A classic orchard refill.',
    accent: '#8dfc6e',
  },
  carrot: {
    name: 'Carrot',
    shortLabel: 'CR',
    cost: 2,
    score: 4,
    description: 'tJa3dA',
    flavor: 'Crunchy focus sticks for orderly field behavior.',
    accent: '#ff9a3c',
  },
  berry: {
    name: 'Berries',
    shortLabel: 'BY',
    cost: 4,
    score: 8,
    description: 'toutt lbarri',
    flavor: 'A bright pocket of sugar and tiny chaos.',
    accent: '#ff5d9e',
  },
  snack_pack: {
    name: 'Snack Pack',
    shortLabel: 'SP',
    cost: 10,
    score: 20,
    description: 'Matina wchwya dia lfakia',
    flavor: 'Two handfuls of calories and one handful of trouble.',
    accent: '#ffe066',
  },
  drink: {
    name: 'Drink',
    shortLabel: 'DR',
    cost: 6,
    score: 13,
    description: 'the water of life, mssayb btfa7 dial a7med',
    flavor: 'A neon can of movement and questionable focus.',
    accent: '#4cf5e6',
  },
  ball: {
    name: 'Ball',
    shortLabel: 'BL',
    cost: 5,
    score: 0,
    description: 'Koora dmika dial 5dh la drbatk lwjhek kat7ess bl7gra',
    flavor: 'A prized toy that turns the arena into recess.',
    accent: '#ffcf5a',
  },
}

export function getRank(score: number) {
  if (score >= 200) return 'ENPC Architect'
  if (score >= 100) return 'ENPC Booster'
  return 'ENPC Supporter'
}

export function getProgress(score: number) {
  if (score >= 200) {
    return {
      current: 200,
      max: 200,
      pct: 100,
      label: 'Architect tier secured',
      nextTarget: 'Max rank reached',
    }
  }

  if (score >= 100) {
    return {
      current: score - 100,
      max: 100,
      pct: ((score - 100) / 100) * 100,
      label: `${score}/200 total score`,
      nextTarget: 'Next rank: ENPC Architect at 200',
    }
  }

  return {
    current: score,
    max: 100,
    pct: score,
    label: `${score}/100 toward ENPC Booster`,
    nextTarget: 'Next rank: ENPC Booster at 100',
  }
}
