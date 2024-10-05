<template>
  <div id="app">
    <Sidebar />
    <div class="main-content">
      <div class="viewer">
        <p>3D Viewer</p>
      </div>
      <div class="chat">
        <p>Chat</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import Sidebar from "./components/Sidebar.vue";
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: Arial, sans-serif;
}

#app {
  height: 100%;
  display: flex;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.viewer {
  flex: 1;
  background: #333;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat {
  height: 200px;
  background: #e0e0e0;
  padding: 10px;
}
</style>
