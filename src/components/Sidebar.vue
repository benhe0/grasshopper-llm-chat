<template>
  <div class="sidebar" :class="{ 'sidebar-closed': !sidebarOpen }">
    <div class="sidebar-header">
      <span>Parameters</span>
    </div>
    <div class="sidebar-content">
      <p v-if="inputs.length === 0">No parameters loaded</p>
      <div v-for="input in inputs" :key="input.name" class="param-item">
        {{ input.name }}: {{ input.value }}
      </div>
    </div>
    <button class="collapse-btn" @click="toggleSidebar">
      {{ sidebarOpen ? '<' : '>' }}
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useStore } from "vuex";

const store = useStore();
const sidebarOpen = ref(true);
const inputs = computed(() => store.state.parameters.inputs);

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};
</script>

<style scoped>
.sidebar {
  width: 200px;
  background: #f0f0f0;
  height: 100%;
  position: relative;
  transition: transform 0.3s;
}

.sidebar-closed {
  transform: translateX(-180px);
}

.sidebar-header {
  padding: 10px;
  font-weight: bold;
  border-bottom: 1px solid #ccc;
}

.sidebar-content {
  padding: 10px;
}

.param-item {
  margin: 5px 0;
  padding: 5px;
  background: white;
  border-radius: 4px;
}

.collapse-btn {
  position: absolute;
  right: -20px;
  top: 50%;
  width: 20px;
  height: 40px;
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}
</style>
