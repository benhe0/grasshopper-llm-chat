<template>
  <div class="mesh-viewer">
    <TresCanvas>
      <TresPerspectiveCamera :position="[5, 5, 5]" />
      <TresAmbientLight :intensity="0.5" />
      <TresDirectionalLight :position="[10, 10, 5]" :intensity="1" />
      <!-- Placeholder cube -->
      <TresMesh>
        <TresBoxGeometry :args="[1, 1, 1]" />
        <TresMeshStandardMaterial color="#007bff" />
      </TresMesh>
    </TresCanvas>
  </div>
</template>

<script setup>
import { TresCanvas } from "@tresjs/core";
</script>

<style scoped>
.mesh-viewer {
  width: 100%;
  height: 100%;
}
</style>
