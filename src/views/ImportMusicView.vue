<!--
Import Music page: paste YouTube links and watch progress.
-->
<script setup>
import { onMounted } from 'vue'
import { MAX_LINKS, useImport } from '@/composables/useImport.js'
import ImportLinksBox from '@/components/import/ImportLinksBox.vue'
import ImportProgress from '@/components/import/ImportProgress.vue'
import ImportResults from '@/components/import/ImportResults.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

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
    <PageHeader
      title="Import Music"
      description="Paste YouTube links to add songs to your Music Library."
    />

    <div class="import-layout grid items-start gap-5 desktop:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <!-- Left: the links and the Import button. -->
      <div class="app-card links-card flex flex-col gap-4">
        <div>
          <h2 class="m-0 text-[16px] font-semibold">YouTube links</h2>
          <p class="mt-1 mb-0 text-[14px] text-muted">
            Up to {{ MAX_LINKS }} links, one per line. Videos and Shorts both work.
          </p>
        </div>

        <ImportLinksBox
          v-model="text"
          :count="count"
          :max="MAX_LINKS"
          :over-limit="overLimit"
          :disabled="busy"
        />

        <p v-if="overLimit" class="app-alert m-0" role="alert">
          You can import at most {{ MAX_LINKS }} links at a time. Remove
          {{ count - MAX_LINKS }} to continue.
        </p>
        <p v-if="error" class="app-alert m-0" role="alert">{{ error }}</p>

        <div class="actions flex flex-wrap items-center justify-between gap-2">
          <RouterLink :to="{ name: 'library' }" class="app-btn min-h-11">
            Back to Music Library
          </RouterLink>
          <button
            class="app-btn app-btn-primary min-h-11 px-[18px]"
            type="button"
            :disabled="!canImport"
            @click="start"
          >
            {{ busy ? 'Importing…' : 'Import' }}
          </button>
        </div>
      </div>

      <!-- Right: what happens, then live progress and the results. -->
      <div class="status-column flex flex-col gap-4">
        <div v-if="phase === 'idle'" class="app-card how">
          <h2 class="m-0 mb-3 text-[16px] font-semibold">How importing works</h2>
          <ol class="m-0 flex list-none flex-col gap-3 p-0 text-[14px] text-muted">
            <li class="flex gap-3">
              <span
                class="step inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-[12px] font-bold text-accent-light"
                aria-hidden="true"
              >1</span>
              <span>Paste links from YouTube, one per line.</span>
            </li>
            <li class="flex gap-3">
              <span
                class="step inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-[12px] font-bold text-accent-light"
                aria-hidden="true"
              >2</span>
              <span>Click Import. Each link is checked, and its title and length are read.</span>
            </li>
            <li class="flex gap-3">
              <span
                class="step inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-[12px] font-bold text-accent-light"
                aria-hidden="true"
              >3</span>
              <span>The songs appear in your Music Library. Songs you already have are skipped.</span>
            </li>
          </ol>
        </div>

        <ImportProgress
          v-else
          :phase="phase"
          :label="label"
          :percent="percent"
          :failed="phase === 'finished' && summary?.added === 0 && summary?.problems.length > 0"
        />

        <ImportResults v-if="summary" :summary="summary" />
      </div>
    </div>
  </section>
</template>
