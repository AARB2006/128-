import { computed, onScopeDispose, ref, watch } from 'vue'

const DEBOUNCE_MS = 250

// Debounced substring search over the songs already in memory.
export function useSongSearch(songs) {
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

    return songs.value.filter(
      (song) =>
        song.title.toLowerCase().includes(term) ||
        song.source_url.toLowerCase().includes(term),
    )
  })

  return { query, results }
}