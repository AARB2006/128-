/*
Tracks which rows are ticked in a list.
*/

import { computed, ref, watch } from 'vue'

// Tracks which songs are ticked. Only songs currently shown can stay selected,
// so a search or a delete can never leave a hidden song selected.
export function useSongSelection(visibleSongs, idKey = 'song_id') {
  const selectedIds = ref(new Set())

  const visibleIds = computed(() => visibleSongs.value.map((item) => item[idKey]))
  const count = computed(() => selectedIds.value.size)
  const allSelected = computed(
    () =>
      visibleIds.value.length > 0 &&
      visibleIds.value.every((id) => selectedIds.value.has(id)),
  )
  const someSelected = computed(() => count.value > 0 && !allSelected.value)

  function toggle(id) {
    const next = new Set(selectedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selectedIds.value = next
  }

  function toggleAll() {
    selectedIds.value = allSelected.value ? new Set() : new Set(visibleIds.value)
  }

  function clear() {
    selectedIds.value = new Set()
  }

  watch(visibleIds, (ids) => {
    const visible = new Set(ids)
    const kept = [...selectedIds.value].filter((id) => visible.has(id))
    if (kept.length !== selectedIds.value.size) selectedIds.value = new Set(kept)
  })

  return { selectedIds, count, allSelected, someSelected, toggle, toggleAll, clear }
}