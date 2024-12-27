<template>
  <div
    id="app"
    :class="{
      'light-theme': theme === 'light',
      'dark-theme': theme === 'dark',
    }"
  >
    <div class="theme-toggle-container">
      <ToggleButton
        :modelValue="isDarkTheme"
        @update:modelValue="setTheme"
        onText="Dark"
        offText="Light"
      />
    </div>
    <ApiCaller />
    <Chat />
    <div class="mesh-and-sidebar">
      <MeshViewer />
      <Sidebar />
    </div>
  </div>
</template>

<script setup>
import { useStore } from "vuex";
import Sidebar from "./components/Sidebar.vue";
import Chat from "./components/Chat.vue";
import MeshViewer from "./components/MeshViewer.vue";
import { computed } from "vue";
import ApiCaller from "./components/ApiCaller.vue";
import ToggleButton from "./components/ToggleButton.vue";

const store = useStore();
const theme = computed(() => store.state.theme);

// Computed property to check if the theme is dark
const isDarkTheme = computed({
  get: () => store.state.theme === "dark",
  set: (value) => {
    store.commit("setTheme", value ? "dark" : "light");
  },
});

function setTheme(value) {
  store.commit("setTheme", value ? "dark" : "light");
}
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
}

#app {
  height: 100%;
  width: 100%;
  position: relative;
}

.light-theme {
  background-color: #fff;
}

.dark-theme {
  background-color: #000;
}

.theme-toggle-container {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 1000;
  /* padding: 10px; */
}
</style>
