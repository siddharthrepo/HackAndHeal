/**
 * Video consultation functionality for Chikitsa360
 * Integrates Daily.co WebRTC for video calls
 */

// Initialize variables
let call = null;
let localStream = null;
let remoteStream = null;
let isCallActive = false;
let audioRecorder = null;
let audioChunks = [];
let isRecording = false;
let callStartTime = null;
let callTimer = null;
let transcriptionInProgress = false;

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    const videoContainer = document.getElementById('video-container');
    const localVideo = document.getElementById('local-video');
    const remoteVideo = document.getElementById('remote-video');
    const joinBtn = document.getElementById('join-call-btn');
    const endCallBtn = document.getElementById('end-call-btn');
    const muteAudioBtn = document.getElementById('mute-audio-btn');
    const muteVideoBtn = document.getElementById('mute-video-btn');
    const callStatusIndicator = document.getElementById('call-status');
    const callDuration = document.getElementById('call-duration');
    const errorDisplay = document.getElementById('error-display');
    const transcribeBtn = document.getElementById('transcribe-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const patientInfoPanel = document.getElementById('patient-info-panel');
    const roomName = document.getElementById('room-name').value;
    const token = document.getElementById('room-token').value;
    const appointmentId = document.getElementById('appointment-id').value;

    /**
     * Initialize the Daily.co call
     */
    async function initializeCall() {
        try {
            updateCallStatus('Initializing call...');
            
            // Create Daily.co call object
            call = DailyIframe.createFrame({
                showLeaveButton: false,
                iframeStyle: {
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    border: 'none',
                    backgroundColor: 'transparent'
                }
            });
            
            // Add call frame to container
            videoContainer.appendChild(call.iframe);
            
            // Set up event listeners
            call.on('joined-meeting', handleJoinedMeeting);
            call.on('left-meeting', handleLeftMeeting);
            call.on('participant-joined', handleParticipantJoined);
            call.on('participant-left', handleParticipantLeft);
            call.on('error', handleCallError);
            
            // Join the call if token and room name are available
            if (token && roomName) {
                joinCall();
            }
            
        } catch (error) {
            displayError('Failed to initialize call: ' + error.message);
        }
    }
    
    /**
     * Join the Daily.co call
     */
    async function joinCall() {
        try {
            updateCallStatus('Joining call...');
            
            // If audio recording was previously enabled, set up recording
            setupAudioRecording();
            
            // Join the meeting with token
            await call.join({
                url: `https://chikitsa360.daily.co/${roomName}`,
                token: token
            });
            
            // Show call controls
            document.getElementById('call-controls').classList.remove('hidden');
            
            // Hide join button
            if (joinBtn) joinBtn.classList.add('hidden');
            
            // Show end call button
            endCallBtn.classList.remove('hidden');
            
            isCallActive = true;
            startCallTimer();
            
        } catch (error) {
            displayError('Failed to join call: ' + error.message);
        }
    }
    
    /**
     * End the Daily.co call
     */
    async function endCall() {
        try {
            if (!isCallActive) return;
            
            updateCallStatus('Ending call...');
            
            // Stop timer
            stopCallTimer();
            
            // Stop recording if active
            if (isRecording) {
                stopRecording();
            }
            
            // Leave the meeting
            await call.leave();
            
            // Remove call frame
            if (call && call.iframe) {
                videoContainer.removeChild(call.iframe);
            }
            
            // Reset call object
            call = null;
            isCallActive = false;
            
            // Update UI
            document.getElementById('call-controls').classList.add('hidden');
            endCallBtn.classList.add('hidden');
            if (joinBtn) joinBtn.classList.remove('hidden');
            
            updateCallStatus('Call ended');
            
        } catch (error) {
            displayError('Error ending call: ' + error.message);
        }
    }
    
    /**
     * Toggle audio mute state
     */
    function toggleAudio() {
        if (!call) return;
        
        const audioState = call.participants().local.audio;
        call.setLocalAudio(!audioState);
        
        // Update button UI
        if (audioState) {
            muteAudioBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg> Unmute';
            muteAudioBtn.classList.remove('bg-red-600');
            muteAudioBtn.classList.add('bg-green-600');
        } else {
            muteAudioBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clip-rule="evenodd"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"></path></svg> Mute';
            muteAudioBtn.classList.remove('bg-green-600');
            muteAudioBtn.classList.add('bg-red-600');
        }
    }
    
    /**
     * Toggle video mute state
     */
    function toggleVideo() {
        if (!call) return;
        
        const videoState = call.participants().local.video;
        call.setLocalVideo(!videoState);
        
        // Update button UI
        if (videoState) {
            muteVideoBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg> Enable Video';
            muteVideoBtn.classList.remove('bg-red-600');
            muteVideoBtn.classList.add('bg-green-600');
        } else {
            muteVideoBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg> Disable Video';
            muteVideoBtn.classList.remove('bg-green-600');
            muteVideoBtn.classList.add('bg-red-600');
        }
    }
    
    /**
     * Handle joined meeting event
     */
    function handleJoinedMeeting(event) {
        updateCallStatus('Connected');
        startRecording();
    }
    
    /**
     * Handle left meeting event
     */
    function handleLeftMeeting(event) {
        updateCallStatus('Disconnected');
        stopCallTimer();
        if (isRecording) {
            stopRecording();
        }
    }
    
    /**
     * Handle participant joined event
     */
    function handleParticipantJoined(event) {
        const participant = event.participant;
        updateCallStatus('Connected with ' + (participant.user_name || 'another participant'));
    }
    
    /**
     * Handle participant left event
     */
    function handleParticipantLeft(event) {
        updateCallStatus('Other participant left the call');
    }
    
    /**
     * Handle call errors
     */
    function handleCallError(event) {
        displayError('Call error: ' + event.errorMsg);
    }
    
    /**
     * Set up audio recording using MediaRecorder
     */
    function setupAudioRecording() {
        // Check if MediaRecorder is supported
        if (!window.MediaRecorder) {
            displayError('MediaRecorder not supported in this browser');
            return;
        }
        
        // Reset recording state
        audioChunks = [];
        isRecording = false;
        
        // Enable transcribe button if recording is possible
        if (transcribeBtn) {
            transcribeBtn.disabled = false;
        }
    }
    
    /**
     * Start audio recording
     */
    function startRecording() {
        if (!call || isRecording) return;
        
        try {
            // Get audio stream from call
            navigator.mediaDevices.getUserMedia({ audio: true, video: false })
                .then(stream => {
                    localStream = stream;
                    audioRecorder = new MediaRecorder(stream);
                    
                    audioRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                        }
                    };
                    
                    audioRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        if (transcribeBtn && transcribeBtn.dataset.autoTranscribe === 'true') {
                            submitTranscription(audioBlob);
                        }
                    };
                    
                    // Start recording
                    audioRecorder.start(1000);
                    isRecording = true;
                    
                    // Update UI
                    if (transcribeBtn) {
                        transcribeBtn.textContent = 'Transcribe Call (Recording...)';
                        transcribeBtn.classList.add('bg-red-600');
                        transcribeBtn.classList.remove('bg-blue-600');
                    }
                })
                .catch(error => {
                    displayError('Error accessing microphone: ' + error.message);
                });
                
        } catch (error) {
            displayError('Failed to start recording: ' + error.message);
        }
    }
    
    /**
     * Stop audio recording
     */
    function stopRecording() {
        if (!audioRecorder || !isRecording) return;
        
        try {
            audioRecorder.stop();
            isRecording = false;
            
            // Stop all tracks in the stream
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            
            // Update UI
            if (transcribeBtn) {
                transcribeBtn.textContent = 'Transcribe Call';
                transcribeBtn.classList.remove('bg-red-600');
                transcribeBtn.classList.add('bg-blue-600');
            }
            
        } catch (error) {
            displayError('Failed to stop recording: ' + error.message);
        }
    }
    
    /**
     * Submit audio for transcription
     */
    function submitTranscription(audioBlob) {
        if (transcriptionInProgress) return;
        
        try {
            transcriptionInProgress = true;
            
            // Show loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.remove('hidden');
            }
            
            // Create form data with audio blob
            const formData = new FormData();
            formData.append('audio_data', audioBlob, 'recording.mp3');
            
            // Get CSRF token
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Submit transcription request
            fetch(`/transcription/create/${appointmentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Monitor transcription status
                    monitorTranscriptionStatus(data.transcription_id);
                } else {
                    throw new Error(data.error || 'Failed to start transcription');
                }
            })
            .catch(error => {
                transcriptionInProgress = false;
                if (loadingIndicator) {
                    loadingIndicator.classList.add('hidden');
                }
                displayError('Transcription error: ' + error.message);
            });
            
        } catch (error) {
            transcriptionInProgress = false;
            if (loadingIndicator) {
                loadingIndicator.classList.add('hidden');
            }
            displayError('Failed to submit transcription: ' + error.message);
        }
    }
    
    /**
     * Monitor transcription status
     */
    function monitorTranscriptionStatus(transcriptionId) {
        const statusCheckInterval = setInterval(() => {
            fetch(`/transcription/status/${transcriptionId}/`, {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
                if (data.completed) {
                    clearInterval(statusCheckInterval);
                    transcriptionInProgress = false;
                    
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('hidden');
                    }
                    
                    // Show success message
                    showNotification('Transcription completed and sent via email!', 'success');
                    
                    // Redirect to transcription detail page
                    window.location.href = `/transcription/detail/${transcriptionId}/`;
                    
                } else if (data.failed) {
                    clearInterval(statusCheckInterval);
                    transcriptionInProgress = false;
                    
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('hidden');
                    }
                    
                    // Show error message
                    displayError('Transcription failed: ' + (data.error_message || 'Unknown error'));
                }
            })
            .catch(error => {
                clearInterval(statusCheckInterval);
                transcriptionInProgress = false;
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('hidden');
                }
                
                displayError('Failed to check transcription status: ' + error.message);
            });
        }, 5000); // Check every 5 seconds
    }
    
    /**
     * Update call status display
     */
    function updateCallStatus(status) {
        if (callStatusIndicator) {
            callStatusIndicator.textContent = status;
        }
    }
    
    /**
     * Display error message
     */
    function displayError(message) {
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.classList.remove('hidden');
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorDisplay.classList.add('hidden');
            }, 5000);
        }
        console.error(message);
    }
    
    /**
     * Start call timer
     */
    function startCallTimer() {
        callStartTime = new Date();
        callTimer = setInterval(updateCallDuration, 1000);
        updateCallDuration();
    }
    
    /**
     * Update call duration display
     */
    function updateCallDuration() {
        if (!callDuration || !callStartTime) return;
        
        const now = new Date();
        const diff = now - callStartTime;
        const seconds = Math.floor(diff / 1000) % 60;
        const minutes = Math.floor(diff / (1000 * 60)) % 60;
        const hours = Math.floor(diff / (1000 * 60 * 60));
        
        callDuration.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    /**
     * Stop call timer
     */
    function stopCallTimer() {
        if (callTimer) {
            clearInterval(callTimer);
            callTimer = null;
        }
    }
    
    /**
     * Display a notification message
     */
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-md z-50 ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('opacity-0', 'transition-opacity', 'duration-500');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 5000);
    }
    
    // Initialize UI event listeners
    if (joinBtn) {
        joinBtn.addEventListener('click', joinCall);
    }
    
    if (endCallBtn) {
        endCallBtn.addEventListener('click', endCall);
    }
    
    if (muteAudioBtn) {
        muteAudioBtn.addEventListener('click', toggleAudio);
    }
    
    if (muteVideoBtn) {
        muteVideoBtn.addEventListener('click', toggleVideo);
    }
    
    if (transcribeBtn) {
        transcribeBtn.addEventListener('click', function() {
            if (isRecording) {
                stopRecording();
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                submitTranscription(audioBlob);
            } else {
                displayError('No recording available to transcribe');
            }
        });
    }
    
    // Initialize call when page loads
    if (videoContainer && roomName && token) {
        initializeCall();
    }
    
    // Handle window unload event
    window.addEventListener('beforeunload', function(e) {
        if (isCallActive) {
            endCall();
        }
    });
});
