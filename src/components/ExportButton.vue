<script setup>
import { useLinks } from '../composables/useLinks.js'

const { canExport, exportZip } = useLinks()
</script>

<template>
  <button class="action-button" type="button" :disabled="!canExport" @click="exportZip">
    export
  </button>
</template>
