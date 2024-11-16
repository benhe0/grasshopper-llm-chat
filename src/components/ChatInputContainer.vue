<template>
  <div class="chat-input-container">
    <label class="switch">
      <input type="checkbox" :checked="isVoiceInput" @change="$emit('update:isVoiceInput', $event.target.checked)" />
      <span class="slider-toggle">{{ isVoiceInput ? "Voice" : "Text" }}</span>
    </label>
    <div class="chat-input">
      <div v-if="isVoiceInput" class="voice-input" :class="{ recording: isRecording }" @click="$emit('start-voice-recognition')">
        <span v-if="isRecording">Tap to stop</span>
        <span v-else>Tap to speak</span>
      </div>
      <div v-else class="text-input">
        <input
          :value="inputMessage"
          @input="$emit('update:inputMessage', $event.target.value)"
          placeholder="Type your message..."
          @keyup.enter="$emit('send-message')"
        />
        <button @click="$emit('send-message')">Send</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  inputMessage: String,
  isVoiceInput: Boolean,
  isRecording: Boolean,
});
defineEmits(["update:inputMessage", "update:isVoiceInput", "send-message", "start-voice-recognition"]);
</script>

<style scoped>
.chat-input-container {
  padding: 10px;
}

.switch {
  display: inline-block;
  margin-bottom: 10px;
}

.switch input {
  display: none;
}

.slider-toggle {
  display: inline-block;
  padding: 5px 15px;
  background: #ccc;
  border-radius: 20px;
  cursor: pointer;
}

input:checked + .slider-toggle {
  background: #007bff;
  color: white;
}

.chat-input {
  display: flex;
}

.text-input {
  display: flex;
  flex: 1;
  gap: 8px;
}

.text-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
}

.text-input button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
}

.voice-input {
  flex: 1;
  padding: 15px;
  text-align: center;
  background: #f0f0f0;
  border-radius: 20px;
  cursor: pointer;
}

.voice-input.recording {
  background: #ff6b6b;
  color: white;
}
</style>
