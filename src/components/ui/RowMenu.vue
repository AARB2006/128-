<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'

// The "⋮" menu at the end of a table row. Items are
// { key, label, disabled?, danger?, title? }; choosing one emits `select`.
// The menu is positioned with `fixed` so the table's rounded, clipped edge
// can never cut it off.
const props = defineProps({
  items: { type: Array, required: true },
  label: { type: String, default: 'More actions' },
})
const emit = defineEmits(['select'])

const open = ref(false)
const button = ref(null)
const menu = ref(null)
const position = ref({ top: 0, left: 0 })

let openScrollY = 0

const ITEM_HEIGHT = 40
const MENU_WIDTH = 200

function place() {
  const rect = button.value.getBoundingClientRect()
  const height = props.items.length * ITEM_HEIGHT + 8
  const fitsBelow = rect.bottom + height + 8 < window.innerHeight

  position.value = {
    top: fitsBelow ? rect.bottom + 4 : rect.top - height - 4,
    left: Math.max(8, Math.min(rect.right - MENU_WIDTH, window.innerWidth - MENU_WIDTH - 8)),
  }
}

async function openMenu() {
  place()
  openScrollY = window.scrollY
  open.value = true
  document.addEventListener('pointerdown', onOutside, true)
  document.addEventListener('dragstart', closeMenu, true)
  window.addEventListener('scroll', onScroll, true)
  window.addEventListener('resize', closeMenu)
  await nextTick()
  menu.value?.querySelector('button:not(:disabled)')?.focus()
}

function closeMenu() {
  if (!open.value) return
  open.value = false
  document.removeEventListener('pointerdown', onOutside, true)
  document.removeEventListener('dragstart', closeMenu, true)
  window.removeEventListener('scroll', onScroll, true)
  window.removeEventListener('resize', closeMenu)
}

// Scrolling would leave the menu floating in the wrong place, so it closes.
// A scroll event that arrives late, from the browser bringing the button into
// view just before it was tapped, doesn't count: the page hasn't moved since.
function onScroll(event) {
  const isPage = event.target === document || event.target === document.documentElement
  if (isPage && Math.abs(window.scrollY - openScrollY) < 2) return
  closeMenu()
}

function onOutside(event) {
  if (menu.value?.contains(event.target) || button.value?.contains(event.target)) return
  closeMenu()
}

function toggle() {
  if (open.value) closeMenu()
  else openMenu()
}

function choose(item) {
  if (item.disabled) return
  closeMenu()
  button.value?.focus()
  emit('select', item.key)
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    event.stopPropagation()
    closeMenu()
    button.value?.focus()
    return
  }
  if (event.key === 'Tab') {
    closeMenu()
    return
  }
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return

  event.preventDefault()
  const buttons = [...menu.value.querySelectorAll('button:not(:disabled)')]
  const at = buttons.indexOf(document.activeElement)
  const next = event.key === 'ArrowDown' ? at + 1 : at - 1
  buttons[(next + buttons.length) % buttons.length]?.focus()
}

onBeforeUnmount(closeMenu)
</script>

<template>
  <button
    ref="button"
    class="dots"
    type="button"
    aria-haspopup="menu"
    :aria-expanded="open"
    :aria-label="label"
    @click="toggle"
  >
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <circle cx="12" cy="5" r="1.8" fill="currentColor" />
      <circle cx="12" cy="12" r="1.8" fill="currentColor" />
      <circle cx="12" cy="19" r="1.8" fill="currentColor" />
    </svg>
  </button>

  <Teleport to="body">
    <div
      v-if="open"
      ref="menu"
      class="row-menu"
      role="menu"
      :aria-label="label"
      :style="{ top: position.top + 'px', left: position.left + 'px' }"
      @keydown="onKeydown"
    >
      <button
        v-for="item in items"
        :key="item.key"
        class="item"
        :class="{ danger: item.danger }"
        type="button"
        role="menuitem"
        :disabled="item.disabled"
        :title="item.title"
        @click="choose(item)"
      >
        {{ item.label }}
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.dots {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--c-muted);
  cursor: pointer;
}

.dots:hover,
.dots[aria-expanded='true'] {
  background: var(--c-hover);
  color: var(--c-text);
}
</style>

<!-- The menu is teleported to <body>, outside .app-shell, so it carries its own
     colours instead of inheriting the app's CSS variables. -->
<style>
.row-menu {
  position: fixed;
  z-index: 50;
  box-sizing: border-box;
  width: 200px;
  padding: 4px;
  border: 1px solid #e3e6ea;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.14);
}

.row-menu .item {
  display: block;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #111827;
  font: inherit;
  font-size: 15px;
  text-align: left;
  cursor: pointer;
}

.row-menu .item:hover:not(:disabled),
.row-menu .item:focus-visible {
  background: #f0f2f5;
  outline: none;
}

.row-menu .item.danger {
  color: #b42318;
}

.row-menu .item:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>