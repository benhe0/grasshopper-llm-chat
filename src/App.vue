<template>
  <div id="app">
    <ApiCaller />
    <Sidebar />
    <MeshViewer />
    <Chat />
  </div>
</template>

<script setup>
import ApiCaller from "./components/ApiCaller.vue";
import Sidebar from "./components/Sidebar.vue";
import MeshViewer from "./components/MeshViewer.vue";
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
  width: 100%;
  position: relative;
}
</style>
