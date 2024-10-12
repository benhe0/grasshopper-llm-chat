<template>
  <button class="sidebar-collapse-button" @click="toggleSidebar">
    {{ sidebarOpen ? '<' : '>' }}
  </button>
</template>

<script setup>
defineProps({ sidebarOpen: Boolean });
const emit = defineEmits(["toggle-sidebar"]);
const toggleSidebar = () => emit("toggle-sidebar");
</script>

<style scoped>
.sidebar-collapse-button {
  position: absolute;
  right: -25px;
  top: 50%;
  transform: translateY(-50%);
  width: 25px;
  height: 50px;
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 0 5px 5px 0;
}
</style>
