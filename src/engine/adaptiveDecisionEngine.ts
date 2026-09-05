import type {
  ActivityKind,
  Difficulty,
  Format,
  LearningActivity,
  LearningProfile,
  ActivityRecord,
  Outcome,
  Feeling,
  Recommendation,
} from '../types'

const difficultyValue: Record<Difficulty, number> = {
  Easy: 1,
  Intermediate: 2,
  Challenging: 3,
}

const nextDifficulty = (d: Difficulty): Difficulty =>
  d === 'Easy' ? 'Intermediate' : d === 'Intermediate' ? 'Challenging' : 'Challenging'

const prevDifficulty = (d: Difficulty): Difficulty =>
  d === 'Challenging' ? 'Intermediate' : d === 'Intermediate' ? 'Easy' : 'Easy'

export interface LearningState {
  needsRevision: boolean
  shortSuccess: number
  longStruggle: boolean
  consecutiveStruggles: number
  consecutiveSuccesses: number
  isConsistent: boolean
  hasLimitedTime: boolean
  topicStruggleCount: Record<string, number>
  topicSuccessCount: Record<string, number>
  totalExplainRequests: number
  supportModeActive: boolean
}

export function analyzeLearningState(
  profile: LearningProfile,
  history: ActivityRecord[]
): LearningState {
  const recent = history.slice(-6)
  const shortSuccess = recent.filter(
    (x) => x.duration <= 15 && x.outcome === 'completed' && x.feeling !== 'difficult'
  ).length

  const recentLongStruggle = recent.some(
    (x) => x.duration > 15 && x.outcome !== 'completed'
  )
  const longStruggle = profile.longActivityAbandoned || recentLongStruggle

  let consecutiveStruggles = 0
  for (let i = history.length - 1; i >= 0; i--) {
    const h = history[i]
    const struggled = h.outcome !== 'completed' || h.feeling === 'difficult'
    if (struggled) consecutiveStruggles++
    else break
  }

  let consecutiveSuccesses = 0
  for (let i = history.length - 1; i >= 0; i--) {
    const h = history[i]
    const succeeded = h.outcome === 'completed' && h.feeling !== 'difficult'
    if (succeeded) consecutiveSuccesses++
    else break
  }

  const completedCount = recent.filter((x) => x.outcome === 'completed').length
  const isConsistent =
    profile.recentCompletionRate >= 80 && completedCount >= 2 && consecutiveSuccesses >= 2

  const hasLimitedTime = profile.availableMinutes <= 15

  const topicStruggleCount: Record<string, number> = {}
  const topicSuccessCount: Record<string, number> = {}
  for (const h of recent) {
    const struggled = h.outcome !== 'completed' || h.feeling === 'difficult'
    if (struggled) topicStruggleCount[h.topic] = (topicStruggleCount[h.topic] || 0) + 1
    else topicSuccessCount[h.topic] = (topicSuccessCount[h.topic] || 0) + 1
  }

  const totalExplainRequests = profile.explanationRequests
  const supportModeActive = totalExplainRequests > 0

  const needsRevision =
    profile.repeatedMistakes.length > 0 || Object.values(topicStruggleCount).some((n) => n >= 2)

  return {
    needsRevision,
    shortSuccess,
    longStruggle,
    consecutiveStruggles,
    consecutiveSuccesses,
    isConsistent,
    hasLimitedTime,
    topicStruggleCount,
    topicSuccessCount,
    totalExplainRequests,
    supportModeActive,
  }
}

export function calculateTaskPriority(
  activity: LearningActivity,
  profile: LearningProfile,
  history: ActivityRecord[],
  state: LearningState
): number {
  let score = activity.priority

  if (profile.revisionTopics.includes(activity.topic)) score += 20
  if (profile.repeatedMistakes.includes(activity.topic)) score += 28

  const topicStruggles = state.topicStruggleCount[activity.topic] || 0
  if (topicStruggles >= 1) score += topicStruggles * 10

  const clampedDuration = Math.min(activity.duration, 25, profile.typicalSuccessfulMinutes + 10)
  if (clampedDuration > profile.availableMinutes) score -= 20
  if (profile.availableMinutes < 5) score -= 40

  if (state.longStruggle && activity.duration > 15) score -= 15

  if (state.consecutiveStruggles >= 2 && activity.duration > 10) score -= 12

  if (activity.format === profile.preferredFormat) score += 8

  if (state.supportModeActive && activity.format === 'Visual') score += 6

  if (state.needsRevision && activity.kind === 'Revision') score += 18
  if (!state.needsRevision && activity.kind === 'Revision') score -= 8

  const targetDiff = recommendDifficulty(profile, history, state)
  if (activity.difficulty === targetDiff) score += 10
  else if (
    Math.abs(difficultyValue[activity.difficulty] - difficultyValue[targetDiff]) === 1
  )
    score += 3
  else score -= 15

  return score
}

export function recommendTaskSize(
  profile: LearningProfile,
  history: ActivityRecord[],
  state: LearningState
): number {
  const base = profile.typicalSuccessfulMinutes

  if (state.consecutiveStruggles >= 3) return Math.max(5, base - 10)
  if (state.consecutiveStruggles >= 2) return Math.max(5, base - 5)
  if (state.longStruggle && state.consecutiveStruggles >= 1) return 10

  if (state.consecutiveSuccesses >= 4) return Math.min(30, base + 10)
  if (state.consecutiveSuccesses >= 2) return Math.min(25, base + 5)

  if (state.isConsistent) return Math.min(20, base + 5)
  if (state.hasLimitedTime) return Math.min(10, base)

  return base
}

export function recommendSessionDuration(
  profile: LearningProfile,
  history: ActivityRecord[],
  state: LearningState
): number {
  const size = recommendTaskSize(profile, history, state)
  const clampedToAvailability = Math.min(size, profile.availableMinutes)
  return Math.max(5, clampedToAvailability)
}

export function recommendLearningFormat(
  profile: LearningProfile,
  state: LearningState
): Format {
  if (state.totalExplainRequests >= 3) return 'Visual'
  if (state.supportModeActive && profile.preferredFormat !== 'Visual') return 'Visual'
  return profile.preferredFormat
}

export function recommendDifficulty(
  profile: LearningProfile,
  history: ActivityRecord[],
  state?: LearningState
): Difficulty {
  const s = state || analyzeLearningState(profile, history)

  if (s.needsRevision) return 'Easy'

  if (s.consecutiveStruggles >= 3) return prevDifficulty(prevDifficulty(profile.currentDifficulty))
  if (s.consecutiveStruggles >= 2) return prevDifficulty(profile.currentDifficulty)

  if (s.isConsistent && s.consecutiveSuccesses >= 3)
    return nextDifficulty(nextDifficulty(profile.currentDifficulty))
  if (s.isConsistent) return nextDifficulty(profile.currentDifficulty)

  return profile.currentDifficulty
}

export function determineBreak(
  duration: number,
  profile: LearningProfile,
  state: LearningState
): number {
  if (state.consecutiveStruggles >= 2) return 5
  if (duration >= 20 || profile.longActivityAbandoned) return 4
  if (duration >= 15) return 3
  return 2
}

export function determineSupportNeeded(
  profile: LearningProfile,
  activity: LearningActivity,
  state: LearningState
): boolean {
  return (
    state.supportModeActive ||
    profile.repeatedMistakes.includes(activity.topic) ||
    (state.topicStruggleCount[activity.topic] || 0) >= 1
  )
}

export function selectNextActivity(
  activities: LearningActivity[],
  profile: LearningProfile,
  history: ActivityRecord[],
  state: LearningState
): LearningActivity {
  const sorted = [...activities].sort(
    (a, b) => calculateTaskPriority(b, profile, history, state) - calculateTaskPriority(a, profile, history, state)
  )
  return sorted[0]
}

export function generateRecommendationReason(
  profile: LearningProfile,
  activity: LearningActivity,
  candidateDifficulty: Difficulty,
  duration: number,
  difficulty: Difficulty,
  support: boolean,
  state: LearningState
): { summary: string; bullets: string[]; adaptedFlags: string[] } {
  const bullets: string[] = []
  const adaptedFlags: string[] = []

  const overrideUp = difficultyValue[difficulty] > difficultyValue[candidateDifficulty]
  const overrideDown = difficultyValue[difficulty] < difficultyValue[candidateDifficulty]
  const difficultyChangedUp =
    difficultyValue[difficulty] > difficultyValue[profile.currentDifficulty] || overrideUp
  const difficultyChangedDown =
    difficultyValue[difficulty] < difficultyValue[profile.currentDifficulty] || overrideDown

  if (profile.repeatedMistakes.includes(activity.topic)) {
    bullets.push(`You have recently found ${activity.topic.toLowerCase()} challenging — this focuses on a topic flagged for review`)
    adaptedFlags.push('REVISION FOCUS')
  }

  const struggles = state.topicStruggleCount[activity.topic] || 0
  if (struggles >= 2) {
    bullets.push(`${activity.topic} has been difficult in the last ${struggles} sessions — building back confidence with a guided step`)
  } else if (struggles === 1 && !profile.repeatedMistakes.includes(activity.topic)) {
    bullets.push(`${activity.topic} was tricky last session — consolidating before moving on`)
  }

  if (profile.longActivityAbandoned || state.longStruggle) {
    bullets.push('Shorter activities have been more manageable than longer ones — keeping this focused')
    adaptedFlags.push('SHORT & FOCUSED')
  }

  if (state.consecutiveStruggles >= 2) {
    bullets.push(`After ${state.consecutiveStruggles} tricky sessions in a row, this step is intentionally smaller`)
    adaptedFlags.push('REDUCED TASK SIZE')
  }

  if (state.consecutiveSuccesses >= 2 && !state.needsRevision) {
    bullets.push(`${state.consecutiveSuccesses} successful sessions in a row — gently stretching you`)
    adaptedFlags.push('GENTLE STRETCH')
  }

  if (overrideUp) {
    bullets.push(`This activity has been stepped up to ${difficulty.toLowerCase()} based on your consistent progress`)
    adaptedFlags.push(`BOOSTED → ${difficulty.toUpperCase()}`)
  } else if (overrideDown) {
    bullets.push(`Scaffolded down to ${difficulty.toLowerCase()} so you can rebuild confidence before advancing`)
    adaptedFlags.push(`SCAFFOLDED → ${difficulty.toUpperCase()}`)
  } else if (difficultyChangedUp) {
    bullets.push(`Consistent completion lets us try a harder ${difficulty.toLowerCase()} level`)
    adaptedFlags.push(`DIFFICULTY: ↑ ${difficulty.toUpperCase()}`)
  } else if (difficultyChangedDown) {
    bullets.push(`Taking difficulty back down to ${difficulty.toLowerCase()} to rebuild confidence`)
    adaptedFlags.push(`DIFFICULTY: ↓ ${difficulty.toUpperCase()}`)
  } else {
    bullets.push(`Staying at ${difficulty.toLowerCase()} — a good fit right now`)
  }

  if (activity.format === profile.preferredFormat) {
    bullets.push(`Uses your preferred ${activity.format.toLowerCase()} format`)
  } else if (activity.format === 'Visual' && state.totalExplainRequests >= 2) {
    bullets.push(`Visual format selected because you've asked for extra explanation recently`)
    adaptedFlags.push('VISUAL SUPPORT')
  }

  bullets.push(`It fits your ${profile.availableMinutes} minutes available (this activity: ${duration} min)`)

  if (support) {
    bullets.push('An optional simple explanation via Study Buddy is ready if you need it')
    adaptedFlags.push('STUDY BUDDY READY')
  }

  if (duration <= 10) adaptedFlags.push(`QUICK ${duration}MIN STEP`)
  if (duration >= 20) adaptedFlags.push(`${duration}MIN DEEP DIVE`)

  const summaryParts = bullets.slice(0, 2)
  const summary = `Recommended because ${summaryParts.join('; and ')}.`

  return { summary, bullets, adaptedFlags }
}

export function generateRecommendation(
  activities: LearningActivity[],
  profile: LearningProfile,
  history: ActivityRecord[]
): Recommendation & { reasons: string[]; flags: string[]; bullets: string[] } {
  const state = analyzeLearningState(profile, history)

  const desiredDifficulty = recommendDifficulty(profile, history, state)
  const preferredFormat = recommendLearningFormat(profile, state)
  const duration = recommendSessionDuration(profile, history, state)

  const candidate = selectNextActivity(activities, profile, history, state)

  const inRevision =
    profile.repeatedMistakes.includes(candidate.topic) ||
    (state.topicStruggleCount[candidate.topic] || 0) >= 2

  const finalDifficulty = inRevision ? 'Easy' : desiredDifficulty
  const finalKind: ActivityKind = inRevision ? 'Revision' : candidate.kind

  const activity: LearningActivity = {
    ...candidate,
    duration: Math.max(0, Math.min(candidate.duration, duration, profile.availableMinutes)),
    difficulty: finalDifficulty,
    format: preferredFormat,
    kind: finalKind,
  }

  const support = determineSupportNeeded(profile, activity, state)
  const breakMinutes = determineBreak(activity.duration, profile, state)
  const score = calculateTaskPriority(activity, profile, history, state)
  const reasoning = generateRecommendationReason(
    profile,
    activity,
    candidate.difficulty,
    activity.duration,
    finalDifficulty,
    support,
    state
  )

  return {
    activity,
    duration: activity.duration,
    difficulty: activity.difficulty,
    format: activity.format,
    kind: activity.kind,
    breakMinutes,
    supportNeeded: support,
    score,
    reasons: [reasoning.summary],
    bullets: reasoning.bullets,
    flags: reasoning.adaptedFlags,
  } as Recommendation & { reasons: string[]; flags: string[]; bullets: string[] }
}

export function updateLearningProfile(
  profile: LearningProfile,
  activity: LearningActivity,
  outcome: Outcome,
  feeling: Feeling,
  history: ActivityRecord[]
): LearningProfile {
  const success = outcome === 'completed' && feeling !== 'difficult'
  const struggle = outcome === 'skipped' || outcome === 'partial' || feeling === 'difficult'

  const completionWeight = 0.75
  const newOutcomeScore =
    outcome === 'completed' ? 100 : outcome === 'partial' ? 50 : 0
  const completion = Math.round(
    profile.recentCompletionRate * completionWeight +
      newOutcomeScore * (1 - completionWeight)
  )

  const topicStruggles = history.filter(
    (h) => h.topic === activity.topic && (h.outcome !== 'completed' || h.feeling === 'difficult')
  ).length

  const topicSuccesses = history.filter(
    (h) => h.topic === activity.topic && h.outcome === 'completed' && h.feeling !== 'difficult'
  ).length

  let repeatedMistakes = profile.repeatedMistakes
  if (struggle && topicStruggles >= 2) {
    repeatedMistakes = Array.from(new Set([...repeatedMistakes, activity.topic]))
  } else if (success && repeatedMistakes.includes(activity.topic)) {
    repeatedMistakes = repeatedMistakes.filter((t) => t !== activity.topic)
  }

  let revisionTopics = profile.revisionTopics
  if (struggle && topicStruggles >= 2) {
    revisionTopics = Array.from(new Set([...revisionTopics, activity.topic]))
  } else if (success && topicSuccesses >= 2) {
    revisionTopics = revisionTopics.filter((t) => t !== activity.topic)
  }

  let consecutiveStruggles = 0
  for (let i = history.length - 1; i >= 0; i--) {
    const h = history[i]
    if (h.outcome !== 'completed' || h.feeling === 'difficult') consecutiveStruggles++
    else break
  }

  let consecutiveSuccesses = 0
  for (let i = history.length - 1; i >= 0; i--) {
    const h = history[i]
    if (h.outcome === 'completed' && h.feeling !== 'difficult') consecutiveSuccesses++
    else break
  }

  let typicalSuccessfulMinutes = profile.typicalSuccessfulMinutes
  if (success && consecutiveSuccesses >= 2 && activity.duration >= typicalSuccessfulMinutes) {
    typicalSuccessfulMinutes = Math.min(25, typicalSuccessfulMinutes + 5)
  } else if (struggle && consecutiveStruggles >= 2 && activity.duration >= typicalSuccessfulMinutes) {
    typicalSuccessfulMinutes = Math.max(5, typicalSuccessfulMinutes - 5)
  }

  const recent = history.slice(-5)
  const recentStruggles = recent.filter(
    (h) => h.outcome !== 'completed' || h.feeling === 'difficult'
  ).length
  const recentSuccesses = recent.filter(
    (h) => h.outcome === 'completed' && h.feeling !== 'difficult'
  ).length

  let currentDifficulty = profile.currentDifficulty
  if (success && consecutiveSuccesses % 3 === 0 && completion >= 82) {
    currentDifficulty = nextDifficulty(currentDifficulty)
  }
  if (struggle && consecutiveStruggles >= 2 && consecutiveStruggles % 2 === 0) {
    currentDifficulty = prevDifficulty(currentDifficulty)
  }

  const explanationRequests =
    profile.explanationRequests + (feeling === 'difficult' ? 1 : 0)

  let longActivityAbandoned = profile.longActivityAbandoned
  if (activity.duration > 15 && outcome !== 'completed') {
    longActivityAbandoned = true
  } else if (success && consecutiveSuccesses >= 2) {
    longActivityAbandoned = false
  }

  const timeUsed = activity.duration
  const availableMinutes = Math.max(0, profile.availableMinutes - timeUsed)

  const completedToday = profile.completedToday + (outcome === 'completed' ? 1 : 0)

  return {
    ...profile,
    recentCompletionRate: completion,
    completedToday,
    typicalSuccessfulMinutes,
    currentDifficulty,
    repeatedMistakes,
    revisionTopics,
    explanationRequests,
    longActivityAbandoned,
    availableMinutes,
  }
}

export function recordExplanationRequest(
  profile: LearningProfile
): LearningProfile {
  return {
    ...profile,
    explanationRequests: profile.explanationRequests + 1,
  }
}
