<template>
  <div class="chat-messages-wrapper">
    <div class="chat-messages">
      <div
        class="chat-message-container"
        v-for="(message, index) in messages"
        :key="index"
        :class="message.type"
      >
        <span class="message-sender">{{ message.sender }}</span>
        <p class="chat-message" :class="message.type">
          {{ message.text }}
        </p>
      </div>
      <div v-if="isThinking" class="thinking-animation"></div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from "vue";

const props = defineProps({
  messages: Array,
  isThinking: Boolean,
});
</script>

<style scoped>
.chat-messages-wrapper {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.chat-messages {
  flex-grow: 1;
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.chat-message-container {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
  max-width: 90%;
}

.chat-message-container.user {
  align-self: flex-end;
  align-items: flex-end;
}

.chat-message-container.response {
  align-self: flex-start;
  align-items: flex-start;
}

.message-sender {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-bottom: 2px;
  padding: 0 8px;
}

.chat-message {
  padding: 8px 12px;
  border-radius: 20px;
  margin: 0;
}

.chat-message.user {
  background-color: rgba(0, 123, 255, 0.8);
  color: white;
}

.chat-message.response {
  background-color: rgba(100, 100, 100, 0.8);
  color: white;
}

/* Dark Theme Styles */
.dark .chat-message.user {
  background-color: rgba(0, 123, 255, 0.8);
}

.dark .chat-message.response {
  background-color: rgba(100, 100, 100, 0.8);
}

/* Light Theme Styles */
.light .chat-message.user {
  background-color: rgba(0, 123, 255, 0.6);
}

.light .chat-message.response {
  background-color: rgba(220, 220, 220, 0.9);
  color: black;
}

.thinking-animation {
  width: 20px;
  height: 20px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  align-self: center;
  margin-top: 10px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
