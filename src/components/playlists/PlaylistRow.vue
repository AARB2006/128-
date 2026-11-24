<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import RowMenu from '@/components/ui/RowMenu.vue'
import { useExportJob } from '@/composables/useExportJob.js'

const props = defineProps({
  playlist: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'export'])

const router = useRouter()

// Shared by every cell (each adds its own left padding). The row is a `group`,
// so cells turn blue when it's selected.
const cell = 'border-t border-border py-3.5 pr-4 align-middle group-[.selected]:bg-selected'

const created = computed(() =>
  new Date(props.playlist.created_at).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }),
)

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
    <td :class="[cell, 'check w-12 pl-4']">
      <input
        class="size-[18px] cursor-pointer"
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${playlist.name}`"
        @change="$emit('toggle', playlist.playlist_id)"
      />
    </td>

    <td :class="[cell, 'name-cell pl-4 wrap-anywhere']">
      <RouterLink
        class="name block font-bold text-text no-underline hover:underline"
        :to="{ name: 'playlist', params: { playlistId: playlist.playlist_id } }"
      >
        {{ playlist.name }}
      </RouterLink>
      <span
        v-if="playlist.description"
        class="description mt-0.5 line-clamp-1 text-[13px] text-muted"
      >
        {{ playlist.description }}
      </span>
    </td>

    <td :class="[cell, 'created w-[190px] pl-4 text-[14px] whitespace-nowrap text-muted phone:hidden']">
      {{ created }}
    </td>
    <td :class="[cell, 'songs w-[130px] pl-4 text-[14px] tabular-nums']">
      {{ playlist.song_count }}
    </td>

    <td :class="[cell, 'menu w-14 pl-0 text-right']">
      <RowMenu :items="menuItems" :label="`Actions for ${playlist.name}`" @select="onMenu" />
    </td>
  </tr>
</template>
