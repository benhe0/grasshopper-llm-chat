<template>
  <label class="switch">
    <input type="checkbox" :checked="modelValue" @change="$emit('update:modelValue', $event.target.checked)" />
    <span class="slider">{{ modelValue ? onText : offText }}</span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  onText: { type: String, default: "On" },
  offText: { type: String, default: "Off" },
});
defineEmits(["update:modelValue"]);
</script>

<style>
.switch {
  position: relative;
  display: inline-block;
  width: 100px;
  height: 34px;
  margin: 10px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #007bff;
}

input:checked + .slider:before {
  transform: translateX(66px);
}
</style>
