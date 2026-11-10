<script setup>
import { useLinks } from '../composables/useLinks.js'

const { canImport, importDraft } = useLinks()
</script>

<template>
  <button class="action-button" type="button" :disabled="!canImport" @click="importDraft">
    import
  </button>
</template>
