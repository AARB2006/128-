<!--
One row of the playlists table, with its actions menu.
-->
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import RowMenu from '@/components/ui/RowMenu.vue'
import { useExportJob } from '@/composables/useExportJob.js'
import { formatDay, formatDuration } from '@/lib/format.js'

const props = defineProps({
  playlist: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'export'])

const router = useRouter()

// Shared by every cell (each adds its own left padding). The row is a `group`,
// so cells turn blue when it's selected.
const cell = 'border-t border-border py-3 pr-4 align-middle group-[.selected]:bg-selected'

const created = computed(() => formatDay(props.playlist.created_at))
const length = computed(() => formatDuration(props.playlist.total_seconds ?? 0))
const exported = computed(() => formatDay(props.playlist.last_exported_at))

const { busy: exportBusy } = useExportJob()

const menuItems = computed(() => {
  const empty = props.playlist.song_count === 0
  return [
    { key: 'edit', label: 'Edit playlist' },
    {
      key: 'export',
      label: 'Export playlist',
      disabled: empty || exportBusy.value,
      title: empty
        ? 'Add songs to export this playlist'
        : exportBusy.value
          ? 'Another export is running'
          : undefined,
    },
  ]
})

function onMenu(key) {
  if (key === 'edit') {
    router.push({ name: 'playlist', params: { playlistId: props.playlist.playlist_id } })
  }
  if (key === 'export') emit('export', props.playlist)
}
</script>

<template>
  <tr class="group" :class="{ selected }">
    <td :class="[cell, 'check w-11 pl-4 pr-0']">
      <input
        class="size-[18px] cursor-pointer"
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${playlist.name}`"
        @change="emit('toggle', playlist.playlist_id)"
      />
    </td>

    <td :class="[cell, 'name-cell pl-4']">
      <div class="flex min-w-0 items-center gap-3.5">
        <span
          class="tile inline-flex size-10 shrink-0 items-center justify-center rounded-[10px] bg-accent-soft text-accent-light"
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
        <div class="min-w-0">
          <RouterLink
            class="name block truncate font-semibold text-text no-underline hover:underline"
            :to="{ name: 'playlist', params: { playlistId: playlist.playlist_id } }"
            :title="playlist.name"
          >
            {{ playlist.name }}
          </RouterLink>
          <span
            v-if="playlist.description"
            class="description mt-0.5 block truncate text-[13px] text-muted"
          >
            {{ playlist.description }}
          </span>
        </div>
      </div>
    </td>

    <td :class="[cell, 'songs w-[90px] pl-4 text-[14px] tabular-nums']">
      {{ playlist.song_count }}
    </td>

    <td :class="[cell, 'length w-[90px] pl-4 text-[14px] text-muted tabular-nums phone:hidden']">
      {{ length }}
    </td>

    <td :class="[cell, 'created w-[140px] pl-4 text-[14px] whitespace-nowrap text-muted phone:hidden']">
      {{ created }}
    </td>

    <td :class="[cell, 'exported w-[150px] pl-4 text-[14px] whitespace-nowrap text-muted mobile:hidden']">
      <span v-if="playlist.last_exported_at">{{ exported }}</span>
      <span v-else class="app-pill">Never</span>
    </td>

    <td :class="[cell, 'menu w-14 pl-0 text-right']">
      <RowMenu :items="menuItems" :label="`Actions for ${playlist.name}`" @select="onMenu" />
    </td>
  </tr>
</template>
