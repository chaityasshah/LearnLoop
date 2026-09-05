import type { ActivityRecord, LearningActivity, LearningProfile, Outcome, Feeling } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function getStudent(studentId: string) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}`);
    if (!res.ok) throw new Error('Failed to fetch student');
    return res.json();
}

export async function getDemoStudent() {
    const res = await fetch(`${API_BASE_URL}/api/students/demo`);
    if (!res.ok) throw new Error('Failed to fetch demo student');
    return res.json();
}

export async function createStudent(data: { name: string; email: string }) {
    const res = await fetch(`${API_BASE_URL}/api/students/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to create student');
    return res.json();
}

export async function getLearningProfile(studentId: string): Promise<LearningProfile> {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/profile`);
    if (!res.ok) throw new Error('Failed to fetch profile');
    const data = await res.json();
    return {
        name: data.name || data.student_name || "Student",
        currentDifficulty: data.current_difficulty,
        preferredFormat: data.preferred_format,
        typicalSuccessfulMinutes: data.typical_successful_minutes,
        availableMinutes: data.available_minutes,
        recentCompletionRate: data.recent_completion_rate || 80,
        completedToday: data.completed_today || 0,
        goalToday: data.goal_today || 3,
        explanationRequests: data.explanation_requests || 0,
        reducedMotion: data.reduced_motion || false,
        fontScale: data.font_scale || 'Standard',
        simpleLanguage: data.simple_language || false,
        repeatedMistakes: data.repeated_mistakes || [],
        revisionTopics: data.revision_topics || [],
        longActivityAbandoned: data.long_activity_abandoned || false
    } as LearningProfile;
}

export async function getActivities(): Promise<LearningActivity[]> {
    const res = await fetch(`${API_BASE_URL}/api/activities/`);
    if (!res.ok) throw new Error('Failed to fetch activities');
    return res.json();
}

export async function getHistory(studentId: string): Promise<ActivityRecord[]> {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/history`);
    if (!res.ok) throw new Error('Failed to fetch history');
    const raw = await res.json();
    return raw.map((h: any) => ({
        id: h.id,
        activityId: h.activity_id,
        topic: h.topic,
        title: h.title,
        recommendedDuration: h.recommended_duration,
        actualDuration: h.actual_duration,
        difficulty: h.difficulty,
        format: h.format,
        outcome: h.outcome,
        feeling: h.feeling,
        timestamp: h.timestamp
    }));
}

export async function getRecommendation(studentId: string) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/recommendation`);
    if (!res.ok) throw new Error('Failed to fetch recommendation');
    return res.json();
}

export async function recordOutcome(studentId: string, activityId: string, outcome: Outcome, feeling: Feeling, duration: number, snapshotId?: string, responseTimeSeconds?: number) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/activities/${activityId}/outcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            actual_duration: duration,
            outcome,
            feeling,
            snapshot_id: snapshotId,
            response_time: responseTimeSeconds || duration * 60
        })
    });
    if (!res.ok) throw new Error('Failed to record outcome');
    return res.json();
}

export async function recordHelpRequest(studentId: string, activityId: string, context: string) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/help-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            activity_id: activityId,
            context
        })
    });
    if (!res.ok) throw new Error('Failed to record help request');
    return res.json();
}

export async function updateProfileMinutes(studentId: string, availableMinutes: number) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/profile`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ available_minutes: availableMinutes })
    });
    if (!res.ok) throw new Error('Failed to update minutes');
    return res.json();
}

export async function sendChatMessage(
    studentId: string, 
    activityId: string, 
    topic: string, 
    question: string, 
    currentDifficulty: string, 
    history: {role: string, content: string}[]
) {
    const res = await fetch(`${API_BASE_URL}/api/students/${studentId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            activity_id: activityId,
            topic: topic,
            question: question,
            current_difficulty: currentDifficulty,
            history: history
        })
    });
    if (!res.ok) throw new Error('Failed to fetch chat response from Study Buddy');
    return res.json();
}
