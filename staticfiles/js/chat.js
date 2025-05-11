/**
 * Chat functionality for Chikitsa360
 * Implements WebSocket-based real-time chat
 */

// Initialize variables
let chatSocket = null;
let reconnectInterval = null;
let messageContainer = null;
let messageForm = null;
let messageInput = null;
let messageStatus = null;
let lastMessageId = 0;
let isTyping = false;
let typingTimeout = null;
let loadingHistory = false;
let appointmentId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    messageContainer = document.getElementById('message-container');
    messageForm = document.getElementById('message-form');
    messageInput = document.getElementById('message-input');
    messageStatus = document.getElementById('message-status');
    
    // Get appointment ID from the URL
    const pathParts = window.location.pathname.split('/');
    const chatPathIndex = pathParts.indexOf('chat');
    
    if (chatPathIndex !== -1 && chatPathIndex + 1 < pathParts.length) {
        appointmentId = pathParts[chatPathIndex + 2]; // +2 because of path pattern /chat/appointment/{uuid}/
    }
    
    // Only initialize if we're on a chat page
    if (messageContainer && messageForm && messageInput && appointmentId) {
        initializeChat();
    }
    
    /**
     * Initialize chat functionality
     */
    function initializeChat() {
        // Load chat history
        loadChatHistory();
        
        // Connect websocket
        connectWebSocket();
        
        // Set up form submission
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
        
        // Set up input events
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Implement typing indicator
        messageInput.addEventListener('input', function() {
            if (!isTyping) {
                isTyping = true;
                // In a real implementation, we would send a "typing" message to the server
            }
            
            // Reset typing timeout
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                isTyping = false;
                // In a real implementation, we would send a "stopped typing" message to the server
            }, 1000);
        });
        
        // Handle window unload
        window.addEventListener('beforeunload', function() {
            disconnectWebSocket();
        });
    }
    
    /**
     * Connect to WebSocket
     */
    function connectWebSocket() {
        // Close existing connection if any
        if (chatSocket) {
            chatSocket.close();
        }
        
        // Determine WebSocket protocol (wss for HTTPS, ws for HTTP)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${wsProtocol}${window.location.host}/ws/chat/${appointmentId}/`;
        
        // Create new WebSocket connection
        chatSocket = new WebSocket(wsUrl);
        
        // Set up event handlers
        chatSocket.onopen = function(e) {
            console.log('WebSocket connection established');
            updateStatus('Connected');
            
            // Clear reconnect interval if it exists
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        };
        
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            displayMessage(data);
        };
        
        chatSocket.onclose = function(e) {
            console.log('WebSocket connection closed');
            updateStatus('Disconnected. Reconnecting...');
            
            // Set up reconnect interval
            if (!reconnectInterval) {
                reconnectInterval = setInterval(function() {
                    connectWebSocket();
                }, 5000);
            }
        };
        
        chatSocket.onerror = function(e) {
            console.error('WebSocket error:', e);
            updateStatus('Connection error');
        };
    }
    
    /**
     * Disconnect WebSocket
     */
    function disconnectWebSocket() {
        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;
        }
        
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    }
    
    /**
     * Load chat history via AJAX
     */
    function loadChatHistory() {
        if (loadingHistory) return;
        
        loadingHistory = true;
        updateStatus('Loading message history...');
        
        // Get CSRF token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Make AJAX request
        fetch(`/chat/appointment/${appointmentId}/messages/?last_message_id=${lastMessageId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                // Display messages
                data.messages.forEach(message => {
                    displayMessage(message, true);
                });
                
                // Update last message ID
                const lastMessage = data.messages[data.messages.length - 1];
                if (lastMessage && lastMessage.id > lastMessageId) {
                    lastMessageId = lastMessage.id;
                }
                
                // Scroll to bottom
                scrollToBottom();
            }
            
            loadingHistory = false;
            updateStatus('Connected');
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            loadingHistory = false;
            updateStatus('Failed to load message history');
        });
    }
    
    /**
     * Send a message via WebSocket
     */
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (message && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'message': message
            }));
            
            // Clear input
            messageInput.value = '';
            
            // Reset typing indicator
            clearTimeout(typingTimeout);
            isTyping = false;
        }
    }
    
    /**
     * Display a received message
     */
    function displayMessage(data, isHistory = false) {
        // Ignore if we've already displayed this message
        if (document.getElementById(`message-${data.message_id}`)) {
            return;
        }
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.id = `message-${data.message_id}`;
        messageEl.className = `flex mb-4 ${data.is_self ? 'justify-end' : 'justify-start'}`;
        
        // Create message bubble
        const bubbleEl = document.createElement('div');
        bubbleEl.className = `message-bubble ${data.is_self ? 'sent' : 'received'} max-w-xs md:max-w-md`;
        
        // Create name element (only for received messages)
        if (!data.is_self) {
            const nameEl = document.createElement('div');
            nameEl.className = 'text-xs text-gray-500 mb-1';
            nameEl.textContent = data.sender_name;
            bubbleEl.appendChild(nameEl);
        }
        
        // Create content element
        const contentEl = document.createElement('div');
        contentEl.className = 'whitespace-pre-wrap break-words';
        contentEl.textContent = data.message;
        bubbleEl.appendChild(contentEl);
        
        // Create timestamp element
        const timeEl = document.createElement('div');
        timeEl.className = `text-xs ${data.is_self ? 'text-gray-300' : 'text-gray-500'} mt-1 text-right`;
        timeEl.textContent = data.timestamp;
        bubbleEl.appendChild(timeEl);
        
        // Assemble message
        messageEl.appendChild(bubbleEl);
        
        // Add to container
        messageContainer.appendChild(messageEl);
        
        // Update last message ID
        if (data.message_id > lastMessageId) {
            lastMessageId = data.message_id;
        }
        
        // Scroll to bottom if not viewing history
        if (!isHistory) {
            scrollToBottom();
        }
    }
    
    /**
     * Scroll to the bottom of the message container
     */
    function scrollToBottom() {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    /**
     * Update connection status display
     */
    function updateStatus(status) {
        if (messageStatus) {
            messageStatus.textContent = status;
            
            // Set appropriate status colors
            messageStatus.className = 'text-sm';
            
            if (status.includes('Connected')) {
                messageStatus.classList.add('text-green-600');
            } else if (status.includes('Disconnected') || status.includes('error')) {
                messageStatus.classList.add('text-red-600');
            } else {
                messageStatus.classList.add('text-gray-600');
            }
        }
    }
});
