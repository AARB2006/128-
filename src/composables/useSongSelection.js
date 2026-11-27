/*
Tracks which rows are ticked in a list.
*/

import { computed, ref, watch } from 'vue'

// Tracks which songs are ticked. Only songs that match the current search can
// stay selected, so a search or a delete can never leave a hidden song selected.
//
// With paging, pass the current page as `pageSongs`: ticks then survive moving
// between pages, and the header checkbox ticks or unticks just this page.
export function useSongSelection(visibleSongs, idKey = 'song_id', pageSongs = visibleSongs) {
  const selectedIds = ref(new Set())

  const visibleIds = computed(() => visibleSongs.value.map((item) => item[idKey]))
  const pageIds = computed(() => pageSongs.value.map((item) => item[idKey]))
  const count = computed(() => selectedIds.value.size)
  const allSelected = computed(
    () =>
      pageIds.value.length > 0 && pageIds.value.every((id) => selectedIds.value.has(id)),
  )
  const someSelected = computed(
    () => !allSelected.value && pageIds.value.some((id) => selectedIds.value.has(id)),
  )

  function toggle(id) {
    const next = new Set(selectedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selectedIds.value = next
  }

  // Ticks every row on this page, or unticks them if they're all ticked.
  // Ticks on other pages are kept.
  function toggleAll() {
    const next = new Set(selectedIds.value)
    if (allSelected.value) pageIds.value.forEach((id) => next.delete(id))
    else pageIds.value.forEach((id) => next.add(id))
    selectedIds.value = next
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