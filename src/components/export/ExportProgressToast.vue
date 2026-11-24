<script setup>
import { computed, ref, watch } from 'vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import { useExportJob } from '@/composables/useExportJob.js'

// The floating "Exporting <Playlist> 12%" card in the bottom-right corner.
// It lives in AppLayout, so it stays on screen while the user moves between
// pages, and it comes back after a reload while an export is still running.
const {
  job,
  phase,
  status,
  busy,
  percent,
  title,
  detail,
  skipped,
  error,
  downloadError,
  downloading,
  cancelling,
  cancel,
  download,
  dismiss,
} = useExportJob()

const collapsed = ref(false)
const confirmingCancel = ref(false)
const showSkipped = ref(false)

// A new export always opens the card fully.
watch(
  () => job.value?.export_id,
  () => {
    collapsed.value = false
    confirmingCancel.value = false
    showSkipped.value = false
  },
)

const finished = computed(() => phase.value === 'finished')
const hasFile = computed(
  () => finished.value && !error.value && ['completed', 'partial'].includes(status.value),
)
const failed = computed(
  () => finished.value && (Boolean(error.value) || status.value === 'failed'),
)
const showPercent = computed(() => busy.value && status.value !== 'pending' && phase.value !== 'starting')
const indeterminate = computed(() => phase.value === 'starting' || status.value === 'pending')
const showBar = computed(() => busy.value || hasFile.value)

async function onConfirmCancel() {
  confirmingCancel.value = false
  await cancel()
}
</script>

<template>
  <section
    v-if="job"
    class="export-toast"
    :class="{ collapsed }"
    aria-label="Export progress"
  >
    <!-- Collapsed: a small pill that can be opened again. -->
    <button
      v-if="collapsed"
      class="pill"
      type="button"
      :aria-label="`Show export progress, ${percent}%`"
      @click="collapsed = false"
    >
      <span class="pill-text">Exporting · {{ percent }}%</span>
      <span class="chevron up" aria-hidden="true"></span>
    </button>

    <template v-else>
      <div class="head">
        <div class="text">
          <p class="title">
            <span class="title-name" :title="title" role="status" aria-live="polite">
              {{ title }}
            </span>
            <span v-if="showPercent" class="pct" aria-hidden="true">{{ percent }}%</span>
          </p>
          <p class="detail" :class="{ danger: failed }" aria-live="polite">{{ detail }}</p>
        </div>

        <button
          v-if="busy"
          class="icon-btn"
          type="button"
          aria-label="Minimize export progress"
          @click="collapsed = true"
        >
          <span class="chevron" aria-hidden="true"></span>
        </button>
        <button
          v-else
          class="icon-btn"
          type="button"
          aria-label="Close"
          @click="dismiss"
        >
          <span class="cross" aria-hidden="true"></span>
        </button>
      </div>

      <ProgressBar
        v-if="showBar"
        class="bar"
        small
        :percent="percent"
        :active="busy && !indeterminate"
        :indeterminate="indeterminate"
        :label="title"
      />

      <p v-if="downloadError" class="download-error" role="alert">{{ downloadError }}</p>

      <!-- Running: cancel, with a confirmation step. -->
      <div v-if="busy && job.export_id" class="actions">
        <template v-if="confirmingCancel">
          <span class="confirm-text">Stop this export?</span>
          <button class="app-btn small" type="button" @click="confirmingCancel = false">
            No
          </button>
          <button class="app-btn app-btn-danger small" type="button" @click="onConfirmCancel">
            Yes, stop
          </button>
        </template>
        <button
          v-else
          class="app-btn small"
          type="button"
          :disabled="cancelling"
          @click="confirmingCancel = true"
        >
          {{ cancelling ? 'Stopping…' : 'Cancel' }}
        </button>
      </div>

      <!-- Finished with a file. -->
      <div v-else-if="hasFile" class="actions">
        <button
          v-if="skipped.length"
          class="app-btn small"
          type="button"
          :aria-expanded="showSkipped"
          @click="showSkipped = !showSkipped"
        >
          Skipped ({{ skipped.length }})
        </button>
        <RouterLink :to="{ name: 'export-history' }" class="app-btn small" @click="dismiss">
          History
        </RouterLink>
        <button
          class="app-btn app-btn-primary small"
          type="button"
          :disabled="downloading"
          @click="download"
        >
          {{ downloading ? 'Starting…' : 'Download again' }}
        </button>
      </div>

      <ul v-if="hasFile && showSkipped" class="skipped">
        <li v-for="item in skipped" :key="item.position">
          <span class="skipped-title">
            {{ item.position }}. {{ item.title ?? 'Removed from library' }}
          </span>
          <span class="skipped-reason">{{ item.error_message }}</span>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.export-toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  /* Above page content, below the mobile menu (20-30), menus (50) and dialogs. */
  z-index: 15;
  width: 360px;
  max-width: calc(100vw - 24px);
  padding: 14px 16px 16px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
  color: var(--c-text);
  box-shadow:
    0 12px 32px rgba(17, 24, 39, 0.14),
    0 2px 6px rgba(17, 24, 39, 0.08);
}

.export-toast.collapsed {
  width: auto;
  padding: 0;
  border-radius: 999px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 0 18px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 14px;
  font-weight: bold;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
}

.head {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.text {
  flex: 1;
  min-width: 0;
}

.title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0;
  font-size: 15px;
  font-weight: bold;
}

.title-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pct {
  flex: none;
  font-variant-numeric: tabular-nums;
}

.detail {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--c-muted);
}

.detail.danger {
  color: var(--c-danger);
}

.icon-btn {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin: -4px -6px 0 0;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--c-muted);
  cursor: pointer;
}

.icon-btn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

/* Small CSS icons, so no icon library is needed. */
.chevron {
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
}

.chevron.up {
  transform: translateY(2px) rotate(-135deg);
}

.cross {
  position: relative;
  width: 12px;
  height: 12px;
}

.cross::before,
.cross::after {
  position: absolute;
  top: 5px;
  left: -1px;
  width: 14px;
  height: 2px;
  border-radius: 1px;
  background: currentColor;
  content: '';
  transform: rotate(45deg);
}

.cross::after {
  transform: rotate(-45deg);
}

.bar {
  margin-top: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.app-btn.small {
  min-height: 32px;
  padding: 0 12px;
  font-size: 14px;
}

.confirm-text {
  margin-right: auto;
  font-size: 14px;
}

.download-error {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--c-danger);
}

.skipped {
  max-height: 180px;
  margin: 12px 0 0;
  padding: 10px 0 0;
  overflow-y: auto;
  border-top: 1px solid var(--c-border);
  list-style: none;
}

.skipped li + li {
  margin-top: 8px;
}

.skipped-title {
  display: block;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.skipped-reason {
  display: block;
  font-size: 13px;
  color: var(--c-muted);
}

@media (max-width: 768px) {
  .export-toast {
    right: 12px;
    bottom: 12px;
    left: 12px;
    width: auto;
    max-width: none;
  }

  .export-toast.collapsed {
    left: auto;
  }
}
</style>
