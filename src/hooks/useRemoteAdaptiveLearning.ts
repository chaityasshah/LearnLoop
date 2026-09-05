import { useEffect, useState, useCallback } from 'react'
import type { ActivityRecord, Feeling, LearningProfile, Outcome, LearningActivity } from '../types'
import * as api from '../services/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'


export function useRemoteAdaptiveLearning() {
    const [studentId, setStudentId] = useState<string | null>(null)
    const [profile, setProfile] = useState<LearningProfile | null>(null)
    const [history, setHistory] = useState<ActivityRecord[]>([])
    const [activities, setActivities] = useState<LearningActivity[]>([])
    const [recommendation, setRecommendation] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const checkAuth = useCallback(() => {
        const storedId = localStorage.getItem('learnloop_student_id')
        if (storedId) {
            setStudentId(storedId)
        } else {
            setLoading(false) // Ready to show onboarding
        }
    }, [])

    const login = async (name: string, email: string) => {
        try {
            setLoading(true)
            const student = await api.createStudent({ name, email })
            localStorage.setItem('learnloop_student_id', student.id)
            setStudentId(student.id)
            setError(null)
        } catch (err: any) {
            setError(err.message)
            setLoading(false)
        }
    }

    const fetchData = useCallback(async (id: string) => {
        try {
            setLoading(true)
            const [p, h, a, r] = await Promise.all([
                api.getLearningProfile(id),
                api.getHistory(id),
                api.getActivities(),
                api.getRecommendation(id)
            ])
            setProfile(p)
            setHistory(h)
            setActivities(a)
            setRecommendation(r)
            setError(null)
        } catch (err: any) {
            setError(err.message)
            if (err.message.includes('404')) {
                // Invalid user, reset
                localStorage.removeItem('learnloop_student_id')
                setStudentId(null)
            }
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        checkAuth()
    }, [checkAuth])

    useEffect(() => {
        if (studentId) fetchData(studentId)
    }, [fetchData, studentId])

    const recordOutcome = async (outcome: Outcome, feeling: Feeling, responseTime?: number) => {
        if (!studentId || !recommendation) return
        try {
            const data = await api.recordOutcome(
                studentId, 
                recommendation.activity.id, 
                outcome, 
                feeling, 
                recommendation.duration,
                recommendation.snapshot_id,
                responseTime
            )
            setRecommendation(data.recommendation)
            // Still fetch history and profile to keep them in sync
            const [p, h] = await Promise.all([
                api.getLearningProfile(studentId),
                api.getHistory(studentId)
            ])
            setProfile(p)
            setHistory(h)
        } catch (err: any) {
            console.error("Failed to record outcome:", err)
        }
    }

    const recordHelp = async () => {
        if (!studentId || !recommendation) return
        try {
            await api.recordHelpRequest(studentId, recommendation.activity.id, "Student clicked 'I need help'")
            await fetchData(studentId)
        } catch (err: any) {
            console.error("Failed to record help request:", err)
        }
    }

    const setAvailableMinutes = async (minutes: number) => {
        if (!studentId) return
        try {
            await api.updateProfileMinutes(studentId, Math.max(0, minutes))
            await fetchData(studentId)
        } catch (err: any) {
            console.error("Failed to update available minutes:", err)
        }
    }

    const reset = async () => {
        if (studentId) {
            await fetch(`${API_BASE_URL}/api/students/${studentId}/reset`, { method: 'POST' })
            await fetchData(studentId)
        }
    }

    return {
        studentId,
        login,
        profile,
        setProfile, // Only local setProfile can be instantaneous, remote relies on backend but we provide it for compatibility
        history,
        recommendation,
        recordOutcome,
        recordHelp,
        setAvailableMinutes,
        reset,
        activities,
        loading,
        error
    }
}
