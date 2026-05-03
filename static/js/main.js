document.addEventListener('DOMContentLoaded', () => {
    
    // --- Theme Toggle Logic ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check local storage for theme preference
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeToggleBtn.innerHTML = '<i class="ph ph-sun"></i>';
    }

    themeToggleBtn.addEventListener('click', () => {
        if (body.classList.contains('light-theme')) {
            body.classList.replace('light-theme', 'dark-theme');
            localStorage.setItem('theme', 'dark');
            themeToggleBtn.innerHTML = '<i class="ph ph-sun"></i>';
        } else {
            body.classList.replace('dark-theme', 'light-theme');
            localStorage.setItem('theme', 'light');
            themeToggleBtn.innerHTML = '<i class="ph ph-moon"></i>';
        }
    });

    // --- Chat Interface Logic ---
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatHistory = document.getElementById('chat-history');
    const typingIndicator = document.getElementById('typing-indicator');
    const languageSelect = document.getElementById('language-select');
    const personaSelect = document.getElementById('persona-select');
    const micBtn = document.getElementById('mic-btn');

    // Speech Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
            userInput.placeholder = "Listening...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            // Optionally auto-submit
            // chatForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            isRecording = false;
            micBtn.classList.remove('recording');
            userInput.placeholder = "Type your question here...";
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
            userInput.placeholder = "Type your question here...";
        };

        micBtn.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                // Set recognition language based on dropdown
                const langMap = {
                    'English': 'en-US',
                    'Spanish': 'es-ES',
                    'Hindi': 'hi-IN',
                    'French': 'fr-FR'
                };
                recognition.lang = langMap[languageSelect.value] || 'en-US';
                recognition.start();
            }
        });
    } else {
        micBtn.style.display = 'none'; // Hide if not supported
    }

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const avatarIcon = isUser ? '<i class="ph ph-user"></i>' : '<i class="ph ph-robot"></i>';
        
        // Convert simple markdown (bold) to HTML for bot messages
        let formattedMessage = message;
        if (!isUser) {
            formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // Convert newlines to breaks
            formattedMessage = formattedMessage.replace(/\n/g, '<br>');
        }

        messageDiv.innerHTML = `
            <div class="avatar">${avatarIcon}</div>
            <div class="message-content">
                <p>${formattedMessage}</p>
            </div>
        `;
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;

        // Display user message
        addMessage(message, true);
        userInput.value = '';
        
        // Show typing indicator
        typingIndicator.classList.remove('hidden');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    language: languageSelect.value,
                    context: personaSelect.value
                })
            });

            const data = await response.json();
            
            // Hide typing indicator
            typingIndicator.classList.add('hidden');
            
            if (response.ok) {
                addMessage(data.response);
            } else {
                addMessage("Error: " + (data.error || "Could not reach the server."));
            }
        } catch (error) {
            console.error("Chat Error:", error);
            typingIndicator.classList.add('hidden');
            addMessage("Sorry, there was a network error. Please try again.");
        }
    });

    // --- Google Services Integration ---

    // 1. Google Calendar Links dynamically generated
    const calendarBtns = document.querySelectorAll('.calendar-btn');
    calendarBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const eventName = encodeURIComponent(btn.getAttribute('data-event'));
            const dates = btn.getAttribute('data-date'); // Format: YYYYMMDDTHHMMSSZ/YYYYMMDDTHHMMSSZ
            const details = encodeURIComponent("Election timeline event generated by Smart Election Navigator.");
            
            // Google Calendar Event URL format
            const googleCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${eventName}&dates=${dates}&details=${details}`;
            
            // Open in new tab
            window.open(googleCalUrl, '_blank');
        });
    });

    // 2. Google Maps — India Polling Booth Locator
    const searchMapBtn = document.getElementById('search-map-btn');
    const zipInput = document.getElementById('zip-input');
    const mapContainer = document.getElementById('map-container');
    const openMapBtn = document.getElementById('open-map-btn');

    function loadIndiaMap(pinCode) {
        const mapsKey = document.querySelector('.search-box').getAttribute('data-maps-key');
        const searchQuery = encodeURIComponent(`polling booth near PIN ${pinCode}, India`);
        
        let embedSrc;
        if (mapsKey && mapsKey !== "" && mapsKey !== "None") {
            // Official Google Maps Embed API (Requires Key)
            embedSrc = `https://www.google.com/maps/embed/v1/search?key=${mapsKey}&q=${searchQuery}&zoom=14`;
        } else {
            // Standard Google Maps Embed (No Key - limited functionality but works for demo)
            embedSrc = `https://maps.google.com/maps?q=${searchQuery}&output=embed&z=14`;
        }

        const searchUrl = `https://www.google.com/maps/search/${searchQuery}`;

        mapContainer.innerHTML = `
            <iframe
                class="map-iframe"
                src="${embedSrc}"
                title="Polling booths near PIN ${pinCode}, India"
                allowfullscreen
                loading="lazy"
                referrerpolicy="no-referrer-when-downgrade"
                onerror="this.style.display='none'; document.getElementById('map-error').style.display='block';">
            </iframe>
            <div id="map-error" style="display:none; padding: 2rem; text-align: center;">
                <i class="ph ph-warning-circle" style="font-size: 3rem; color: var(--primary-color);"></i>
                <p>Could not load interactive map. Please use the direct link below.</p>
            </div>
        `;

        // Update the external link button
        if (openMapBtn) {
            openMapBtn.href = searchUrl;
            openMapBtn.style.display = 'inline-flex';
        }
    }

    searchMapBtn.addEventListener('click', () => {
        const query = zipInput.value.trim();
        if (!query) {
            zipInput.style.borderColor = '#ef4444';
            return;
        }
        const pinRegex = /^[1-9][0-9]{5}$/;
        if (!pinRegex.test(query)) {
            zipInput.style.borderColor = '#ef4444';
            mapContainer.innerHTML = `
                <div class="map-placeholder">
                    <i class="ph ph-warning" style="color:#ef4444;font-size:2.5rem;"></i>
                    <p style="color:#ef4444;margin-top:0.5rem;">Please enter a valid 6-digit Indian PIN code (e.g. 110001).</p>
                </div>
            `;
            return;
        }
        zipInput.style.borderColor = '';

        // Show loading state
        mapContainer.innerHTML = `
            <div class="map-placeholder">
                <i class="ph ph-circle-notch" style="font-size:2.5rem;animation:spin 1s linear infinite;"></i>
                <p style="margin-top:0.5rem;">Loading map...</p>
            </div>
        `;
        // Small delay to allow loading state to render
        setTimeout(() => loadIndiaMap(query), 100);
    });

    zipInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchMapBtn.click();
    });
    zipInput.addEventListener('input', () => {
        zipInput.style.borderColor = '';
    });

    // --- Interactive Checklist Logic ---
    const checkIds = ['check-registered', 'check-id', 'check-location', 'check-voted'];
    const resetChecklistBtn = document.getElementById('reset-checklist-btn');

    // Load saved states
    checkIds.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            checkbox.checked = localStorage.getItem(id) === 'true';
            checkbox.addEventListener('change', (e) => {
                localStorage.setItem(id, e.target.checked);
            });
        }
    });

    // Reset checklist
    if (resetChecklistBtn) {
        resetChecklistBtn.addEventListener('click', () => {
            checkIds.forEach(id => {
                const checkbox = document.getElementById(id);
                if (checkbox) {
                    checkbox.checked = false;
                    localStorage.removeItem(id);
                }
            });
        });
    }
});
