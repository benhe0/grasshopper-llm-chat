<template>
  <div id="app">
    <div class="main-container">
      <div class="sidebar">
        <h2>Parameters</h2>
        <!-- sliders will go here -->
      </div>
      <div class="viewer">
        <p>3D Viewer placeholder</p>
      </div>
      <div class="chat">
        <p>Chat placeholder</p>
      </div>
    </div>
  </div>
</template>

<script setup>
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
}

.main-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 200px;
  background: #f0f0f0;
  padding: 10px;
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
  width: 300px;
  background: #e0e0e0;
  padding: 10px;
}
</style>
