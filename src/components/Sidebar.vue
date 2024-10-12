<template>
  <div class="sidebar" :class="{ 'sidebar-closed': !sidebarOpen }">
    <SidebarHeader />
    <SidebarTab :receivedInputs="inputs" />
    <SidebarCollapseButton
      :sidebarOpen="sidebarOpen"
      @toggle-sidebar="toggleSidebar"
    />
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useStore } from "vuex";
import SidebarHeader from "./SidebarTabButtons.vue";
import SidebarTab from "./SidebarTab.vue";
import SidebarCollapseButton from "./SidebarCollapseButton.vue";

const store = useStore();
const sidebarOpen = ref(true);
const inputs = computed(() => store.state.parameters.inputs);

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};
</script>

<style scoped>
.sidebar {
  width: 250px;
  background: #f5f5f5;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s;
}

.sidebar-closed {
  transform: translateX(-230px);
}
</style>
