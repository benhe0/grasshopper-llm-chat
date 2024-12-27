<template>
  <div
    :class="[
      'sidebar',
      theme,
      { 'sidebar-closed': !sidebarOpen, 'sidebar-open': sidebarOpen },
    ]"
  >
    <SidebarHeader />
    <SidebarTab :receivedInputs="inputs" />
    <SidebarCollapseButton
      :sidebarOpen="sidebarOpen"
      @toggle-sidebar="toggleSidebar"
    />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";
import SidebarHeader from "./SidebarTabButtons.vue";
import SidebarTab from "./SidebarTab.vue";
import SidebarCollapseButton from "./SidebarCollapseButton.vue";

const store = useStore();
const inputs = computed(() => store.state.parameters.inputs);
const sidebarOpen = computed(() => store.state.sidebarOpen);
const theme = computed(() => store.state.theme);

const toggleSidebar = () => {
  store.commit("toggleSidebar");
};
</script>
<style scoped>
.sidebar {
  height: 100%;
  width: 17vw;
  position: absolute;
  transition: transform 0.3s ease;
  z-index: 1000; /* Ensure Sidebar is on top */
  backdrop-filter: blur(5px);
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.sidebar-closed {
  transform: translateX(-100%);
}

.sidebar-open {
  transform: translateX(0);
}

/* Dark Theme Styles */
.dark .sidebar {
  background-color: rgba(40, 40, 40, 0.9);
  border-color: rgba(100, 100, 100, 0.8);
  color: white;
}

/* Light Theme Styles */
.light .sidebar {
  background-color: rgba(255, 255, 255, 0.9);
  border-color: rgba(200, 200, 200, 0.8);
  color: black;
}

/* Mobile Styles */
@media (max-width: 768px) {
  .sidebar {
    width: 40vw;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 80vw;
  }

  .sidebar-closed {
    transform: translateX(-100%);
  }

  .sidebar-open {
    transform: translateX(0);
  }
}
</style>
