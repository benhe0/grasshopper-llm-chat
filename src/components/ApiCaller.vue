<template>
  <!-- Logic-only component -->
</template>

<script setup>
import { watch, computed, onMounted, onUnmounted } from "vue";
import { useStore } from "vuex";
import { initSocket, getSocket } from "../services/socket";

const store = useStore();
const parameters = computed(() => store.state.parameters);
const prompt = computed(() => store.state.prompt);

onMounted(() => {
  const socket = initSocket();

  socket.on('params_init', (data) => {
    console.log('Received initial params:', data);
    if (data.params && data.params.length > 0) {
      store.commit('setParameters', data.params);
    }
  });

  socket.on('params_sync', (data) => {
    console.log('Params sync:', data);
    if (data.params) {
      store.commit('setParameters', data.params);
    }
  });

  socket.on('geometry_result', (data) => {
    console.log('Geometry received');
    if (data.geometry) {
      store.commit('setReceivedMeshData', data.geometry);
    }
    store.commit('setThinking', false);
  });
});

// Watch for prompt changes and send to server
watch(
  () => prompt.value,
  (newPrompt) => {
    if (newPrompt && newPrompt.trim()) {
      console.log('Sending prompt:', newPrompt);
      // TODO: send via socket
    }
  }
);
</script>
