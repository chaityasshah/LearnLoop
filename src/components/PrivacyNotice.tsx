import React, { useState } from 'react';
import './PrivacyNotice.css'; // Optional styling

export function PrivacyNotice() {
    const [dismissed, setDismissed] = useState(false);

    if (dismissed) return null;

    return (
        <div className="privacy-notice">
            <div className="privacy-content">
                <strong>Data Collection & Privacy</strong>
                <p>
                    LearnLoop collects interaction data (such as topics studied, duration, and self-reported difficulty) to personalize your learning experience and improve future recommendations. 
                </p>
                <p>
                    We <strong>do not</strong> collect unnecessary behavioral surveillance, medical diagnoses, or use disability labels for inference. Your self-reported learning state is used strictly as a learning signal.
                </p>
                <button onClick={() => setDismissed(true)} className="primary sm">I understand</button>
            </div>
        </div>
    );
}
