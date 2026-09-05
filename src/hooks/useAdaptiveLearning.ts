import { useEffect, useMemo, useState } from 'react'
import { activities, initialHistory, initialProfile } from '../data/mockData'
import {
  generateRecommendation,
  recordExplanationRequest,
  updateLearningProfile,
} from '../engine/adaptiveDecisionEngine'
import type { ActivityRecord, Feeling, LearningProfile, Outcome } from '../types'

const PROFILE_KEY = 'learnloop.profile.v1'
const HISTORY_KEY = 'learnloop.history.v1'

function loadProfile(): LearningProfile {
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    if (raw) return { ...initialProfile, ...(JSON.parse(raw) as LearningProfile) }
  } catch (_e) {
    /* ignore */
  }
  return initialProfile
}

function loadHistory(): ActivityRecord[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (raw) return JSON.parse(raw) as ActivityRecord[]
  } catch (_e) {
    /* ignore */
  }
  return initialHistory
}

export function useAdaptiveLearning() {
  const [profile, setProfile] = useState<LearningProfile>(() => loadProfile())
  const [history, setHistory] = useState<ActivityRecord[]>(() => loadHistory())

  useEffect(() => {
    try {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
    } catch (_e) {
      /* ignore */
    }
  }, [profile])

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
    } catch (_e) {
      /* ignore */
    }
  }, [history])

  const recommendation = useMemo(
    () => generateRecommendation(activities, profile, history) as any,
    [profile, history]
  )

  const recordOutcome = (outcome: Outcome, feeling: Feeling, responseTime?: number) => {
    const a = recommendation.activity
    const newHistory: ActivityRecord[] = [
      ...history,
      {
        activityId: a.id,
        topic: a.topic,
        duration: recommendation.duration,
        outcome,
        feeling,
        timestamp: new Date().toLocaleDateString(),
      },
    ]
    setHistory(newHistory)
    setProfile((p) => updateLearningProfile(p, a, outcome, feeling, newHistory))
  }

  const recordHelp = () => {
    setProfile((p) => recordExplanationRequest(p))
  }

  const setAvailableMinutes = (minutes: number) => {
    setProfile((p) => ({ ...p, availableMinutes: Math.max(0, minutes) }))
  }

  const reset = () => {
    setProfile(initialProfile)
    setHistory(initialHistory)
    try {
      localStorage.removeItem(PROFILE_KEY)
      localStorage.removeItem(HISTORY_KEY)
    } catch (_e) {
      /* ignore */
    }
  }

  return {
    profile,
    setProfile,
    history,
    recommendation,
    recordOutcome,
    recordHelp,
    setAvailableMinutes,
    reset,
    activities,
  }
}
