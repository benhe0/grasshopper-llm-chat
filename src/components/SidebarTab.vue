<template>
  <div class="sidebar-tab">
    <div class="sidebar-input-container">
      <GHInput v-for="input in receivedInputs" :key="input.id" :id="input.id" />
    </div>
  </div>
</template>

<script setup>
import GHInput from "./GHInput.vue";
defineProps({ receivedInputs: Array });
</script>

<style scoped>
.sidebar-tab {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
</style>
