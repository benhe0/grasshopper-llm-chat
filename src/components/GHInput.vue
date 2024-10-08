<template>
  <div class="gh-input">
    <label>{{ input?.label || input?.name }}</label>
    <VueSlider
      v-model="localValue"
      :min="input?.min ?? 0"
      :max="input?.max ?? 100"
      :interval="1"
    />
    <span>{{ localValue }}</span>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStore } from "vuex";
import VueSlider from "vue-3-slider-component";

const props = defineProps({
  id: Number,
});

const store = useStore();

const input = computed(() =>
  store.state.parameters.inputs.find((i) => i.id === props.id)
);

const localValue = computed({
  get: () => input.value?.value ?? 0,
  set: (val) => {
    store.commit("updateParameterValue", { id: props.id, value: val });
  },
});
</script>

<style scoped>
.gh-input {
  margin: 10px 0;
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.gh-input label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
</style>
