<template>
  <div :class="['sidebar-tab', theme]">
    <div class="sidebar-input-container">
      <GHInput v-for="input in receivedInputs" :key="input.id" :id="input.id" />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";
import GHInput from "./GHInput.vue";
import { defineProps } from "vue";

const store = useStore();
const theme = computed(() => store.state.theme);

const props = defineProps({
  receivedInputs: Array,
});
</script>

<style scoped>
.sidebar-tab {
  flex: 1;
  overflow-y: auto;
  transition: background-color 0.3s, color 0.3s;
}

/* Dark Theme Styles */
.dark .sidebar-tab {
  color: white;
}

/* Light Theme Styles */
.light .sidebar-tab {
  color: black;
}

.sidebar-input-container {
  z-index: 1001;
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.sidebar-input-container::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  background-color: #f5f5f5;
}

.sidebar-input-container::-webkit-scrollbar {
  width: 6px;
  background-color: #f5f5f5;
  position: absolute;
  right: 10%;
}

.sidebar-input-container::-webkit-scrollbar-thumb {
  border-radius: 10px;
  -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
  background-color: grey;
}
</style>
