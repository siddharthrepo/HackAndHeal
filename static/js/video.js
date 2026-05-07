/**
 * Video consultation for HealthMeter
 *
 * Uses Daily.co call-object mode (NOT iframe) so we have direct access to
 * every participant's MediaStreamTrack.  This lets us:
 *   - Render local + remote video ourselves
 *   - Record local and remote audio into SEPARATE streams
 *   - Send both files to the backend for per-speaker transcription
 *
 * Why two recorders instead of a mixed stream:
 *   Whisper is a single-speaker ASR. Mixing local + remote into one track
 *   causes overlap/clipping and Whisper drops most of the conversation.
 *   Recording each speaker in isolation lets the backend transcribe each
 *   cleanly, then merge the segments by timestamp with speaker labels.
 */

// ── State ─────────────────────────────────────────────────────
let callObject = null;
let isCallActive = false;
let callCleanupDone = false;
let callStartTime = null;
let callTimerInterval = null;

// Per-speaker audio recording (one recorder per side)
let audioContext = null;
let recorders = {
    local:  { destination: null, recorder: null, chunks: [], source: null, started: false },
    remote: { destination: null, recorder: null, chunks: [], source: null, started: false },
};
let remoteSessionId = null; // Daily.co session id of the remote participant

// Transcription
let transcriptionInProgress = false;

// Config (populated on DOMContentLoaded)
let roomName = null;
let token = null;
let appointmentId = null;
let localRole = null; // 'doctor' or 'patient'

// DOM element refs
let localVideoEl, remoteVideoEl, waitingOverlay;
let endCallBtn, muteAudioBtn, muteVideoBtn;
let callStatusEl, callDurationEl, errorDisplayEl, loadingIndicatorEl;
let chatForm, chatInput, chatMessages;

console.log('video.js loaded');

// ── Bootstrap ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Cache DOM elements
    localVideoEl       = document.getElementById('local-video');
    remoteVideoEl      = document.getElementById('remote-video');
    waitingOverlay     = document.getElementById('waiting-overlay');
    endCallBtn         = document.getElementById('end-call-btn');
    muteAudioBtn       = document.getElementById('mute-audio-btn');
    muteVideoBtn       = document.getElementById('mute-video-btn');
    callStatusEl       = document.getElementById('call-status');
    callDurationEl     = document.getElementById('call-duration');
    errorDisplayEl     = document.getElementById('error-display');
    loadingIndicatorEl = document.getElementById('loading-indicator');
    chatForm           = document.getElementById('chat-form');
    chatInput          = document.getElementById('chat-input');
    chatMessages       = document.getElementById('chat-messages');

    roomName      = document.getElementById('room-name')?.value;
    token         = document.getElementById('room-token')?.value;
    appointmentId = document.getElementById('appointment-id')?.value;
    localRole     = document.getElementById('local-role')?.value || 'patient';

    // Wire up buttons
    if (endCallBtn)   endCallBtn.addEventListener('click', endCall);
    if (muteAudioBtn) muteAudioBtn.addEventListener('click', toggleAudio);
    if (muteVideoBtn) muteVideoBtn.addEventListener('click', toggleVideo);

    initializeChat();
    initializeCall();
});

// ── Call Initialization ───────────────────────────────────────
async function initializeCall() {
    try {
        updateCallStatus('Initializing...');

        if (!roomName || !token) {
            displayError('Missing room name or token. Cannot join call.');
            return;
        }

        // createCallObject gives us raw track access (unlike createFrame)
        callObject = DailyIframe.createCallObject({
            audioSource: true,
            videoSource: true,
        });

        // Register event handlers
        callObject.on('joined-meeting',     handleJoinedMeeting);
        callObject.on('left-meeting',       handleLeftMeeting);
        callObject.on('participant-joined',  handleParticipantJoined);
        callObject.on('participant-left',    handleParticipantLeft);
        callObject.on('track-started',       handleTrackStarted);
        callObject.on('track-stopped',       handleTrackStopped);
        callObject.on('error',               handleCallError);
        callObject.on('app-message',         handleAppMessage);

        updateCallStatus('Joining call...');
        await callObject.join({
            url: `https://chikitsa360.daily.co/${roomName}`,
            token: token,
        });
    } catch (error) {
        displayError('Failed to initialize call: ' + error.message);
        console.error('Call init error:', error);
    }
}

// ── Daily.co Event Handlers ───────────────────────────────────

function handleJoinedMeeting() {
    console.log('Joined meeting');
    isCallActive = true;
    callCleanupDone = false;

    updateCallStatus('Connected — waiting for others...');
    document.getElementById('call-controls')?.classList.remove('hidden');

    startCallTimer();
    setupAudioRecording();
}

function handleLeftMeeting() {
    console.log('Left meeting');
    handleCallCleanup();
}

function handleParticipantJoined(event) {
    console.log('Participant joined:', event.participant.user_name || event.participant.session_id);
    if (waitingOverlay) waitingOverlay.classList.add('hidden');
    updateCallStatus('Connected');
}

function handleParticipantLeft(event) {
    const pid = event.participant.session_id;
    console.log('Participant left:', pid);

    // Disconnect their audio source from the remote recorder, but DON'T stop
    // the recorder — they may rejoin, and stopping now would discard chunks.
    if (pid === remoteSessionId) {
        disconnectSource('remote');
    }
    document.getElementById(`remote-audio-${pid}`)?.remove();

    // Clear remote video
    if (remoteVideoEl) remoteVideoEl.srcObject = null;
    if (waitingOverlay) waitingOverlay.classList.remove('hidden');
    updateCallStatus('Other participant left');
}

function handleTrackStarted(event) {
    const { participant, track } = event;
    if (!participant || !track) return;

    if (participant.local) {
        if (track.kind === 'video' && localVideoEl) {
            localVideoEl.srcObject = new MediaStream([track]);
        }
        if (track.kind === 'audio') {
            attachTrackToRecorder('local', track);
        }
    } else {
        if (track.kind === 'video' && remoteVideoEl) {
            remoteVideoEl.srcObject = new MediaStream([track]);
            if (waitingOverlay) waitingOverlay.classList.add('hidden');
        }
        if (track.kind === 'audio') {
            // Play remote audio so the user can hear the other person
            playRemoteAudio(participant.session_id, track);
            remoteSessionId = participant.session_id;
            attachTrackToRecorder('remote', track);
        }
    }
}

function handleTrackStopped(event) {
    const { participant, track } = event;
    if (!participant || !track) return;

    if (participant.local && track.kind === 'video' && localVideoEl) {
        localVideoEl.srcObject = null;
    }
    if (!participant.local && track.kind === 'video' && remoteVideoEl) {
        remoteVideoEl.srcObject = null;
    }
    // Audio track-stopped during a call (e.g. mute) doesn't kill the recorder.
    // Recorders keep running on a silent stream so timestamps stay aligned;
    // the user's mic toggling on/off just produces a quiet section in the file.
}

function handleCallError(event) {
    console.error('Call error:', event);
    displayError('Call error: ' + (event.errorMsg || 'Unknown error'));
}

function handleAppMessage(event) {
    if (!event.data?.message) return;
    const local = callObject.participants().local;
    const sender = (event.fromId === local.session_id) ? 'You' : 'Other participant';
    addChatMessage(sender, event.data.message);
}

// ── Remote Audio Playback ─────────────────────────────────────
// In call-object mode Daily.co does NOT play remote audio automatically.
// We must create <audio> elements ourselves.

function playRemoteAudio(participantId, track) {
    let el = document.getElementById(`remote-audio-${participantId}`);
    if (!el) {
        el = document.createElement('audio');
        el.id = `remote-audio-${participantId}`;
        el.autoplay = true;
        document.body.appendChild(el);
    }
    el.srcObject = new MediaStream([track]);
    el.play().catch(err => console.warn('Audio autoplay blocked:', err));
}

// ── Per-Speaker Audio Recording ───────────────────────────────
// Each side gets its own MediaStreamDestination + MediaRecorder so that:
//   - Whisper sees clean single-speaker audio (no overlap, no clipping)
//   - The backend can label segments by speaker (Doctor / Patient)
//   - Both files share a wall-clock start, so segment timestamps align

function setupAudioRecording() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        recorders.local.destination  = audioContext.createMediaStreamDestination();
        recorders.remote.destination = audioContext.createMediaStreamDestination();
        // Recorders are created lazily once each side's first track arrives.
    } catch (err) {
        console.error('AudioContext setup failed:', err);
        displayError('Audio recording setup failed');
    }
}

function pickMimeType() {
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) return 'audio/webm;codecs=opus';
    if (MediaRecorder.isTypeSupported('audio/webm'))             return 'audio/webm';
    return '';
}

function attachTrackToRecorder(side, track) {
    const slot = recorders[side];
    if (!audioContext || !slot || !slot.destination) return;

    // Replace any previous source for this side (e.g., Daily replaces a track)
    disconnectSource(side);

    try {
        const stream = new MediaStream([track]);
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(slot.destination);
        slot.source = source;
        console.log(`Audio attached: ${side}`);

        if (!slot.started) {
            startRecorder(side);
        }
    } catch (err) {
        console.error(`Failed to attach ${side} audio:`, err);
    }
}

function disconnectSource(side) {
    const slot = recorders[side];
    if (slot?.source) {
        try { slot.source.disconnect(); } catch (e) { /* ok */ }
        slot.source = null;
    }
}

function startRecorder(side) {
    const slot = recorders[side];
    if (!slot || slot.started) return;

    try {
        const mimeType = pickMimeType();
        const options = mimeType ? { mimeType } : {};
        const recorder = new MediaRecorder(slot.destination.stream, options);
        slot.recorder = recorder;
        slot.chunks = [];

        recorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) slot.chunks.push(e.data);
        };

        recorder.start(1000);
        slot.started = true;
        console.log(`Recorder started: ${side} (${mimeType || 'browser default'})`);
    } catch (err) {
        console.error(`Failed to start ${side} recorder:`, err);
    }
}

function stopAllRecorders() {
    for (const side of ['local', 'remote']) {
        const slot = recorders[side];
        if (!slot?.recorder) continue;
        try {
            if (slot.recorder.state !== 'inactive') slot.recorder.stop();
        } catch (err) {
            console.error(`Error stopping ${side} recorder:`, err);
        }
        slot.started = false;
        disconnectSource(side);
    }

    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close().catch(() => {});
        audioContext = null;
    }
    console.log('All recorders stopped');
}

function getBlob(side) {
    const chunks = recorders[side]?.chunks || [];
    if (chunks.length === 0) return null;
    return new Blob(chunks, { type: 'audio/webm' });
}

// ── Call Lifecycle ────────────────────────────────────────────

async function endCall() {
    if (!isCallActive || !callObject) return;
    updateCallStatus('Ending call...');

    try {
        await callObject.leave();
        // handleLeftMeeting will fire → handleCallCleanup
    } catch (err) {
        console.error('Error leaving call:', err);
        handleCallCleanup(); // force cleanup on failure
    }
}

/**
 * Single cleanup path — guarded by callCleanupDone so it only runs once,
 * regardless of whether triggered by endCall() or handleLeftMeeting().
 */
function handleCallCleanup() {
    if (callCleanupDone) return;
    callCleanupDone = true;
    console.log('Cleaning up call...');

    stopCallTimer();
    stopAllRecorders();

    // MediaRecorder.stop() flushes asynchronously — wait one tick so the
    // final ondataavailable fires before we pull the blobs.
    setTimeout(() => {
        const localBlob  = getBlob('local');
        const remoteBlob = getBlob('remote');
        if (localBlob || remoteBlob) {
            submitTranscription(localBlob, remoteBlob);
        }
        // Free chunk memory
        recorders.local.chunks  = [];
        recorders.remote.chunks = [];
    }, 250);

    // Remove dynamically created remote audio elements
    document.querySelectorAll('audio[id^="remote-audio-"]').forEach(el => el.remove());

    // Reset state
    isCallActive = false;
    callObject = null;

    // Reset UI
    if (localVideoEl)  localVideoEl.srcObject  = null;
    if (remoteVideoEl) remoteVideoEl.srcObject = null;
    document.getElementById('call-controls')?.classList.add('hidden');
    updateCallStatus('Call ended');
}

// ── Transcription Submission ──────────────────────────────────

function submitTranscription(localBlob, remoteBlob) {
    if (transcriptionInProgress) return;
    const localSize  = localBlob  ? localBlob.size  : 0;
    const remoteSize = remoteBlob ? remoteBlob.size : 0;
    if (localSize === 0 && remoteSize === 0) return;
    if (!appointmentId) {
        displayError('Appointment ID missing');
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        displayError('Security token missing');
        return;
    }

    transcriptionInProgress = true;
    if (loadingIndicatorEl) loadingIndicatorEl.classList.remove('hidden');

    const formData = new FormData();
    if (localBlob  && localSize  > 0) formData.append('local_audio',  localBlob,  'local.webm');
    if (remoteBlob && remoteSize > 0) formData.append('remote_audio', remoteBlob, 'remote.webm');
    formData.append('local_role', localRole || 'patient');
    console.log(`Submitting audio: local=${localSize}B remote=${remoteSize}B role=${localRole}`);

    fetch(`/transcription/create/${appointmentId}/`, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken },
        credentials: 'same-origin',
    })
    .then(resp => {
        if (!resp.ok) {
            return resp.json()
                .catch(() => { throw new Error(`Server error ${resp.status}`); })
                .then(data => { throw new Error(data.error || `Server error ${resp.status}`); });
        }
        return resp.json();
    })
    .then(() => {
        displaySuccess('Transcription submitted — emails will be sent shortly.');
    })
    .catch(err => {
        displayError('Transcription failed: ' + err.message);
        console.error('Transcription error:', err);
    })
    .finally(() => {
        transcriptionInProgress = false;
        if (loadingIndicatorEl) loadingIndicatorEl.classList.add('hidden');
    });
}

// ── UI Controls ───────────────────────────────────────────────

function toggleAudio() {
    if (!callObject) return;
    const isOn = callObject.localAudio();
    callObject.setLocalAudio(!isOn);

    if (!muteAudioBtn) return;
    if (isOn) {
        // Was on → now muted
        muteAudioBtn.innerHTML =
            '<svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
            'd="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg> Unmute';
        muteAudioBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
        muteAudioBtn.classList.add('bg-green-600', 'hover:bg-green-700');
    } else {
        // Was muted → now on
        muteAudioBtn.innerHTML =
            '<svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
            'd="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clip-rule="evenodd"></path>' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
            'd="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"></path></svg> Mute';
        muteAudioBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
        muteAudioBtn.classList.add('bg-red-600', 'hover:bg-red-700');
    }
}

function toggleVideo() {
    if (!callObject) return;
    const isOn = callObject.localVideo();
    callObject.setLocalVideo(!isOn);

    if (!muteVideoBtn) return;
    if (isOn) {
        // Was on → now off
        muteVideoBtn.innerHTML =
            '<svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
            'd="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg> Enable Video';
        muteVideoBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
        muteVideoBtn.classList.add('bg-green-600', 'hover:bg-green-700');
    } else {
        // Was off → now on
        muteVideoBtn.innerHTML =
            '<svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
            'd="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg> Disable Video';
        muteVideoBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
        muteVideoBtn.classList.add('bg-red-600', 'hover:bg-red-700');
    }
}

// ── UI Helpers ────────────────────────────────────────────────

function updateCallStatus(status) {
    if (!callStatusEl) return;
    callStatusEl.textContent = status;
    callStatusEl.classList.remove('bg-green-600', 'bg-red-600', 'bg-yellow-500');

    if (status.includes('Connected')) {
        callStatusEl.classList.add('bg-green-600');
    } else if (status.includes('ended') || status.includes('left') || status.includes('Error')) {
        callStatusEl.classList.add('bg-red-600');
    } else {
        callStatusEl.classList.add('bg-yellow-500');
    }
}

function displayError(message) {
    console.error(message);
    if (!errorDisplayEl) return;
    errorDisplayEl.textContent = message;
    errorDisplayEl.classList.remove('hidden', 'text-green-500');
    errorDisplayEl.classList.add('text-red-400');
    setTimeout(() => errorDisplayEl.classList.add('hidden'), 5000);
}

function displaySuccess(message) {
    console.log(message);
    if (!errorDisplayEl) return;
    errorDisplayEl.textContent = message;
    errorDisplayEl.classList.remove('hidden', 'text-red-400');
    errorDisplayEl.classList.add('text-green-500');
    setTimeout(() => errorDisplayEl.classList.add('hidden'), 5000);
}

function startCallTimer() {
    callStartTime = new Date();
    callTimerInterval = setInterval(() => {
        if (!callDurationEl) return;
        const diff = Date.now() - callStartTime.getTime();
        const h = String(Math.floor(diff / 3600000)).padStart(2, '0');
        const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
        const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
        callDurationEl.textContent = `${h}:${m}:${s}`;
    }, 1000);
}

function stopCallTimer() {
    if (callTimerInterval) {
        clearInterval(callTimerInterval);
        callTimerInterval = null;
    }
}

// ── Chat ──────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function initializeChat() {
    if (!chatForm || !chatInput || !chatMessages) return;

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message || !callObject) return;

        callObject.sendAppMessage({ message }, '*');
        addChatMessage('You', message);
        chatInput.value = '';
    });
}

function addChatMessage(sender, message) {
    if (!chatMessages) return;
    const el = document.createElement('div');
    el.className = 'mb-3';
    el.innerHTML =
        `<p class="text-sm font-medium text-gray-600">${escapeHtml(sender)}</p>` +
        `<div class="bg-gray-100 rounded-lg p-3 mt-1">` +
        `<p class="text-gray-800">${escapeHtml(message)}</p></div>`;
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
