<template>
  <div class="chat-messages">
    <div
      v-for="(message, index) in messages"
      :key="index"
      class="chat-message"
      :class="message.type"
    >
      <p>{{ message.text }}</p>
    </div>
    <div v-if="isThinking" class="thinking">...</div>
  </div>
</template>

<script setup>
defineProps({
  messages: Array,
  isThinking: Boolean,
});
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.chat-message {
  margin: 8px 0;
  padding: 10px;
  border-radius: 10px;
  max-width: 80%;
}

.chat-message.user {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.chat-message.response {
  background: #e0e0e0;
  color: black;
}

.chat-message p {
  margin: 0;
}

.thinking {
  padding: 10px;
  color: #666;
}
</style>
