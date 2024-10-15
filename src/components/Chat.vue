<template>
  <div class="chat-container">
    <div class="chat-header">
      <span>Chat</span>
    </div>
    <div class="chat-messages">
      <p v-if="messages.length === 0">No messages yet</p>
      <div v-for="(msg, i) in messages" :key="i" class="message">
        {{ msg.text }}
      </div>
    </div>
    <div class="chat-input">
      <input v-model="inputMessage" placeholder="Type a message..." @keyup.enter="sendMessage" />
      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useStore } from "vuex";

const store = useStore();
const inputMessage = ref("");
const messages = computed(() => store.state.chatMessages);

const sendMessage = () => {
  if (inputMessage.value.trim()) {
    store.commit("addMessage", { text: inputMessage.value, type: "user" });
    store.commit("setPrompt", inputMessage.value);
    inputMessage.value = "";
  }
};
</script>

<style scoped>
.chat-container {
  width: 300px;
  height: 100%;
  background: #e8e8e8;
  display: flex;
  flex-direction: column;
  position: fixed;
  right: 0;
  top: 0;
}

.chat-header {
  padding: 10px;
  font-weight: bold;
  border-bottom: 1px solid #ccc;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin: 5px 0;
  padding: 8px;
  background: white;
  border-radius: 8px;
}

.chat-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #ccc;
}

.chat-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-right: 5px;
}

.chat-input button {
  padding: 8px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
