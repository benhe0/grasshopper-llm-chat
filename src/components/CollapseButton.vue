<template>
  <button class="collapse-button" @click="toggleCollapse">
    <img
      v-if="isCollapsed"
      src="../assets/arrow-up.png"
      alt="Expand"
      width="10"
      height="10"
    />
    <img
      v-else
      src="../assets/arrow-down.png"
      alt="Collapse"
      width="10"
      height="10"
    />
  </button>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";

const props = defineProps({
  isCollapsed: Boolean,
});

const emit = defineEmits(["toggle-collapse"]);

const toggleCollapse = () => {
  emit("toggle-collapse");
};
</script>

<style scoped>
.collapse-button {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  padding: 6px 12px;
  flex-shrink: 0;
}

.collapse-button:hover {
  background-color: #0056b3;
}
</style>
