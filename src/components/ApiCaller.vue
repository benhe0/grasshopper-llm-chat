<template>
  <!-- Logic-only component -->
</template>

<script setup>
import { watch, computed, onMounted } from "vue";
import { useStore } from "vuex";
import { initSocket, emitParamsUpdate, emitChatRequest } from "../services/socket";

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
      store.commit('setSidebarOpen', true);
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

  socket.on('chat_llm_response', (data) => {
    console.log('LLM response:', data);
    if (data.params) {
      // Update sliders based on LLM response
      isSyncingFromServer = true;
      for (const [name, value] of Object.entries(data.params)) {
        const param = parameters.value.inputs.find(p => p.name === name);
        if (param) {
          store.commit('updateParameterValue', { id: param.id, value });
        }
      }
      store.commit('addResponse', `Updated: ${Object.keys(data.params).join(', ')}`);
      setTimeout(() => { isSyncingFromServer = false; }, 100);
    }
    store.commit('setThinking', false);
  });
});

watch(
  () => parameters.value.inputs,
  (newInputs) => {
    if (isSyncingFromServer) return;
    if (newInputs.length > 0) {
      const params = {};
      newInputs.forEach(p => { params[p.name] = p.value; });
      emitParamsUpdate(params);
    }
  },
  { deep: true }
);

watch(
  () => prompt.value,
  (newPrompt) => {
    if (newPrompt?.trim()) {
      const paramsForLLM = parameters.value.inputs.map(p => ({
        name: p.name,
        value: p.value,
        min: p.min,
        max: p.max,
      }));
      emitChatRequest(newPrompt, paramsForLLM);
    }
  }
);
</script>
