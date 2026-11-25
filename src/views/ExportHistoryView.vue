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
import PageHeader from '@/components/ui/PageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import ListSkeleton from '@/components/ui/ListSkeleton.vue'
import { plural } from '@/lib/format.js'
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

// ---- search and row details ------------------------------------------------------
const query = ref('')
const shown = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? exportsList.value.filter((row) => nameOf(row).toLowerCase().includes(q)) : exportsList.value
})

// "2 of 3 · 1 skipped" for partial exports, "3 songs" otherwise.
function songsLabel(row) {
  if (row.status !== 'partial') return plural(row.exported_songs, 'song')
  const skipped = row.total_songs - row.exported_songs
  return `${row.exported_songs} of ${row.total_songs} · ${skipped} skipped`
}

// The one action worth a button: Download while the file exists, otherwise
// Export again if the playlist still exists.
function mainAction(row) {
  if (!isExpired(row, now.value)) return { key: 'download', label: 'Download' }
  if (row.playlist && !busy.value) return { key: 'again', label: 'Export again' }
  return null
}
</script>

<template>
  <section class="app-page">
    <PageHeader
      title="Export History"
      description="Playlists you exported recently. Each ZIP can be downloaded again for 60 minutes."
    >
      <template v-if="hasRows" #actions>
        <button class="app-btn app-btn-danger min-h-11" type="button" @click="askClearHistory">
          Delete History
        </button>
      </template>
    </PageHeader>

    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <ListSkeleton
      v-if="loading"
      label="Loading your exports"
      :rows="4"
      lead="tile"
      :checkbox="false"
      :columns="['190px', '170px', '180px', '120px']"
    />

    <div v-else-if="loadError" class="app-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <div
      v-else-if="!hasRows"
      class="app-card empty flex flex-col items-center gap-2 px-6 py-12 text-center"
    >
      <h2 class="m-0 text-[20px]">No exports yet</h2>
      <p class="app-muted mt-0 mb-3">Open a playlist and choose Export Playlist.</p>
      <RouterLink :to="{ name: 'playlists' }" class="app-btn app-btn-primary">
        Go to Playlists
      </RouterLink>
    </div>

    <ListCard v-else v-model:query="query" placeholder="Search exports">
      <template #tools>
        <span class="hint pr-1 text-[14px] text-muted phone:hidden">Newest first</span>
      </template>

      <p v-if="!shown.length" class="m-0 px-4 py-10 text-center text-muted">
        No exports match “{{ query }}”.
      </p>
      <table v-else class="w-full min-w-[820px] table-fixed border-collapse">
        <thead>
          <tr>
            <th class="toggle w-12 pr-0"><span class="visually-hidden">Show songs</span></th>
            <th>Playlist</th>
            <th class="w-[190px]">Exported</th>
            <th class="w-[170px]">Songs</th>
            <th class="w-[180px]">File</th>
            <th class="w-[170px]"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>

        <tbody v-for="row in shown" :key="row.export_id">
          <tr :class="{ open: expanded.has(row.export_id) }">
            <td class="toggle pr-0">
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

            <td>
              <div class="flex min-w-0 items-center gap-3.5">
                <span
                  class="inline-flex size-10 shrink-0 items-center justify-center rounded-[10px] bg-accent-soft text-accent-light"
                  aria-hidden="true"
                >
                  <svg
                    class="size-[18px]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M3 6h12M3 12h12M3 18h8" />
                    <path d="M19 4v12" />
                    <circle cx="17" cy="17" r="2.5" />
                  </svg>
                </span>
                <RouterLink
                  v-if="row.playlist"
                  class="name truncate"
                  :to="{ name: 'playlist', params: { playlistId: row.playlist_id } }"
                  :title="row.playlist_name"
                >
                  {{ row.playlist_name }}
                </RouterLink>
                <span v-else class="name deleted">Deleted playlist</span>
              </div>
            </td>

            <td class="text-[14px] whitespace-nowrap text-muted">{{ formatDate(row.created_at) }}</td>

            <td>
              <span
                class="app-pill"
                :class="row.status === 'partial' ? 'app-pill-warning' : 'app-pill-accent'"
              >
                {{ songsLabel(row) }}
              </span>
            </td>

            <td>
              <span v-if="isExpired(row, now)" class="app-pill">Expired</span>
              <span v-else class="app-pill app-pill-success">
                Ready until {{ formatTime(row.file_expires_at) }}
              </span>
            </td>

            <td class="text-right">
              <span class="inline-flex items-center gap-1">
                <button
                  v-if="mainAction(row)"
                  class="app-btn min-h-[34px] px-3 text-[14px]"
                  type="button"
                  @click="onMenu(row, mainAction(row).key)"
                >
                  {{ mainAction(row).label }}
                </button>
                <RowMenu
                  :items="menuItems(row)"
                  :label="`More actions for ${nameOf(row)}`"
                  @select="onMenu(row, $event)"
                />
              </span>
            </td>
          </tr>

          <tr v-if="expanded.has(row.export_id)" class="details">
            <td></td>
            <td colspan="5">
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

      <template #footer>
        <span>{{ plural(exportsList.length, 'export') }}</span>
        <span>Showing {{ shown.length }} of {{ exportsList.length }}</span>
      </template>
    </ListCard>

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
th {
  padding: 12px 16px;
  background: var(--c-head);
  font-size: 12px;
  font-weight: 600;
  color: var(--c-muted);
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

td {
  padding: 12px 16px;
  border-top: 1px solid var(--c-border);
  vertical-align: middle;
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

.name {
  display: block;
  color: var(--c-text);
  font-weight: 600;
  text-decoration: none;
}

a.name:hover {
  text-decoration: underline;
}

.name.deleted {
  color: var(--c-muted);
  font-style: italic;
}

.details td {
  padding-top: 0;
  border-top: 0;
}

.song-list {
  margin: 0;
  padding: 12px 16px 4px 36px;
  border: 1px solid var(--c-border);
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

.file.gone {
  color: var(--c-muted);
  font-style: italic;
}

.reason {
  display: block;
  font-size: 13px;
  color: var(--c-danger);
}

@media (prefers-reduced-motion: reduce) {
  .chevron {
    transition: none;
  }
}
</style>
