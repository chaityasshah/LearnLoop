import { useState } from 'react'
import { useAdaptiveLearning } from './useAdaptiveLearning'
import { useRemoteAdaptiveLearning } from './useRemoteAdaptiveLearning'
import { initialProfile, initialHistory, activities as mockActs } from '../data/mockData'

const ADAPTIVE_MODE = import.meta.env.VITE_ADAPTIVE_MODE || 'local'


export function useLearningController() {
    const [mode, setMode] = useState<'local' | 'remote'>(ADAPTIVE_MODE as 'local' | 'remote')

    const local = useAdaptiveLearning()
    const remote = useRemoteAdaptiveLearning()

    if (mode === 'remote') {
        if (remote.error) {
            return {
                ...local,
                loading: false,
                error: remote.error,
                fallbackToLocal: () => setMode('local')
            }
        }

        if (remote.loading) {
            return {
                ...local,
                loading: true,
                error: null,
                fallbackToLocal: () => setMode('local')
            }
        }
        
        if (!remote.studentId) {
            return {
                ...local,
                studentId: null,
                login: remote.login,
                loading: false,
                error: null,
                fallbackToLocal: () => setMode('local')
            }
        }

        if (!remote.profile || !remote.recommendation) {
            return {
                ...local,
                loading: true,
                error: null,
                fallbackToLocal: () => setMode('local')
            }
        }
        
        return {
            ...remote,
            loading: false,
            error: null,
            fallbackToLocal: () => setMode('local')
        }
    }

    return {
        ...local,
        loading: false,
        error: null,
        fallbackToLocal: () => setMode('local')
    }
}
