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
            window.call = DailyIframe.createFrame({
                showLeaveButton: false,
                iframeStyle: {
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    border: 'none',
                    backgroundColor: 'transparent'
                },
                target: videoContainer
            });

            const call = window.call;

            console.log("✅ Daily call frame created:", call);

            // Set up event listeners
            call.on('joined-meeting', handleJoinedMeeting);
            call.on('left-meeting', handleLeftMeeting);
            call.on('participant-joined', handleParticipantJoined);
            call.on('participant-left', handleParticipantLeft);
            call.on('error', handleCallError);
            
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
            console.log("hehehe")
            console.log("typeof updateCallStatus:", typeof updateCallStatus);
            updateCallStatus('Joining call...');
            
            // If audio recording was previously enabled, set up recording
            console.log("🎤 Setting up audio recording before joining...");
            setupAudioRecording();
            
            // Join the meeting with token
            console.log("🔑 Joining with token...");
            await call.join({
                url: `https://chikitsa360.daily.co/${roomName}`,
                token: token
            });
            
            console.log("✅ Successfully joined the call");
            
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
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                console.log("📤 Submitting audio for transcription");
                submitTranscription(audioBlob);
            }
            
            // Leave the meeting
            console.log("👋 Leaving the Daily.co meeting");
            await call.leave();
            
            // Remove call frame
            if (call && call.iframe) {
                console.log("🧹 Removing call iframe from DOM");
                videoContainer.removeChild(call.iframe);
            }
            
            // Reset call object
            call = null;
            isCallActive = false;
            participantCount = 0;
            
            // Update UI
            console.log("🔄 Updating UI after call end");
            document.getElementById('call-controls').classList.add('hidden');
            endCallBtn.classList.add('hidden');
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
            const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
            console.log("📤 Submitting audio for transcription after leaving");
            submitTranscription(audioBlob);
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
        updateCallStatus('Other participant left the call');
        
        // If all participants have left except local user, we can handle ending/transitioning
        if (participantCount <= 1) {
            console.log("⚠️ All remote participants have left, preparing to end call");
        }
    }
    
    /**
     * Handle call errors
     */
    function handleCallError(event) {
        console.error("❌ CALL ERROR EVENT:", event);
        displayError('Call error: ' + event.errorMsg);
    }
    
    /**
     * Set up audio recording using MediaRecorder
     */
    function setupAudioRecording() {
        console.log("🎤 Setting up audio recording");
        
        // Check if MediaRecorder is supported
        if (!window.MediaRecorder) {
            console.error("❌ MediaRecorder not supported in this browser");
            displayError('MediaRecorder not supported in this browser');
            return;
        }
        
        // Reset recording state
        audioChunks = [];
        isRecording = false;
        recordingStarted = false;
        
        console.log("✅ Audio recording setup complete");
        
        // Enable transcribe button if recording is possible
        if (transcribeBtn) {
            transcribeBtn.disabled = false;
        }
    }
    
    /**
     * Start audio recording
     */
    function startRecording() {
        console.log("▶️ startRecording called");
        if (!call) {
            console.warn("⚠️ Call not initialized, cannot start recording");
            return;
        }
        
        if (isRecording) {
            console.warn("⚠️ Already recording, ignoring startRecording call");
            return;
        }
        
        try {
            console.log("🎤 Attempting to access media devices for recording");
            navigator.mediaDevices.getUserMedia({ audio: true, video: false })
                .then(stream => {
                    console.log("✅ Got media stream:", stream);
                    localStream = stream;
                    
                    console.log("📼 Creating MediaRecorder instance");
                    audioRecorder = new MediaRecorder(stream);
                    
                    audioRecorder.ondataavailable = (event) => {
                        console.log(`📊 Recording data available: ${event.data.size} bytes`);
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                            console.log(`📊 Total chunks: ${audioChunks.length}`);
                        }
                    };
                    
                    audioRecorder.onstop = () => {
                        console.log("⏹️ MediaRecorder stopped");
                        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        console.log(`📊 Final audio size: ${audioBlob.size} bytes`);
                        
                        if (transcribeBtn && transcribeBtn.dataset.autoTranscribe === 'true') {
                            console.log("🔄 Auto-transcribing recording");
                            submitTranscription(audioBlob);
                        }
                    };
                    
                    // Start recording
                    console.log("▶️ Starting MediaRecorder with 1 second chunks");
                    audioRecorder.start(1000);
                    isRecording = true;
                    recordingStarted = true;
                    
                    // Update UI
                    console.log("🔄 Updating UI for active recording");
                    if (transcribeBtn) {
                        transcribeBtn.textContent = 'Transcribe Call (Recording...)';
                        transcribeBtn.classList.add('bg-red-600');
                        transcribeBtn.classList.remove('bg-blue-600');
                    }
                })
                .catch(error => {
                    console.error("❌ Media access error:", error);
                    displayError('Error accessing microphone: ' + error.message);
                });
                
        } catch (error) {
            console.error("❌ Recording setup error:", error);
            displayError('Failed to start recording: ' + error.message);
        }
    }
    
    /**
     * Stop audio recording
     */
    function stopRecording() {
        console.log("⏹️ stopRecording called");
        
        if (!audioRecorder) {
            console.warn("⚠️ No audioRecorder instance found");
            return;
        }
        
        if (!isRecording) {
            console.warn("⚠️ Not currently recording");
            return;
        }
        
        try {
            console.log("⏹️ Stopping MediaRecorder");
            audioRecorder.stop();
            isRecording = false;
            
            // Stop all tracks in the stream
            if (localStream) {
                console.log("⏹️ Stopping all media tracks");
                localStream.getTracks().forEach(track => {
                    console.log(`⏹️ Stopping track: ${track.kind}`);
                    track.stop();
                });
            }
            
            // Update UI
            console.log("🔄 Updating UI after stopping recording");
            if (transcribeBtn) {
                transcribeBtn.textContent = 'Transcribe Call';
                transcribeBtn.classList.remove('bg-red-600');
                transcribeBtn.classList.add('bg-blue-600');
            }
            
        } catch (error) {
            console.error("❌ Error stopping recording:", error);
            displayError('Failed to stop recording: ' + error.message);
        }
    }
    
    /**
     * Submit audio for transcription
     */
    function submitTranscription(audioBlob) {
        console.log("📤 submitTranscription called with blob size:", audioBlob.size);
        
        if (transcriptionInProgress) {
            console.warn("⚠️ Transcription already in progress, ignoring request");
            return;
        }
        
        try {
            console.log("🔄 Starting transcription process");
            transcriptionInProgress = true;
            
            // Show loading indicator
            if (loadingIndicator) {
                console.log("🔄 Showing loading indicator");
                loadingIndicator.classList.remove('hidden');
            }
            
            // Create form data with audio blob
            console.log("🔄 Creating FormData with audio blob");
            const formData = new FormData();
            formData.append('audio_data', audioBlob, 'recording.mp3');
            
            // Get CSRF token
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            console.log("🔑 CSRF token retrieved:", csrftoken ? "Token present (hidden)" : "Token missing");
            
            // Submit transcription request
            console.log(`📤 Submitting transcription request for appointment ID: ${appointmentId}`);
            fetch(`/transcription/create/${appointmentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => {
                console.log("📥 Received response from server:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("📥 Parsed response data:", data);
                if (data.success) {
                    console.log(`✅ Transcription started with ID: ${data.transcription_id}`);
                    // Monitor transcription status
                    monitorTranscriptionStatus(data.transcription_id);
                } else {
                    throw new Error(data.error || 'Failed to start transcription');
                }
            })
            .catch(error => {
                console.error("❌ Transcription request error:", error);
                transcriptionInProgress = false;
                if (loadingIndicator) {
                    loadingIndicator.classList.add('hidden');
                }
                displayError('Transcription error: ' + error.message);
            });
            
        } catch (error) {
            console.error("❌ Error in transcription process:", error);
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
        console.log(`🔍 Starting status monitoring for transcription ID: ${transcriptionId}`);
        
        const statusCheckInterval = setInterval(() => {
            console.log(`🔄 Checking status of transcription ID: ${transcriptionId}`);
            
            fetch(`/transcription/status/${transcriptionId}/`, {
                method: 'GET'
            })
            .then(response => {
                console.log(`📥 Status check response code: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log(`📥 Status check data:`, data);
                
                if (data.completed) {
                    console.log(`✅ Transcription completed successfully`);
                    clearInterval(statusCheckInterval);
                    transcriptionInProgress = false;
                    
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('hidden');
                    }
                    
                    // Show success message
                    showNotification('Transcription completed and sent via email!', 'success');
                    
                    // Redirect to transcription detail page
                    console.log(`🔄 Redirecting to detail page: /transcription/detail/${transcriptionId}/`);
                    window.location.href = `/transcription/detail/${transcriptionId}/`;
                    
                } else if (data.failed) {
                    console.error(`❌ Transcription failed: ${data.error_message || 'Unknown error'}`);
                    clearInterval(statusCheckInterval);
                    transcriptionInProgress = false;
                    
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.classList.add('hidden');
                    }
                    
                    // Show error message
                    displayError('Transcription failed: ' + (data.error_message || 'Unknown error'));
                } else {
                    console.log(`⏳ Transcription still in progress`);
                }
            })
            .catch(error => {
                console.error(`❌ Error checking transcription status: ${error.message}`);
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
        console.log(`🔄 Call status: ${status}`);
        if (callStatusIndicator) {
            callStatusIndicator.textContent = status;
        }
    }
    
    /**
     * Display error message
     */
    function displayError(message) {
        console.error(`❌ ERROR: ${message}`);
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.classList.remove('hidden');
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorDisplay.classList.add('hidden');
            }, 5000);
        }
    }
    
    /**
     * Start call timer
     */
    function startCallTimer() {
        console.log(`⏱️ Starting call timer`);
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
        
        const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        callDuration.textContent = formattedTime;
    }
    
    /**
     * Stop call timer
     */
    function stopCallTimer() {
        console.log(`⏱️ Stopping call timer`);
        if (callTimer) {
            clearInterval(callTimer);
            callTimer = null;
        }
    }
    
    /**
     * Display a notification message
     */
    function showNotification(message, type = 'info') {
        console.log(`🔔 Notification (${type}): ${message}`);
        
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-md z-50 ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        console.log(`🔔 Notification created and added to DOM`);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('opacity-0', 'transition-opacity', 'duration-500');
            setTimeout(() => {
                document.body.removeChild(notification);
                console.log(`🔔 Notification removed from DOM`);
            }, 500);
        }, 5000);
    }
    
    // Initialize UI event listeners
    console.log(`🔄 Setting up UI event listeners`);
    
    if (joinBtn) {
        console.log(`🔄 Adding click listener to join button`);
        joinBtn.addEventListener('click', joinCall);
    }
    
    if (endCallBtn) {
        console.log(`🔄 Adding click listener to end call button`);
        endCallBtn.addEventListener('click', endCall);
    }
    
    if (muteAudioBtn) {
        console.log(`🔄 Adding click listener to mute audio button`);
        muteAudioBtn.addEventListener('click', toggleAudio);
    }
    
    if (muteVideoBtn) {
        console.log(`🔄 Adding click listener to mute video button`);
        muteVideoBtn.addEventListener('click', toggleVideo);
    }
    
    if (transcribeBtn) {
        console.log(`🔄 Adding click listener to transcribe button`);
        transcribeBtn.addEventListener('click', function() {
            console.log(`🎤 Transcribe button clicked`);
            if (isRecording) {
                console.log(`⏹️ Stopping current recording for transcription`);
                stopRecording();
                console.log(`🔄 Creating audio blob for transcription`);
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                console.log(`📤 Submitting audio for transcription manually`);
                submitTranscription(audioBlob);
            } else {
                console.log(`⚠️ No active recording to transcribe`);
                displayError('No recording available to transcribe');
            }
        });
    }
    
    // If we have all required elements, initialize the call
    if (videoContainer && roomName && token) {
        console.log("✅ All values present. Initializing call...");
        initializeCall();
    } else {
        console.log("❌ One or more required values are missing:");
        if (!videoContainer) console.log("  - Missing videoContainer");
        if (!roomName) console.log("  - Missing roomName");
        if (!token) console.log("  - Missing token");
    }

    // Handle window unload event
    window.addEventListener('beforeunload', function(e) {
        console.log(`🚪 Window unload event triggered`);
        if (isCallActive) {
            console.log(`📴 Ending call during page unload`);
            endCall();
        }
    });
}

// Initialize chat functionality
function initializeChat() {
    console.log("Initializing chat functionality");
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (!chatForm || !chatInput || !chatMessages) {
        console.error("One or more chat elements not found in DOM.");
        return;
    }
    
    // Add support for Daily.co's built-in chat
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        
        if (message && window.call) {
            // Send message using Daily.co's sendAppMessage
            window.call.sendAppMessage({ type: 'chat-message', message: message });
            
            // Display the message
            const messageEl = document.createElement('div');
            messageEl.className = 'flex justify-end mb-3';
            messageEl.innerHTML = `
                <div class="bg-blue-500 text-white rounded-lg py-2 px-3 max-w-xs">
                    <p class="text-sm">${message}</p>
                    <p class="text-xs text-blue-200 text-right mt-1">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                </div>
            `;
            chatMessages.appendChild(messageEl);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Clear input
            chatInput.value = '';
        }
    });
    
    // Listen for incoming chat messages
    if (window.call) {
        window.call.on('app-message', function(event) {
            if (event.data.type === 'chat-message') {
                const message = event.data.message;
                const messageEl = document.createElement('div');
                messageEl.className = 'flex justify-start mb-3';
                messageEl.innerHTML = `
                    <div class="bg-gray-200 rounded-lg py-2 px-3 max-w-xs">
                        <p class="text-xs text-gray-600 mb-1">${event.fromId}</p>
                        <p class="text-sm">${message}</p>
                        <p class="text-xs text-gray-500 text-right mt-1">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                    </div>
                `;
                chatMessages.appendChild(messageEl);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });
    }
}

// Single DOMContentLoaded event listener that runs after all script is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ DOMContentLoaded event triggered");
    initializeVideoConsultation();
});