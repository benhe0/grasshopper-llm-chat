<template>
  <label class="switch">
    <input
      type="checkbox"
      :checked="isChecked"
      @change="updateIsVoiceInput($event.target.checked)"
    />
    <span class="slider">{{ isChecked ? onText : offText }}</span>
  </label>
</template>

<script setup>
import { defineProps, defineEmits, computed } from "vue";

// Define the props
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  onText: {
    type: String,
    default: "On",
  },
  offText: {
    type: String,
    default: "Off",
  },
});

// Define the emits
const emit = defineEmits(["update:modelValue"]);

// Computed property for checked state
const isChecked = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit("update:modelValue", value);
  },
});

function updateIsVoiceInput(value) {
  isChecked.value = value;
}
</script>

<style>
.switch {
  position: relative;
  display: inline-block;
  width: 120px;
  height: 34px;
  margin: 10px;
  right: 0;
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
  transform: translateX(86px);
}
</style>
