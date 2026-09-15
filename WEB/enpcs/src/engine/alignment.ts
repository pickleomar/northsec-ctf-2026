import type { Thronglet } from '../types'

// Target line is y = x
export function computeLoss(thronglets: ReadonlyArray<Pick<Thronglet, 'x' | 'y'>>): number {
  const n = thronglets.length
  if (n === 0) return 1
  let sum = 0
  for (let i = 0; i < n; i++) {
    const d = thronglets[i].y - thronglets[i].x
    sum += d * d
  }
  return sum / n
}
