<template>
  <div class="chat-input-container">
    <input
      :value="inputMessage"
      @input="$emit('update:inputMessage', $event.target.value)"
      placeholder="Type your message..."
      @keyup.enter="$emit('send-message')"
    />
    <button @click="$emit('send-message')">Send</button>
  </div>
</template>

<script setup>
defineProps({ inputMessage: String });
defineEmits(["update:inputMessage", "send-message"]);
</script>

<style scoped>
.chat-input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #ccc;
  gap: 8px;
}

.chat-input-container input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
}

.chat-input-container button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
}

.chat-input-container button:hover {
  background: #0056b3;
}
</style>
