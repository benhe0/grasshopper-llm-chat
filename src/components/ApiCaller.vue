<template>
  <!-- Logic-only component, no UI -->
</template>

<script setup>
import { watch, computed, toRaw, onMounted, onUnmounted, ref } from "vue";
import { useStore } from "vuex";
import {
  initSocket,
  getSocket,
  disconnectSocket,
  connectionState,
  emitParamsUpdate,
  emitChatRequest
} from "../services/socket";

const store = useStore();

// Computed properties from the Vuex store
const parameters = computed(() => store.state.parameters);
const prompt = computed(() => store.state.prompt);
const username = computed(() => store.state.username);
const websocketUrl = computed(() => store.state.websocketUrl);

// Track if we're currently processing a request
const isProcessing = ref(false);

// Flag to prevent update loop when syncing from server
let isSyncingFromServer = false;

// Debounce timer for parameter updates
let paramUpdateDebounce = null;
const DEBOUNCE_MS = 50; // 50ms debounce for rapid slider changes

// Initialize WebSocket connection and handlers
const setupSocketHandlers = () => {
  const socket = getSocket();

  // Initial params from server on connect
  socket.on('params_init', (data) => {
    console.log('[Socket] params_init:', data);
    handleParamsFromServer(data.params, true);
  });

  // Params sync from GH (when user changes sliders in GH)
  socket.on('params_sync', (data) => {
    console.log('[Socket] params_sync:', data);
    if (data.source === 'grasshopper') {
      handleParamsFromServer(data.params, false);
    }
  });

  // Params broadcast from another web client
  socket.on('params_broadcast', (data) => {
    console.log('[Socket] params_broadcast from other client:', data);
    if (data.source === 'other_client' && data.params) {
      // Update local sliders to match other client's changes
      isSyncingFromServer = true;
      for (const [name, value] of Object.entries(data.params)) {
        store.dispatch('updateParameterByName', { name, value });
      }
      setTimeout(() => { isSyncingFromServer = false; }, 100);
      // Show loading since geometry will update
      store.commit('setGeometryLoading', true);
    }
  });

  // Acknowledgment that params were sent to GH
  socket.on('params_ack', (data) => {
    console.log('[Socket] params_ack:', data);
    // Params have been forwarded to GH
  });

  // Chat message broadcast (from self or other clients)
  socket.on('chat_message', (data) => {
    console.log('[Socket] chat_message:', data);
    if (data.type === 'user') {
      // Add user message to chat with username
      const senderName = data.username || (data.from_self ? 'You' : 'User');
      store.commit('addUserMessage', { text: data.content, username: senderName });
    }
  });

  // Geometry result pushed from server
  socket.on('geometry_result', (data) => {
    console.log('[Socket] geometry_result received');

    if (data.geometry) {
      store.commit('setReceivedMeshData', data.geometry);
    }

    store.commit('setGeometryLoading', false);
    isProcessing.value = false;
  });

  // Chat processing status
  socket.on('chat_processing', (data) => {
    console.log('[Socket] chat_processing:', data);
    store.commit('setThinking', true);
  });

  // LLM response during chat
  socket.on('chat_llm_response', (data) => {
    console.log('[Socket] chat_llm_response:', data);

    if (data.params && Object.keys(data.params).length > 0) {
      const changes = Object.entries(data.params)
        .map(([name, value]) => `${name}: ${value}`)
        .join(', ');
      store.commit('addResponseMessage', `Setting: ${changes}`);

      // Update local params
      isSyncingFromServer = true;
      for (const [name, value] of Object.entries(data.params)) {
        store.dispatch('updateParameterByName', { name, value });
      }
      setTimeout(() => { isSyncingFromServer = false; }, 100);
    }

    store.commit('setThinking', false);
  });

  // Error handling
  socket.on('error', (data) => {
    console.error('[Socket] Error:', data);
    store.commit('addResponseMessage', `Error: ${data.message}`);
    store.commit('setThinking', false);
    store.commit('setGeometryLoading', false);
    isProcessing.value = false;
  });
};

// Handle params received from server
const handleParamsFromServer = (serverParams, isInitial) => {
  if (!serverParams || serverParams.length === 0) {
    console.log('[Socket] No parameters from server');
    return;
  }

  const currentInputs = parameters.value.inputs;

  // Initial load
  if (isInitial || currentInputs.length === 0) {
    console.log('[Socket] Initial parameter load');
    const processedInputs = serverParams.map((input) => ({
      ...input,
      name: input.name || input.label,
      label: input.label || input.name,
      value: input.value ?? input.default ?? 0,
    }));

    store.commit('setParameters', processedInputs);
    store.commit('setSidebarOpen', true);
    return;
  }

  // Sync individual param changes from server
  isSyncingFromServer = true;

  for (const serverParam of serverParams) {
    const name = serverParam.name || serverParam.label;
    const serverValue = serverParam.value ?? 0;
    const localParam = currentInputs.find((p) => p.name === name);

    if (localParam && localParam.value !== serverValue) {
      console.log(`[Socket] Server changed ${name}: ${localParam.value} -> ${serverValue}`);
      store.dispatch('updateParameterByName', { name, value: serverValue });
    }
  }

  setTimeout(() => { isSyncingFromServer = false; }, 100);
};

// Debounced parameter update to GH
const sendParamsToServer = () => {
  if (paramUpdateDebounce) {
    clearTimeout(paramUpdateDebounce);
  }

  paramUpdateDebounce = setTimeout(() => {
    const currentParams = {};
    parameters.value.inputs.forEach((p) => {
      currentParams[p.name] = p.value;
    });

    console.log('[Socket] Sending params_update:', currentParams);
    store.commit('setGeometryLoading', true);
    emitParamsUpdate(currentParams);
  }, DEBOUNCE_MS);
};

// Watch for parameter changes - send to GH via WebSocket
watch(
  () => parameters.value.formatted,
  (newParams) => {
    if (isSyncingFromServer || isProcessing.value) {
      return;
    }
    if (newParams.length > 0) {
      sendParamsToServer();
    }
  },
  { deep: true }
);

// Watch for prompt changes (chat messages with NLP)
watch(
  () => prompt.value,
  (newPrompt) => {
    if (newPrompt && newPrompt.trim() && !isProcessing.value) {
      console.log('[Socket] Sending chat_request:', newPrompt);
      isProcessing.value = true;
      store.commit('setThinking', true);
      store.commit('setGeometryLoading', true);

      const paramsForLLM = parameters.value.inputs.map((p) => ({
        name: p.name,
        label: p.label,
        value: p.value,
        min: p.min,
        max: p.max,
        description: p.description,
      }));

      emitChatRequest(newPrompt, paramsForLLM, username.value);
    }
  }
);

// Watch for websocket URL changes and re-setup handlers
watch(
  () => websocketUrl.value,
  (newUrl, oldUrl) => {
    if (newUrl && newUrl !== oldUrl) {
      console.log('[ApiCaller] WebSocket URL changed, re-setting up handlers');
      // Small delay to allow socket to reconnect
      setTimeout(() => {
        setupSocketHandlers();
      }, 100);
    }
  }
);

// Initialize on mount
onMounted(() => {
  initSocket();
  setupSocketHandlers();
});

// Cleanup on unmount
onUnmounted(() => {
  if (paramUpdateDebounce) {
    clearTimeout(paramUpdateDebounce);
  }
  disconnectSocket();
});
</script>
