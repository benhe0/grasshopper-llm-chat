<template>
  <div class="chat-input-container">
    <label class="switch">
      <input
        type="checkbox"
        :checked="isVoiceInput"
        @change="updateIsVoiceInput($event.target.checked)"
      />
      <span class="slider">{{ isVoiceInput ? "Voice" : "Text" }}</span>
    </label>
    <div class="chat-input">
      <div
        v-if="isVoiceInput"
        class="voice-input"
        :class="{ recording: isRecording, transcribing: isTranscribing }"
        @click="startVoiceRecognition"
      >
        <span v-if="isTranscribing">Transcribing...</span>
        <span v-else-if="isRecording">Tap to stop</span>
        <span v-else>Tap to speak</span>
      </div>
      <div v-else>
        <input
          :value="inputMessage"
          @input="updateInputMessage($event.target.value)"
          placeholder="Type your prompt here..."
          @keyup.enter="sendMessage"
        />
        <button @click="sendMessage">Send</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";

const props = defineProps({
  inputMessage: String,
  isVoiceInput: Boolean,
  isRecording: Boolean,
  isTranscribing: Boolean,
});

const emit = defineEmits([
  "update:inputMessage",
  "update:isVoiceInput",
  "send-message",
  "start-voice-recognition",
]);

const updateInputMessage = (value) => {
  emit("update:inputMessage", value);
};

const updateIsVoiceInput = (value) => {
  emit("update:isVoiceInput", value);
};

const sendMessage = () => {
  emit("send-message");
};

const startVoiceRecognition = () => {
  emit("start-voice-recognition");
};
</script>

<style scoped>
.chat-input-container {
  padding-top: 3%;
}

.switch {
  position: relative;
  display: inline-block;
  width: 120px;
  height: 34px;
  margin: 10px;
  right: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #007bff;
}

input:checked + .slider:before {
  transform: translateX(86px);
}

.chat-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.chat-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  margin-right: 10px;
}

.chat-input button {
  background-color: #007bff;
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  padding: 8px 16px;
}

.chat-input button:hover {
  background-color: #0056b3;
}

.voice-input {
  flex: 1;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.voice-input.recording {
  background-color: #f26262;
}

.voice-input.transcribing {
  background-color: #f2c862;
  cursor: wait;
}
</style>
