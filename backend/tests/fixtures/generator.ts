import { generateRecommendation } from '../../../src/engine/adaptiveDecisionEngine';
import { initialProfile, activities, initialHistory } from '../../../src/data/mockData';
import type { ActivityRecord, Difficulty } from '../../../src/types';
import * as fs from 'fs';

const fixtures: Record<string, any> = {};

function addFixture(name: string, p: any, h: any, a: any) {
    fixtures[name] = {
        inputs: { profile: p, history: h, activities: a },
        expected: generateRecommendation(a, p, h)
    };
}

addFixture('initial', initialProfile, initialHistory, activities);

const history1: ActivityRecord[] = [...initialHistory, {
    id: "h2", activityId: "a1", topic: "Fractions", title: "Equivalent Fractions with Pictures",
    recommendedDuration: 10, actualDuration: 10, difficulty: "Easy", format: "Visual",
    outcome: "completed", feeling: "easy", timestamp: "2026-08-20T10:00:00Z"
}];
addFixture('one_success', initialProfile, history1, activities);

const history2: ActivityRecord[] = [...history1, {
    id: "h3", activityId: "a2", topic: "Fractions", title: "Compare Equivalent Fractions",
    recommendedDuration: 15, actualDuration: 15, difficulty: "Intermediate", format: "Visual",
    outcome: "completed", feeling: "manageable", timestamp: "2026-08-20T11:00:00Z"
}];
addFixture('multiple_successes', initialProfile, history2, activities);

const history_strug: ActivityRecord[] = [...initialHistory, {
    id: "s1", activityId: "a2", topic: "Fractions", title: "Compare Equivalent Fractions",
    recommendedDuration: 15, actualDuration: 20, difficulty: "Intermediate", format: "Visual",
    outcome: "partial", feeling: "difficult", timestamp: "2026-08-20T12:00:00Z"
}];
addFixture('one_struggle', initialProfile, history_strug, activities);

const history_rep_strug: ActivityRecord[] = [...history_strug, {
    id: "s2", activityId: "a3", topic: "Fractions", title: "Add Fractions",
    recommendedDuration: 15, actualDuration: 20, difficulty: "Intermediate", format: "Visual",
    outcome: "skipped", feeling: "difficult", timestamp: "2026-08-20T13:00:00Z"
}];
addFixture('repeated_struggle', initialProfile, history_rep_strug, activities);

const profile_help = { ...initialProfile, explanationRequests: 3 };
addFixture('help_request', profile_help, initialHistory, activities);

const profile_limited = { ...initialProfile, availableMinutes: 8 };
addFixture('limited_time', profile_limited, initialHistory, activities);

const profile_rev = { ...initialProfile, repeatedMistakes: ["Fractions"] };
addFixture('revision', profile_rev, initialHistory, activities);

const profile_chall = { ...initialProfile, currentDifficulty: "Challenging" as Difficulty, recentCompletionRate: 95 };
addFixture('challenging', profile_chall, history2, activities);

fs.writeFileSync(__dirname + '/engine_fixtures.json', JSON.stringify(fixtures, null, 2));
console.log('Wrote engine_fixtures.json with inputs and outputs');
