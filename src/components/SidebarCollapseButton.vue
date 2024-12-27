<template>
  <button :class="['sidebar-collapse-button', theme]" @click="toggleSidebar">
    <img
      v-if="sidebarOpen"
      src="../assets/arrow-up.png"
      alt="Close"
      width="10"
      height="10"
    />
    <img
      v-else
      src="../assets/arrow-down.png"
      alt="Open"
      width="10"
      height="10"
    />
  </button>
</template>

<script setup>
import { defineProps, defineEmits, computed } from "vue";
import { useStore } from "vuex";

const props = defineProps({
  sidebarOpen: Boolean,
});

const emit = defineEmits(["toggle-sidebar"]);

const toggleSidebar = () => {
  emit("toggle-sidebar");
};

const store = useStore();
const theme = computed(() => store.state.theme);
</script>

<style scoped>
.sidebar-collapse-button {
  position: fixed;
  top: 50%;
  right: 0%;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  padding: 8px 16px;
  z-index: 1001;
  transform: translate(90%, 0) rotate(270deg);
  transition: background-color 0.3s;
}

/* Dark Theme Styles */
.dark .sidebar-collapse-button {
  background-color: #007bff;
  color: white;
}

.dark .sidebar-collapse-button:hover {
  background-color: #0056b3;
}

/* Light Theme Styles */
.light .sidebar-collapse-button {
  background-color: #007bff;
  color: black;
}

.light .sidebar-collapse-button:hover {
  background-color: #0056b3;
}
</style>
