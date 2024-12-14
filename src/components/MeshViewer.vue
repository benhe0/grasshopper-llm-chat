<template>
  <div class="mesh-viewer-container">
    <button class="fit-view" @click="fitView">
      <img src="../assets/fit.png" alt="Fit View" width="20" height="20" />
    </button>
    <TresCanvas v-bind="gl">
      <TresAmbientLight :intensity="1" />
      <TresDirectionalLight
        :position="[20, 2, 10]"
        :intensity="1.2"
        cast-shadow
      />
      <TresPerspectiveCamera :position="[0, 10, 50]" ref="camera" />
      <OrbitControls ref="controls" />
      <!-- Grid and Axes Helpers -->
      <primitive :object="new THREE.GridHelper(100, 100)" />
      <primitive :object="new THREE.AxesHelper(50)" />
      <!-- Render each mesh -->
      <primitive
        v-for="(mesh, index) in meshes"
        :key="mesh.uuid + keySuffix + index"
        :object="mesh"
      />
    </TresCanvas>
  </div>
</template>

<script setup>
import { computed, watch, shallowReactive, toRaw, nextTick, ref } from "vue";
import { useStore } from "vuex";
import * as THREE from "three";
import { SRGBColorSpace, NoToneMapping } from "three";
import { TresCanvas } from "@tresjs/core";
import { OrbitControls } from "@tresjs/cientos";
import TWEEN from "@tweenjs/tween.js";

const gl = {
  clearColor: null,
  alpha: true,
  shadows: true,
  outputColorSpace: SRGBColorSpace,
  toneMapping: NoToneMapping,
};

const store = useStore();
const meshes = shallowReactive([]);
const keySuffix = ref(0);
const blendFactor = ref(1.0);
const camera = ref(null);
const controls = ref(null);
const hasInitializedCamera = ref(false);
const lastMeshHash = ref(null);

const meshData = computed(() => store.state.receivedMeshData);
const geometryLoading = computed(() => store.state.geometryLoading);

// -----------------------
// Mesh Change Detection
// -----------------------
function computeMeshHash(data) {
  if (!data || !Array.isArray(data)) return null;
  // Create a simple hash from vertex counts and sample values
  const parts = data.map((obj) => {
    const rawObj = toRaw(obj);
    const meshInfo = rawObj?.mesh?.meshData;
    if (!meshInfo?.vertices) return "empty";
    const verts = meshInfo.vertices;
    // Use vertex count + sum of all vertex coords as fingerprint (order-independent)
    let sumX = 0, sumY = 0, sumZ = 0;
    for (const v of verts) {
      sumX += v.X || 0;
      sumY += v.Y || 0;
      sumZ += v.Z || 0;
    }
    return `${verts.length}:${sumX.toFixed(2)}:${sumY.toFixed(2)}:${sumZ.toFixed(2)}`;
  });
  // Sort parts so array order doesn't matter
  return parts.sort().join("|");
}

// -----------------------
// Materials & Shaders
// -----------------------
const woodMaterial = new THREE.MeshStandardMaterial({
  color: 0x8b4513,
  side: THREE.DoubleSide,
});
const concreteMaterial = new THREE.MeshStandardMaterial({
  color: 0x808080,
  side: THREE.DoubleSide,
});
const glassMaterial = new THREE.MeshStandardMaterial({
  color: 0x007bff,
  side: THREE.DoubleSide,
  transparent: true,
  opacity: 0.1,
  roughness: 0,
});

// Color palette for meshes without a specified material
const defaultColorPalette = [
  0xe63946, // Red
  0x2a9d8f, // Teal
  0xe9c46a, // Yellow
  0x264653, // Dark blue
  0xf4a261, // Orange
  0x9b5de5, // Purple
  0x00f5d4, // Cyan
  0xfee440, // Bright yellow
  0xf15bb5, // Pink
  0x00bbf9, // Sky blue
  0x8ac926, // Lime green
  0xff006e, // Magenta
];

const vertexShader = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  uniform float blendFactor;
  uniform vec3 normalColor;
  uniform vec3 wireframeColor;
  uniform float normalOpacity;
  uniform float wireframeOpacity;
  uniform vec3 ambientLightColor;
  uniform vec3 directionalLightColor;
  uniform vec3 directionalLightDirection;
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vec3 normalMaterialColor = normalColor;
    vec3 wireframeMaterialColor = wireframeColor;
    vec3 ambient = ambientLightColor;
    vec3 lightDir = normalize(directionalLightDirection);
    float diff = max(dot(vNormal, lightDir), 0.0);
    vec3 diffuse = diff * directionalLightColor;
    vec3 lighting = ambient + diffuse;
    vec4 litNormalColor = vec4(normalMaterialColor * lighting, normalOpacity);
    vec4 litWireframeColor = vec4(wireframeMaterialColor * lighting, wireframeOpacity);
    gl_FragColor = mix(litNormalColor, litWireframeColor, blendFactor);
  }
`;

const uniforms = {
  blendFactor: { value: 1.0 },
  normalColor: { value: new THREE.Color(0x000000) },
  wireframeColor: { value: new THREE.Color(0xffffff) },
  normalOpacity: { value: 1.0 },
  wireframeOpacity: { value: 1.0 },
  ambientLightColor: { value: new THREE.Color(0x333333) },
  directionalLightColor: { value: new THREE.Color(0xffffff) },
  directionalLightDirection: { value: new THREE.Vector3(20, 2, 10).normalize() },
};

function createBlendMaterial(normalMaterial) {
  return new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      ...uniforms,
      normalColor: { value: normalMaterial.color },
      normalOpacity: { value: normalMaterial.opacity || 1.0 },
    },
    side: THREE.DoubleSide,
    transparent: true,
  });
}

function animateBlendFactor(targetValue, duration) {
  new TWEEN.Tween(uniforms.blendFactor)
    .to({ value: targetValue }, duration)
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();
}
function animate() {
  requestAnimationFrame(animate);
  TWEEN.update();
}
animate();

watch(
  geometryLoading,
  (newValue) => {
    animateBlendFactor(newValue ? 1.0 : 0.0, 1000);
  },
  { immediate: true }
);

// -----------------------
// Mesh Data Watcher
// -----------------------
watch(
  meshData,
  async (newData) => {
    if (!newData || !Array.isArray(newData) || newData.length === 0) {
      console.log("No valid mesh data received");
      return;
    }

    // Skip processing if mesh data hasn't actually changed
    const newHash = computeMeshHash(newData);
    if (newHash === lastMeshHash.value) {
      return;
    }
    lastMeshHash.value = newHash;

    // Clear existing meshes
    meshes.length = 0;

    newData.forEach((dataObj, index) => {
      const rawData = toRaw(dataObj);
      if (!rawData || !rawData.mesh || !rawData.mesh.meshData) {
        console.error("Invalid mesh data structure:", rawData);
        return;
      }
      const meshInfo = rawData.mesh.meshData;
      const metaData = rawData.mesh.metaData;

      if (!meshInfo.vertices || !meshInfo.normals || !meshInfo.faces) {
        console.error("Missing required mesh data properties:", meshInfo);
        return;
      }

      // Process vertices and normals.
      // (Adjust property names if your data uses lowercase keys.)
      const vertices = new Float32Array(
        meshInfo.vertices.flatMap((v) => [v.X, v.Z, v.Y])
      );
      const normals = new Float32Array(
        meshInfo.normals.flatMap((n) => [n.X, n.Z, n.Y])
      );

      // Process faces:
      // If face.C equals face.D, assume it's a triangle.
      // Otherwise, assume a quad and triangulate it.
      const faceArray = [];
      meshInfo.faces.forEach((face) => {
        if (face.C === face.D) {
          faceArray.push(face.A, face.B, face.C);
        } else {
          faceArray.push(face.A, face.B, face.C, face.A, face.C, face.D);
        }
      });
      const indices = new Uint32Array(faceArray);

      console.log("Processed indices count:", indices.length);

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
      geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
      if (indices.length > 0) {
        geometry.setIndex(new THREE.BufferAttribute(indices, 1));
      }

      // Select a material based on metaData.
      // For metaData.material === "default" (or unrecognized), we use a green MeshStandardMaterial.
      let material;
      switch (metaData?.material) {
        case "wood":
          material = woodMaterial;
          break;
        case "concrete":
          material = concreteMaterial;
          break;
        case "glass":
          material = glassMaterial;
          break;
        default:
          material = new THREE.MeshStandardMaterial({
            color: defaultColorPalette[index % defaultColorPalette.length],
            side: THREE.DoubleSide,
          });
      }
      // Optionally, you could use the shader blend material:
      // material = createBlendMaterial(material);

      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      meshes.push(mesh);

      geometry.computeBoundingSphere();
    });

    // Only auto-frame camera on first geometry load
    if (!hasInitializedCamera.value && meshes.length > 0 && camera.value) {
      const box = new THREE.Box3();
      meshes.forEach((mesh) => box.expandByObject(mesh));
      const center = new THREE.Vector3();
      box.getCenter(center);
      const size = new THREE.Vector3();
      box.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z);

      camera.value.position.set(center.x, center.y, center.z + maxDim * 2);
      camera.value.lookAt(center);
      if (controls.value?.target) {
        controls.value.target.copy(center);
        controls.value.update();
      }
      hasInitializedCamera.value = true;
    }

    keySuffix.value++; // Force re-rendering of the mesh primitives
    store.commit("setGeometryLoading", false);
    await nextTick();
  },
  { deep: true }
);

// -----------------------
// Fit View Function
// -----------------------
function fitView() {
  const box = new THREE.Box3();
  meshes.forEach((mesh) => {
    box.expandByObject(mesh);
  });

  const size = new THREE.Vector3();
  box.getSize(size);
  const center = new THREE.Vector3();
  box.getCenter(center);

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.value.fov * (Math.PI / 180);
  let cameraZ = Math.abs((maxDim / 2) * Math.tan(fov * 2));
  cameraZ *= 1.5;
  camera.value.position.set(center.x, center.y, cameraZ);
  camera.value.lookAt(center);

  if (controls.value) {
    controls.value.target.copy(center);
    controls.value.update();
  }
}
</script>

<style>
.mesh-viewer-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 500;
}

.slider-container {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.8);
  padding: 10px;
  border-radius: 5px;
  z-index: 1000;
}

.fit-view {
  position: absolute;
  top: 1%;
  left: 50%;
  padding: 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  background: #007bff;
  transform: translateX(-50%);
  z-index: 1000;
  height: 30px;
  width: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.fit-view button {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
</style>
