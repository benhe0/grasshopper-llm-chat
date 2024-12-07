<template>
  <div :class="['chat-container', { collapsed: isCollapsed }, theme]">
    <div class="chat-header">
      <CollapseButton
        :isCollapsed="isCollapsed"
        @toggle-collapse="toggleCollapse"
      />
      <div class="header-inputs">
        <input
          type="text"
          class="username-input"
          v-model="username"
          @blur="saveUsername"
          @keyup.enter="saveUsername"
          placeholder="Your name..."
        />
        <div class="websocket-row">
          <input
            type="text"
            class="websocket-input"
            v-model="websocketUrl"
            @keyup.enter="saveWebsocketUrl"
            placeholder="ws://localhost:5001"
          />
          <button
            class="connect-btn"
            :class="{ connected: isConnected }"
            @click="saveWebsocketUrl"
            :title="isConnected ? 'Connected' : 'Click to connect'"
          >
            {{ isConnected ? '●' : '○' }}
          </button>
        </div>
      </div>
    </div>
    <ChatMessages :messages="displayedMessages" :isThinking="isThinking" />
    <ChatInputContainer
      v-model:inputMessage="inputMessage"
      v-model:isVoiceInput="isVoiceInput"
      :isRecording="isRecording"
      :isTranscribing="isTranscribing"
      @send-message="handleNewMessage"
      @start-voice-recognition="startVoiceRecognition"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from "vue";
import { useStore } from "vuex";
import CollapseButton from "./CollapseButton.vue";
import ChatMessages from "./ChatMessages.vue";
import ChatInputContainer from "./ChatInputContainer.vue";
import { connectionState, reconnectSocket } from "../services/socket";

const store = useStore();
const inputMessage = ref("");
const isVoiceInput = ref(false);
const isRecording = ref(false);
const isTranscribing = ref(false);
const isCollapsed = ref(false);
const username = ref(store.state.username);
const websocketUrl = ref(store.state.websocketUrl);
const allMessages = computed(() => store.state.allMessages);
const isThinking = computed(() => store.state.isThinking);
const theme = computed(() => store.state.theme);
const isConnected = computed(() => connectionState.connected);

const saveUsername = () => {
  store.commit("setUsername", username.value);
};

const saveWebsocketUrl = () => {
  store.commit("setWebsocketUrl", websocketUrl.value);
  reconnectSocket(websocketUrl.value);
};

const FLASK_HUB_URL = computed(() => store.state.websocketUrl);

// Audio recording state
let mediaRecorder = null;
let audioChunks = [];

const displayedMessages = computed(() => {
  return isCollapsed.value ? allMessages.value.slice(-2) : allMessages.value;
});

const handleNewMessage = async () => {
  if (inputMessage.value.trim()) {
    // Don't add message locally - server will broadcast it back to all clients
    // including this one (with from_self: true)
    store.commit("setPrompt", inputMessage.value);
    inputMessage.value = "";
    store.commit("setThinking", true);
    // Response handled via WebSocket events
  }
};

const startVoiceRecognition = async () => {
  if (isRecording.value) {
    // Stop recording
    stopRecording();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus",
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Stop all tracks to release microphone
      stream.getTracks().forEach((track) => track.stop());

      if (audioChunks.length === 0) {
        console.log("No audio recorded");
        return;
      }

      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      console.log("Audio recorded, size:", audioBlob.size);

      // Send to Whisper for transcription
      await transcribeAudio(audioBlob);
    };

    mediaRecorder.start();
    isRecording.value = true;
    console.log("Recording started");
  } catch (error) {
    console.error("Error accessing microphone:", error);
    alert(
      "Could not access microphone. Please ensure microphone permissions are granted."
    );
  }
};

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    isRecording.value = false;
    console.log("Recording stopped");
  }
};

const transcribeAudio = async (audioBlob) => {
  isTranscribing.value = true;
  console.log("Sending audio to Whisper for transcription...");

  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    const response = await fetch(`${FLASK_HUB_URL.value}/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Transcription failed");
    }

    const result = await response.json();
    console.log("Transcription result:", result);

    if (result.text) {
      inputMessage.value = result.text;
      handleNewMessage();
    }
  } catch (error) {
    console.error("Transcription error:", error);
    alert("Transcription failed: " + error.message);
  } finally {
    isTranscribing.value = false;
  }
};

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};

// Cleanup on component unmount
onBeforeUnmount(() => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
});
</script>

<style scoped>
.chat-container {
  width: 20%;
  height: 90%;
  position: fixed;
  bottom: 10px;
  right: 10px;
  z-index: 1000;
  border-radius: 10px;
  backdrop-filter: blur(5px);
  background-color: rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(0, 0, 0, 0.2);
  transition: height 0.3s ease;
}

.chat-header {
  display: flex;
  align-items: flex-start;
  padding: 8px;
  gap: 8px;
  border-bottom: 1px solid rgba(128, 128, 128, 0.2);
}

.header-inputs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid rgba(128, 128, 128, 0.3);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.username-input:focus {
  border-color: rgba(0, 123, 255, 0.6);
}

.username-input::placeholder {
  color: rgba(128, 128, 128, 0.7);
}

.websocket-row {
  display: flex;
  gap: 4px;
  align-items: center;
}

.websocket-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid rgba(128, 128, 128, 0.3);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
  font-size: 0.75rem;
  outline: none;
  transition: border-color 0.2s;
}

.websocket-input:focus {
  border-color: rgba(0, 123, 255, 0.6);
}

.websocket-input::placeholder {
  color: rgba(128, 128, 128, 0.7);
}

.connect-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 10px;
  background: rgba(128, 128, 128, 0.3);
  color: #ff6b6b;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.connect-btn.connected {
  color: #51cf66;
}

.connect-btn:hover {
  background: rgba(128, 128, 128, 0.5);
}

.chat-container.collapsed {
  height: 150px;
}

/* Dark Theme Styles */
.dark {
  background-color: rgba(40, 40, 40, 0.4);
  color: white;
}

/* Light Theme Styles */
.light {
  background-color: rgba(255, 255, 255, 0.4);
  color: black;
}

.theme-toggle-button {
  margin: 10px;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.theme-toggle-button:hover {
  background-color: #0056b3;
}

/* Mobile Styles */
@media (max-width: 768px) {
  .chat-container {
    width: 40%;
    height: 60%;
    bottom: 5px;
    right: 5px;
  }
}

@media (max-width: 480px) {
  .chat-container {
    width: 90%;
    height: 50%;
    bottom: 5px;
    right: 5px;
  }

  .chat-container.collapsed {
    height: 120px;
  }

  .theme-toggle-button {
    padding: 5px;
    font-size: 14px;
  }
}
</style>
