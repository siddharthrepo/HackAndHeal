/**
 * Video consultation functionality for Chikitsa360
 * Integrates Daily.co WebRTC for video calls with enhanced audio recording
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
let recordingStarted = false; // Flag to track if recording has started
let participantCount = 0; // Track number of participants

// DOM Elements
console.log("✅ video.js has been loaded");

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM ready, initializing video consultation...");
    initializeVideoConsultation();
});

// Main initialization function that will be called when DOM is ready
function initializeVideoConsultation() {
    console.log("✅ DOM fully loaded - starting initialization");

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
    
    // Get critical values and log them
    const roomName = document.getElementById('room-name')?.value;
    const token = document.getElementById('room-token')?.value;
    const appointmentId = document.getElementById('appointment-id')?.value;

    console.log("videoContainer:", videoContainer);
    console.log("roomName:", roomName);
    console.log("token:", token ? "Token present (hidden for security)" : "Token missing");
    console.log("appointmentId:", appointmentId);

    // Check for required elements before proceeding
    if (!videoContainer) console.warn("⚠️ videoContainer is missing or null");
    if (!roomName) console.warn("⚠️ roomName is missing or undefined");
    if (!token) console.warn("⚠️ token is missing or undefined");

    // Initialize chat functionality
    initializeChat();

    // Attach event listeners to UI elements
    if (endCallBtn) {
        endCallBtn.addEventListener('click', endCall);
    }
    
    if (muteAudioBtn) {
        muteAudioBtn.addEventListener('click', toggleAudio);
    }
    
    if (muteVideoBtn) {
        muteVideoBtn.addEventListener('click', toggleVideo);
    }

    // Initialize call automatically
    initializeCall();

    /**
     * Initialize the Daily.co call
     */
    async function initializeCall() {
        console.log("📞 Initializing call")
        try {
            updateCallStatus('🔄 Initializing call...');

            if (!videoContainer) {
                displayError('❌ videoContainer is not defined or not found in the DOM.');
                return;
            }

            // Create Daily.co call object and assign to global window
            console.log("Creating Daily.co frame with target:", videoContainer);
            window.call = DailyIframe.createFrame(videoContainer, {
                showLeaveButton: true,
                iframeStyle: {
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    border: 'none',
                    backgroundColor: 'transparent'
                },
            });

            call = window.call;

            console.log("✅ Daily call frame created:", call);

            // Set up event listeners
            call.on('joined-meeting', handleJoinedMeeting);
            call.on('left-meeting', handleLeftMeeting);
            call.on('participant-joined', handleParticipantJoined);
            call.on('participant-left', handleParticipantLeft);
            call.on('error', handleCallError);
            
            // Setup chat message handler if available
            if (window.setupChatMessageHandler) {
                window.setupChatMessageHandler();
            }
            
            console.log("✅ Call event listeners registered");

            // Attempt to join the call
            if (token && roomName) {
                console.log(`🔐 Joining room "${roomName}" with token...`);
                try {
                    await joinCall();
                } catch (err) {
                    displayError("❌ Error during joinCall: " + err.message);
                    console.error("Full join error:", err);
                }
            } else {
                displayError("❌ Missing token or room name. Cannot join call.");
                console.warn("token present:", !!token, "roomName:", roomName);
            }

        } catch (error) {
            displayError('❌ Failed to initialize call: ' + error.message);
            console.error("Full initialization error:", error);
        }
    }

    
    /**
     * Join the Daily.co call
     */
    async function joinCall() {
        try {
            console.log("🚀 Attempting to join room:", roomName);
            updateCallStatus('Joining call...');
            
            // Join the meeting with token
            console.log("🔑 Joining with token...");
            await call.join({
                url: `https://chikitsa360.daily.co/${roomName}`,
                token: token
            });
            
            console.log("✅ Successfully joined the call");
            
            // Show call controls
            document.getElementById('call-controls').classList.remove('hidden');
            
            // Hide join button if it exists
            if (joinBtn) joinBtn.classList.add('hidden');
            
            // Show end call button
            if (endCallBtn) endCallBtn.classList.remove('hidden');
            
            isCallActive = true;
            startCallTimer();
            
        } catch (error) {
            displayError('Failed to join call: ' + error.message);
            console.error("Full join error:", error);
        }
    }
    
    /**
     * End the Daily.co call
     */
    async function endCall() {
        try {
            console.log("📴 Ending call...");
            if (!isCallActive) {
                console.log("Call not active, nothing to end");
                return;
            }
            
            updateCallStatus('Ending call...');
            
            // Stop timer
            stopCallTimer();
            
            // Stop recording if active and trigger upload
            if (isRecording) {
                console.log("🛑 Stopping recording during endCall");
                stopRecording();
                console.log("🔄 Creating audio blob for upload");
                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                    console.log("📤 Submitting audio for transcription");
                    submitTranscription(audioBlob);
                } else {
                    console.log("⚠️ No audio chunks available for transcription");
                }
            }
            
            // Leave the meeting
            console.log("👋 Leaving the Daily.co meeting");
            await call.leave();
            
            // Reset call object
            call = null;
            isCallActive = false;
            participantCount = 0;
            recordingStarted = false; // Reset recording started flag
            
            // Update UI
            console.log("🔄 Updating UI after call end");
            document.getElementById('call-controls').classList.add('hidden');
            if (endCallBtn) endCallBtn.classList.add('hidden');
            if (joinBtn) joinBtn.classList.remove('hidden');
            
            updateCallStatus('Call ended');
            
        } catch (error) {
            displayError('Error ending call: ' + error.message);
            console.error("Full end call error:", error);
        }
    }
    
    /**
     * Toggle audio mute state
     */
    function toggleAudio() {
        if (!call) return;
        
        const audioState = call.participants().local.audio;
        console.log("🎤 Toggling audio:", audioState ? "OFF" : "ON");
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
        console.log("📹 Toggling video:", videoState ? "OFF" : "ON");
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
        console.log("🎉 JOINED MEETING EVENT:", event);
        updateCallStatus('Connected');
        participantCount++;
        console.log(`👥 Current participant count: ${participantCount}`);
        
        // Start recording when user joins
        console.log("📼 Starting recording after join");
        if (!recordingStarted) {
            startRecording();
        } else {
            console.log("⚠️ Recording already started previously");
        }
    }
    
    /**
     * Handle left meeting event
     */
    function handleLeftMeeting(event) {
        console.log("👋 LEFT MEETING EVENT:", event);
        updateCallStatus('Disconnected');
        stopCallTimer();
        
        // Stop recording and submit for transcription when user leaves
        if (isRecording) {
            console.log("🛑 Stopping recording after user left");
            stopRecording();
            
            // Create blob and submit for transcription
            console.log("🔄 Creating audio blob for upload after leaving");
            if (audioChunks.length > 0) {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                console.log("📤 Submitting audio for transcription after leaving");
                submitTranscription(audioBlob);
            } else {
                console.log("⚠️ No audio chunks available for transcription");
            }
        } else {
            console.log("⚠️ Recording was not active when call ended");
            
            // If we have audio chunks but recording flag is false, try to create a blob anyway
            if (audioChunks.length > 0) {
                console.log("🔄 Found audio chunks despite recording not being active, attempting to process");
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                submitTranscription(audioBlob);
            }
        }
    }
    
    /**
     * Handle participant joined event
     */
    function handleParticipantJoined(event) {
        console.log("👋 PARTICIPANT JOINED EVENT:", event);
        const participant = event.participant;
        participantCount++;
        console.log(`👥 Current participant count: ${participantCount}`);
        updateCallStatus('Connected with ' + (participant.user_name || 'another participant'));
    }
    
    /**
     * Handle participant left event
     */
    function handleParticipantLeft(event) {
        console.log("👋 PARTICIPANT LEFT EVENT:", event);
        participantCount--;
        console.log(`👥 Current participant count: ${participantCount}`);
        
        if (participantCount <= 1) {
            updateCallStatus('Waiting for others to join...');
        }
    }
    
    /**
     * Handle call errors
     */
    function handleCallError(error) {
        console.error("❌ CALL ERROR:", error);
        displayError('Call error: ' + error.errorMsg);
    }
    
    /**
     * Update call status UI
     */
    function updateCallStatus(status) {
        console.log("📊 Call status:", status);
        if (callStatusIndicator) {
            callStatusIndicator.textContent = status;
            
            // Update status colors
            callStatusIndicator.classList.remove('bg-green-600', 'bg-red-600', 'bg-yellow-500');
            if (status.includes('Connected')) {
                callStatusIndicator.classList.add('bg-green-600');
            } else if (status.includes('Disconnected') || status.includes('Error') || status.includes('Failed')) {
                callStatusIndicator.classList.add('bg-red-600');
            } else {
                callStatusIndicator.classList.add('bg-yellow-500');
            }
        }
    }
    
    /**
     * Display error message
     */
    function displayError(message) {
        console.error("❌ ERROR:", message);
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.classList.remove('hidden');
            errorDisplay.classList.remove('text-green-500');
            errorDisplay.classList.add('text-red-400');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorDisplay.classList.add('hidden');
            }, 5000);
        }
    }
    
    /**
     * Display success message
     */
    function displaySuccess(message) {
        console.log("✅ SUCCESS:", message);
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.classList.remove('hidden');
            errorDisplay.classList.remove('text-red-400');
            errorDisplay.classList.add('text-green-500');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorDisplay.classList.add('hidden');
            }, 5000);
        }
    }
    
    /**
     * Start call timer
     */
    function startCallTimer() {
        callStartTime = new Date();
        
        // Update timer display every second
        callTimer = setInterval(() => {
            if (!callDuration) return;
            
            const now = new Date();
            const diff = now - callStartTime;
            
            // Format time as HH:MM:SS
            const hours = Math.floor(diff / 3600000).toString().padStart(2, '0');
            const minutes = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
            const seconds = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');
            
            callDuration.textContent = `${hours}:${minutes}:${seconds}`;
        }, 1000);
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
     * Start audio recording
     */
    function startRecording() {
        if (isRecording) {
            console.log("⚠️ Recording already in progress, not starting again");
            return;
        }
        
        console.log("🎙️ Starting audio recording");
        
        // Reset audio chunks array only if we haven't started recording before
        if (!recordingStarted) {
            audioChunks = [];
        }
        
        try {
            // Access user's audio stream
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    localStream = stream;
                    
                    // Create MediaRecorder instance
                    audioRecorder = new MediaRecorder(stream);
                    
                    // Handle data available event
                    audioRecorder.ondataavailable = (event) => {
                        if (event.data && event.data.size > 0) {
                            console.log(`🎵 Audio data available: ${event.data.size} bytes`);
                            audioChunks.push(event.data);
                        }
                    };
                    
                    // Handle recording stop event
                    audioRecorder.onstop = () => {
                        console.log("🛑 Audio recorder stopped");
                        
                        // Stop all audio tracks
                        if (localStream) {
                            localStream.getAudioTracks().forEach(track => {
                                track.stop();
                                console.log("🔇 Audio track stopped");
                            });
                        }
                        
                        // Reset stream but keep audioChunks for transcription
                        localStream = null;
                    };
                    
                    // Start recording with 1 second time slices
                    audioRecorder.start(1000);
                    isRecording = true;
                    recordingStarted = true;
                    console.log("✅ Audio recording started");
                })
                .catch(error => {
                    console.error("❌ Failed to start recording:", error);
                    displayError("Failed to start recording: " + error.message);
                });
        } catch (error) {
            console.error("❌ Error during recording setup:", error);
            displayError("Recording error: " + error.message);
        }
    }
    
    /**
     * Stop audio recording
     */
    function stopRecording() {
        if (!isRecording || !audioRecorder) {
            console.log("⚠️ No active recording to stop");
            return;
        }
        
        console.log("🛑 Stopping audio recording");
        
        try {
            // Check recorder state
            if (audioRecorder && audioRecorder.state && audioRecorder.state !== 'inactive') {
                audioRecorder.stop();
                console.log("✅ AudioRecorder stopped");
            } else {
                console.log("⚠️ AudioRecorder was not in active state");
            }
            
            isRecording = false;
            
            // Don't reset recordingStarted flag here, we'll reset it when the call fully ends
            
            console.log("✅ Recording stopped successfully");
        } catch (error) {
            console.error("❌ Error stopping recording:", error);
            displayError("Error stopping recording: " + error.message);
            // Ensure flags are reset even if there's an error
            isRecording = false;
        }
    }
    
    /**
     * Submit audio for transcription
     */
    function submitTranscription(audioBlob) {
        if (transcriptionInProgress) {
            console.log("⚠️ Transcription already in progress");
            return;
        }
        
        if (!audioBlob || audioBlob.size === 0) {
            console.log("⚠️ No audio data to transcribe");
            return;
        }
        
        if (!appointmentId) {
            console.error("❌ Appointment ID not found");
            displayError("Appointment ID missing, cannot submit transcription");
            return;
        }
        
        console.log("🔄 Preparing to submit audio for transcription");
        const formData = new FormData();
        formData.append('audio_data', audioBlob, 'recording.mp3'); // Changed from 'audio_file' to 'audio_data' to match backend
        
        // Get CSRF token from the page
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            console.error("❌ CSRF token not found");
            displayError("Security token missing, cannot submit transcription");
            return;
        }
        
        // Show loading indicator
        if (loadingIndicator) loadingIndicator.classList.remove('hidden');
        
        transcriptionInProgress = true;
        
        console.log("📤 Sending audio for transcription...");
        console.log(`Submitting to endpoint: /transcription/create/${appointmentId}/`);
        
        // Send to server with appointment ID in the URL
        fetch(`/transcription/create/${appointmentId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                // Don't set Content-Type header with FormData - browser will set it with boundary
            },
            credentials: 'same-origin',
            mode: 'cors' // Allow CORS for cross-origin requests if needed
        })
        .then(response => {
            if (!response.ok) {
                // Try to extract more detailed error information from response
                return response.json().catch(() => {
                    // If response is not JSON, just throw with status
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }).then(errorData => {
                    // If we got JSON error data, include it in the error
                    throw new Error(`Server error (${response.status}): ${errorData.error || response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Transcription submitted successfully:", data);
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
            
            // Display success message
            displaySuccess("Transcription submitted successfully");
        })
        .catch(error => {
            console.error("❌ Error submitting transcription:", error);
            displayError("Failed to submit transcription: " + error.message);
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
        })
        .finally(() => {
            transcriptionInProgress = false;
        });
    }
    
    /**
     * Initialize chat functionality
     */
    function initializeChat() {
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');
        const chatMessages = document.getElementById('chat-messages');
        
        if (!chatForm || !chatInput || !chatMessages) {
            console.warn("⚠️ Chat elements not found in DOM");
            return;
        }
        
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message || !call) return;
            
            // Send chat message through Daily.co
            call.sendAppMessage({ message }, '*');
            
            // Add message to UI
            addChatMessage('You', message);
            
            // Clear input
            chatInput.value = '';
        });
        
        // Register chat message event handler on call object
        // Make the function available globally so it can be called from initializeCall
        window.setupChatMessageHandler = function() {
            if (!call) {
                console.warn("⚠️ Call object not available for chat setup");
                return;
            }
            
            console.log("🔄 Setting up chat message handler");
            call.on('app-message', function(event) {
                const { message } = event.data;
                const sender = event.fromId === call.participants().local.session_id 
                    ? 'You' 
                    : call.participants()[event.fromId]?.user_name || 'Other participant';
                
                console.log(`📩 Received chat message from ${sender}: ${message}`);
                addChatMessage(sender, message);
            });
        }
        
        // Set up handler when call is created
        // This will also be called from initializeCall
        if (call) {
            window.setupChatMessageHandler();
        }
        
        function addChatMessage(sender, message) {
            // Create message element
            const messageEl = document.createElement('div');
            messageEl.className = 'mb-3';
            messageEl.innerHTML = `
                <p class="text-sm font-medium text-gray-600">${sender}</p>
                <div class="bg-gray-100 rounded-lg p-3 mt-1">
                    <p class="text-gray-800">${message}</p>
                </div>
            `;
            
            // Add to chat container
            chatMessages.appendChild(messageEl);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}