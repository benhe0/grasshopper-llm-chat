<template>
  <div class="chat-container">
    <div class="chat-header">Chat</div>
    <ChatMessages :messages="messages" :isThinking="isThinking" />
    <ChatInputContainer
      v-model:inputMessage="inputMessage"
      @send-message="handleSend"
    />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useStore } from "vuex";
import ChatMessages from "./ChatMessages.vue";
import ChatInputContainer from "./ChatInputContainer.vue";

const store = useStore();
const inputMessage = ref("");
const messages = computed(() => store.state.chatMessages);
const isThinking = computed(() => store.state.isThinking);

const handleSend = () => {
  if (inputMessage.value.trim()) {
    store.commit("addMessage", { text: inputMessage.value, type: "user" });
    store.commit("setPrompt", inputMessage.value);
    store.commit("setThinking", true);
    inputMessage.value = "";
  }
};
</script>

<style scoped>
.chat-container {
  width: 300px;
  height: 90%;
  background: rgba(240, 240, 240, 0.95);
  display: flex;
  flex-direction: column;
  position: fixed;
  right: 10px;
  bottom: 10px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.chat-header {
  padding: 15px;
  font-weight: bold;
  border-bottom: 1px solid #ddd;
}
</style>
