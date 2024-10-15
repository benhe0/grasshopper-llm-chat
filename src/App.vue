<template>
  <div id="app">
    <Sidebar />
    <div class="main-content">
      <div class="viewer">
        <p>3D Viewer (coming soon)</p>
      </div>
    </div>
    <Chat />
  </div>
</template>

<script setup>
import Sidebar from "./components/Sidebar.vue";
import Chat from "./components/Chat.vue";
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
  display: flex;
}

.main-content {
  flex: 1;
  display: flex;
}

.viewer {
  flex: 1;
  background: #333;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
