<template>
  <div class="mesh-viewer-container">
    <TresCanvas v-bind="gl">
      <TresAmbientLight :intensity="1" />
      <TresDirectionalLight :position="[20, 10, 10]" :intensity="1" />
      <TresPerspectiveCamera :position="[0, 10, 30]" ref="camera" />
      <OrbitControls />
      <!-- Grid and axes -->
      <primitive :object="gridHelper" />
      <primitive :object="axesHelper" />
      <!-- Placeholder mesh -->
      <TresMesh v-if="!hasMeshData">
        <TresBoxGeometry :args="[2, 2, 2]" />
        <TresMeshStandardMaterial color="#4CAF50" />
      </TresMesh>
    </TresCanvas>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useStore } from "vuex";
import * as THREE from "three";
import { TresCanvas } from "@tresjs/core";
import { OrbitControls } from "@tresjs/cientos";

const gl = {
  clearColor: "#222",
  shadows: true,
};

const store = useStore();
const hasMeshData = computed(() => !!store.state.receivedMeshData);

const gridHelper = new THREE.GridHelper(50, 50);
const axesHelper = new THREE.AxesHelper(25);
</script>

<style>
.mesh-viewer-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
}
</style>
