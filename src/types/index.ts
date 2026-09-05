export type Format = 'Visual' | 'Text' | 'Audio-ready'
export type Difficulty = 'Easy' | 'Intermediate' | 'Challenging'
export type ActivityKind = 'Practice' | 'Revision' | 'Learn'
export type Outcome = 'completed' | 'partial' | 'skipped'
export type Feeling = 'easy' | 'manageable' | 'difficult'

export interface LearningActivity {
  id: string
  subject: string
  topic: string
  title: string
  kind: ActivityKind
  duration: number
  difficulty: Difficulty
  format: Format
  priority: number
  explanation: string
  example: string
  question: string
  answer: string
}
export interface LearningProfile {
  name: string
  preferredFormat: Format
  typicalSuccessfulMinutes: number
  currentDifficulty: Difficulty
  recentCompletionRate: number
  revisionTopics: string[]
  repeatedMistakes: string[]
  longActivityAbandoned: boolean
  availableMinutes: number
  explanationRequests: number
  reducedMotion: boolean
  fontScale: 'Standard' | 'Large'
  simpleLanguage: boolean
  completedToday: number
  goalToday: number
}
export interface ActivityRecord {
  activityId: string
  topic: string
  duration: number
  outcome: Outcome
  feeling: Feeling
  timestamp: string
}
export interface Recommendation {
  activity: LearningActivity
  duration: number
  difficulty: Difficulty
  format: Format
  kind: ActivityKind
  breakMinutes: number
  supportNeeded: boolean
  score: number
  reasons: string[]
  bullets?: string[]
  flags?: string[]
}
