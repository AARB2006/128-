/*
Debounced search over a list that is already in memory.
*/

import { computed, onScopeDispose, ref, watch } from 'vue'

const DEBOUNCE_MS = 250

// Debounced substring search over the items already in memory. `fields` are
// the text properties to look in: song title and link by default, or name and
// description for playlists.
export function useSongSearch(songs, fields = ['title', 'source_url']) {
  const query = ref('')
  const debouncedQuery = ref('')

  let timeout

  watch(query, (value) => {
    clearTimeout(timeout)

    // Clearing the box shows everything straight away.
    if (!value.trim()) {
      debouncedQuery.value = ''
      return
    }

    timeout = setTimeout(() => {
      debouncedQuery.value = value.trim().toLowerCase()
    }, DEBOUNCE_MS)
  })

  // Don't leave a timer running after the page is closed.
  onScopeDispose(() => clearTimeout(timeout))

  const results = computed(() => {
    const term = debouncedQuery.value
    if (!term) return songs.value

    return songs.value.filter((item) =>
      fields.some((field) => (item[field] ?? '').toLowerCase().includes(term)),
    )
  })

  return { query, results }
}