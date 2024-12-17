<template>
  <div :class="['gh-input-container', theme]">
    <p v-if="input">{{ input.label }}</p>
    <VueSlider
      v-model="localValue"
      :min="input?.min ?? 0"
      :max="input?.max ?? 100"
      :interval="calculateInterval(input?.min ?? 0, input?.max ?? 100)"
      :lazy="true"
    />
    <p v-if="input">{{ input.description }}</p>
  </div>
</template>

<script setup>
import { computed, watch } from "vue";
import { useStore } from "vuex";
import VueSlider from "vue-3-slider-component";

const props = defineProps({
  id: Number,
});

const store = useStore();
const theme = computed(() => store.state.theme);

const input = computed(() =>
  store.state.parameters.inputs.find((i) => i.id === props.id)
);

function calculateInterval(min, max) {
  const range = max - min;
  
  // Handle edge cases
  if (range === 0) return 1;
  if (range < 1) return range / 10;

  // Calculate a nice step size
  const targetSteps = 10;
  const rawStep = range / targetSteps;
  
  // Round to a nice number
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  let niceStep = magnitude;
  
  if (rawStep / magnitude >= 5) niceStep *= 5;
  else if (rawStep / magnitude >= 2) niceStep *= 2;
  
  // Ensure the step divides evenly into the range
  while ((max - min) % niceStep !== 0) {
    niceStep = niceStep / 2;
    // Prevent infinite loops for floating point numbers
    if (niceStep < 0.00001) {
      return (max - min) / targetSteps;
    }
  }
  
  return niceStep;
}

const localValue = computed({
  get: () => {
    const val = input.value ? input.value.value : 0;
    console.log(`[GHInput] Getter for slider id ${props.id} returns:`, val);
    return val;
  },
  set: (val) => {
    console.log(`[GHInput] Setter for slider id ${props.id} called with:`, val);
    if (input.value) {
      console.log(`[GHInput] Dispatching update for parameter:`, input.value.name, "with value:", parseFloat(val));
      store.dispatch("handleParameterUpdate", { id: props.id, value: parseFloat(val) });
    }
  },
});

watch(
  () => input.value?.value,
  (newVal, oldVal) => {
    console.log(`[GHInput] Watcher detected change for id ${props.id} from`, oldVal, `to`, newVal);
    if (newVal !== undefined && newVal !== localValue.value) {
      console.log(`[GHInput] Updating localValue for id ${props.id} to:`, parseFloat(newVal));
      localValue.value = parseFloat(newVal);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.gh-input-container {
  margin: 10px;
  padding: 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 5px;
  transition: background-color 0.3s, color 0.3s;
}

.dark .gh-input-container {
  background-color: rgba(40, 40, 40, 0.4);
  color: white;
  border-color: rgba(100, 100, 100, 0.8);
}

.light .gh-input-container {
  background-color: rgba(255, 255, 255, 0.4);
  color: black;
  border-color: rgba(200, 200, 200, 0.8);
}
</style>
