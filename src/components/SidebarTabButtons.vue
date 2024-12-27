<template>
  <div :class="['sidebar-header', theme]">
    <span>Parameters</span>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";

const store = useStore();
const theme = computed(() => store.state.theme);
</script>

<style scoped>
.sidebar-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px;
  font-weight: bold;
  height: 3%;
  z-index: 10002;
  transition: background-color 0.3s, color 0.3s;
}

/* Dark Theme Styles */
.dark.sidebar-header {
  background-color: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

/* Light Theme Styles */
.light.sidebar-header {
  background-color: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  color: black;
}
</style>
