<template>
  <!-- Logic-only component -->
</template>

<script setup>
import { watch, computed, onMounted } from "vue";
import { useStore } from "vuex";
import { initSocket, getSocket, emitParamsUpdate } from "../services/socket";

const store = useStore();
const parameters = computed(() => store.state.parameters);
const prompt = computed(() => store.state.prompt);

let isSyncingFromServer = false;

onMounted(() => {
  const socket = initSocket();

  socket.on('params_init', (data) => {
    if (data.params?.length > 0) {
      isSyncingFromServer = true;
      store.commit('setParameters', data.params);
      setTimeout(() => { isSyncingFromServer = false; }, 100);
    }
  });

  socket.on('params_sync', (data) => {
    if (data.params) {
      isSyncingFromServer = true;
      store.commit('setParameters', data.params);
      setTimeout(() => { isSyncingFromServer = false; }, 100);
    }
  });

  socket.on('geometry_result', (data) => {
    if (data.geometry) {
      store.commit('setReceivedMeshData', data.geometry);
    }
    store.commit('setThinking', false);
  });
});

// Send param updates to server when local sliders change
watch(
  () => parameters.value.inputs,
  (newInputs) => {
    if (isSyncingFromServer) return;
    if (newInputs.length > 0) {
      const params = {};
      newInputs.forEach(p => { params[p.name] = p.value; });
      console.log('Sending params:', params);
      emitParamsUpdate(params);
    }
  },
  { deep: true }
);
</script>
