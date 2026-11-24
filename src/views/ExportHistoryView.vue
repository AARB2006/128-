<!--
Export History page: past exports, download, export again, delete.
-->
<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  clearExportHistory,
  deleteExport,
  downloadExport,
  getExportHistory,
  isExpired,
} from '@/services/exportService.js'
import { useExportJob } from '@/composables/useExportJob.js'
import RowMenu from '@/components/ui/RowMenu.vue'
import ExportPlaylistDialog from '@/components/export/ExportPlaylistDialog.vue'
import DeleteExportsDialog from '@/components/export/DeleteExportsDialog.vue'

// Recent exports that produced a file (completed, or with some songs skipped).
const exportsList = ref([])
const loading = ref(true)
const loadError = ref('')
const actionError = ref('')
const expanded = ref(new Set())
const now = ref(Date.now())

const { busy, finishedCount, job, dismiss } = useExportJob()

async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    exportsList.value = await getExportHistory()
  } catch (e) {
    loadError.value = e.message || 'Could not load your export history.'
  } finally {
    loading.value = false
  }
}

onMounted(() => load())

// Reload when an export finishes while this page is open.
watch(finishedCount, () => load({ silent: true }))

// Keep "Download" availability honest without reloading.
const clock = setInterval(() => (now.value = Date.now()), 30_000)
onBeforeUnmount(() => clearInterval(clock))

const dateFormat = { dateStyle: 'medium', timeStyle: 'short' }
const formatDate = (value) => new Date(value).toLocaleString(undefined, dateFormat)
const formatTime = (value) =>
  new Date(value).toLocaleTimeString(undefined, { timeStyle: 'short' })

// Names come from the playlist as it is now.
const nameOf = (row) => row.playlist_name ?? 'Deleted playlist'

function toggle(id) {
  const next = new Set(expanded.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expanded.value = next
}

function menuItems(row) {
  const expired = isExpired(row, now.value)
  return [
    {
      key: 'download',
      label: 'Download',
      disabled: expired,
      title: expired ? 'This file has expired. Export the playlist again.' : undefined,
    },
    {
      key: 'again',
      label: 'Export again',
      disabled: !row.playlist || busy.value,
      title: !row.playlist
        ? 'This playlist was deleted'
        : busy.value
          ? 'Another export is running'
          : undefined,
    },
    { key: 'delete', label: 'Delete', danger: true },
  ]
}

// ---- actions -------------------------------------------------------------------
const exportTarget = ref(null)

async function onMenu(row, key) {
  actionError.value = ''

  if (key === 'download') {
    try {
      await downloadExport(row.export_id)
    } catch (e) {
      actionError.value = e.message || 'The download could not be started.'
      if (e.status === 410) load({ silent: true })
    }
  }

  if (key === 'delete') {
    deleteError.value = ''
    deleteTarget.value = row
  }

  if (key === 'again' && row.playlist) {
    exportTarget.value = {
      playlist_id: row.playlist_id,
      name: row.playlist.name,
      song_count: row.playlist.song_count,
    }
  }
}

// ---- delete --------------------------------------------------------------------
// A row to delete, or 'all' for the whole history.
const deleteTarget = ref(null)
const deleting = ref(false)
const deleteError = ref('')

function askClearHistory() {
  deleteError.value = ''
  deleteTarget.value = 'all'
}

async function onConfirmDelete() {
  const target = deleteTarget.value
  if (!target || deleting.value) return

  deleting.value = true
  deleteError.value = ''
  try {
    if (target === 'all') await clearExportHistory()
    else await deleteExport(target.export_id)

    // The progress card's Download button would point at a deleted file.
    if (!busy.value && (target === 'all' || job.value?.export_id === target.export_id)) {
      dismiss()
    }
    expanded.value = new Set()
    deleteTarget.value = null
    await load({ silent: true })
  } catch (e) {
    deleteError.value = e.message || 'The delete did not work. Please try again.'
    if (e.status === 404) load({ silent: true }) // already gone: refresh the list
  } finally {
    deleting.value = false
  }
}

const hasRows = computed(() => exportsList.value.length > 0)
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Export History</h1>
    <p class="app-muted intro">
      Playlists you exported recently. Each ZIP can be downloaded again for a short time
      after it's made; after that, export the playlist again.
    </p>

    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <p v-if="loading" class="app-muted">Loading your exports…</p>

    <div v-else-if="loadError" class="app-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <div v-else-if="!hasRows" class="app-card empty">
      <h2>No exports yet</h2>
      <p class="app-muted">Open a playlist and choose Export Playlist.</p>
      <RouterLink :to="{ name: 'playlists' }" class="app-btn app-btn-primary">
        Go to Playlists
      </RouterLink>
    </div>

    <template v-else>
    <div class="toolbar">
      <button class="app-btn app-btn-danger" type="button" @click="askClearHistory">
        Delete History
      </button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="toggle"><span class="visually-hidden">Show songs</span></th>
            <th>Playlist</th>
            <th class="date">Exported</th>
            <th class="songs">Songs</th>
            <th class="menu"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>

        <tbody v-for="row in exportsList" :key="row.export_id">
          <tr :class="{ open: expanded.has(row.export_id) }">
            <td class="toggle">
              <button
                class="toggle-btn"
                type="button"
                :aria-expanded="expanded.has(row.export_id)"
                :aria-controls="`songs-${row.export_id}`"
                :aria-label="`Show songs in ${nameOf(row)}`"
                @click="toggle(row.export_id)"
              >
                <span class="chevron" aria-hidden="true"></span>
              </button>
            </td>

            <td class="name-cell">
              <RouterLink
                v-if="row.playlist"
                class="name"
                :to="{ name: 'playlist', params: { playlistId: row.playlist_id } }"
              >
                {{ row.playlist_name }}
              </RouterLink>
              <span v-else class="name deleted">Deleted playlist</span>
              <span class="sub app-muted">
                <template v-if="isExpired(row, now)">Download expired</template>
                <template v-else>
                  Download available until {{ formatTime(row.file_expires_at) }}
                </template>
              </span>
            </td>

            <td class="date">{{ formatDate(row.created_at) }}</td>

            <td class="songs">
              <template v-if="row.status === 'partial'">
                {{ row.exported_songs }} of {{ row.total_songs }}
              </template>
              <template v-else>{{ row.exported_songs }}</template>
            </td>

            <td class="menu">
              <RowMenu
                :items="menuItems(row)"
                :label="`Actions for ${nameOf(row)}`"
                @select="onMenu(row, $event)"
              />
            </td>
          </tr>

          <tr v-if="expanded.has(row.export_id)" class="details">
            <td></td>
            <td colspan="4">
              <ol :id="`songs-${row.export_id}`" class="song-list">
                <li
                  v-for="item in row.export_items"
                  :key="item.position"
                  :value="item.position"
                  :class="{ missing: item.status !== 'success' }"
                >
                  <span class="file" :class="{ gone: item.title === null }">
                    {{ item.title ?? 'Removed from library' }}
                  </span>
                  <span v-if="item.status !== 'success'" class="reason">
                    Skipped: {{ item.error_message || 'This song could not be exported.' }}
                  </span>
                </li>
              </ol>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    </template>

    <DeleteExportsDialog
      :open="Boolean(deleteTarget)"
      :all="deleteTarget === 'all'"
      :name="deleteTarget && deleteTarget !== 'all' ? (deleteTarget.playlist_name ?? '') : ''"
      :busy="deleting"
      :error="deleteError"
      @confirm="onConfirmDelete"
      @cancel="deleteTarget = null"
    />

    <ExportPlaylistDialog
      :open="Boolean(exportTarget)"
      :playlist="exportTarget"
      @close="exportTarget = null"
    />
  </section>
</template>

<style scoped>
.intro {
  margin: -12px 0 24px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.table-wrap {
  overflow: hidden;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 12px 16px;
  background: var(--c-bg);
  font-size: 13px;
  font-weight: bold;
  color: var(--c-muted);
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: 14px 16px;
  border-top: 1px solid var(--c-border);
  vertical-align: middle;
}

.toggle {
  width: 48px;
  padding-right: 0;
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--c-muted);
  cursor: pointer;
}

.toggle-btn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

.chevron {
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(-45deg);
  transition: transform 150ms ease;
}

tr.open .chevron {
  transform: translateY(-2px) rotate(45deg);
}

.name-cell {
  overflow-wrap: anywhere;
}

.name {
  display: block;
  color: var(--c-text);
  font-weight: bold;
  text-decoration: none;
}

a.name:hover {
  text-decoration: underline;
}

.name.deleted {
  color: var(--c-muted);
  font-style: italic;
}

.file.gone {
  color: var(--c-muted);
  font-style: italic;
}

.sub {
  display: block;
  margin-top: 2px;
  font-size: 13px;
}

.date {
  width: 190px;
  font-size: 14px;
  color: var(--c-muted);
  white-space: nowrap;
}

.songs {
  width: 110px;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}

.menu {
  width: 56px;
  padding-left: 0;
  text-align: right;
}

.details td {
  padding-top: 0;
  border-top: 0;
}

.song-list {
  margin: 0;
  padding: 12px 16px 4px 32px;
  border-radius: 10px;
  background: var(--c-bg);
  font-size: 14px;
}

.song-list li {
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}

.song-list li.missing .file {
  color: var(--c-muted);
  text-decoration: line-through;
}

.reason {
  display: block;
  font-size: 13px;
  color: var(--c-danger);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 24px;
  text-align: center;
}

.empty h2 {
  margin: 0;
  font-size: 20px;
}

.empty p {
  margin: 0 0 12px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (max-width: 640px) {
  th.date,
  td.date {
    display: none;
  }
}
</style>
