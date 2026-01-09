// Mute/Unmute button functionality
function initMuteButtons() {
    const video = document.getElementById('hero-video');
    if (!video) {
        console.warn('mute.js: hero-video element not found');
        return;
    }

    const buttons = document.querySelectorAll('.mute-btn');
    if (!buttons.length) return;

    const updateLabels = () => {
        const label = video.muted ? 'Unmute' : 'Mute';
        buttons.forEach(btn => btn.textContent = label);
    };

    // Set initial state
    updateLabels();

    // Single click handler for all mute buttons (event delegation)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.mute-btn');
        if (!btn) return;
        console.log('mute.js: mute button clicked, current muted=', video.muted);

        try {
            video.muted = !video.muted;
            updateLabels();
            console.log('mute.js: video.muted set to', video.muted);
        } catch (err) {
            console.error('mute.js: error toggling muted', err);
        }
    });
}

// Initialize safely
document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', initMuteButtons)
    : initMuteButtons();
