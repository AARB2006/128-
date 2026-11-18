<script setup>
import { onMounted } from 'vue'
import { MAX_LINKS, useImport } from '@/composables/useImport.js'
import ImportLinksBox from '@/components/import/ImportLinksBox.vue'
import ImportProgress from '@/components/import/ImportProgress.vue'
import ImportResults from '@/components/import/ImportResults.vue'

const {
  text,
  phase,
  error,
  count,
  overLimit,
  busy,
  canImport,
  percent,
  label,
  summary,
  start,
  resume,
} = useImport()

onMounted(resume)
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Import Music</h1>

    <p class="app-muted intro mt-0 mb-4">
      Paste up to {{ MAX_LINKS }} YouTube links, one per line. Each song is added to your
      Music Library.
    </p>

    <ImportLinksBox
      v-model="text"
      :count="count"
      :max="MAX_LINKS"
      :over-limit="overLimit"
      :disabled="busy"
    />

    <p v-if="overLimit" class="app-alert mt-4 mb-0" role="alert">
      You can import at most {{ MAX_LINKS }} links at a time. Remove
      {{ count - MAX_LINKS }} to continue.
    </p>

    <p v-if="error" class="app-alert mt-4 mb-0" role="alert">{{ error }}</p>

    <ImportProgress
      class="mt-4"
      :phase="phase"
      :label="label"
      :percent="percent"
      :failed="phase === 'finished' && summary?.added === 0 && summary?.problems.length > 0"
    />

    <div class="actions my-4 flex flex-wrap items-center justify-between gap-2">
      <RouterLink :to="{ name: 'library' }" class="app-btn">Back to Music Library</RouterLink>

      <button
        class="app-btn app-btn-primary"
        type="button"
        :disabled="!canImport"
        @click="start"
      >
        Import
      </button>
    </div>

    <ImportResults v-if="summary" :summary="summary" />
  </section>
</template>
