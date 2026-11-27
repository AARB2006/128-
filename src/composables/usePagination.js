/*
Splits a list that is already in memory into pages.
*/

import { computed, ref, watch } from 'vue'

export const PAGE_SIZE = 20

// `items` is a ref or computed list. Returns the current page's items and the
// numbers the pager and footer need. Page numbers start at 1.
export function usePagination(items, pageSize = PAGE_SIZE) {
  const page = ref(1)

  const total = computed(() => items.value.length)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

  // Deleting songs can leave you past the last page: step back to it.
  watch(pageCount, (count) => {
    if (page.value > count) page.value = count
  })

  const start = computed(() => (page.value - 1) * pageSize)
  const pageItems = computed(() => items.value.slice(start.value, start.value + pageSize))

  // "21–40" in "Showing 21–40 of 57" (0–0 when the list is empty).
  const firstShown = computed(() => (total.value ? start.value + 1 : 0))
  const lastShown = computed(() => Math.min(start.value + pageSize, total.value))

  function goTo(n) {
    page.value = Math.min(Math.max(1, n), pageCount.value)
  }

  return { page, pageCount, pageItems, total, firstShown, lastShown, goTo }
}
