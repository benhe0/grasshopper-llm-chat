<template>
  <div id="app" :class="theme">
    <div class="theme-toggle">
      <ToggleButton v-model="isDarkTheme" onText="Dark" offText="Light" />
    </div>
    <ApiCaller />
    <Sidebar />
    <MeshViewer />
    <Chat />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";
import ApiCaller from "./components/ApiCaller.vue";
import Sidebar from "./components/Sidebar.vue";
import MeshViewer from "./components/MeshViewer.vue";
import Chat from "./components/Chat.vue";
import ToggleButton from "./components/ToggleButton.vue";

const store = useStore();
const theme = computed(() => store.state.theme);

const isDarkTheme = computed({
  get: () => store.state.theme === "dark",
  set: (val) => store.commit("setTheme", val ? "dark" : "light"),
});
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: Arial, sans-serif;
  overflow: hidden;
}

#app {
  height: 100%;
  width: 100%;
  position: relative;
}

#app.dark {
  background: #1a1a1a;
}

#app.light {
  background: #ffffff;
}

.theme-toggle {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
}
</style>
