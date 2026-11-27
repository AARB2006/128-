<!--
The signed-in person at the bottom of the sidebar. Clicking it opens a menu
with "Log out".
-->
<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useAuth } from '@/composables/useAuth.js'
import { useSignOut } from '@/composables/useSignOut.js'
import SidebarIcon from './SidebarIcon.vue'

// When the desktop sidebar is collapsed to icons (its `group` has the
// `collapsed` class), only the avatar shows and the menu opens to the side.

const { user } = useAuth()
const { signingOut, signOutNow } = useSignOut()

const name = computed(
  () => user.value?.user_metadata?.full_name || user.value?.email || 'Account',
)
const email = computed(() => user.value?.email ?? '')
const initial = computed(() => name.value.charAt(0).toUpperCase())

const open = ref(false)
const root = ref(null)
const trigger = ref(null)
const menu = ref(null)

const menuItems = () => [...(menu.value?.querySelectorAll('[role="menuitem"]') ?? [])]

async function openMenu() {
  open.value = true
  await nextTick()
  menuItems()[0]?.focus()
}

function close({ returnFocus = true } = {}) {
  open.value = false
  if (returnFocus) trigger.value?.focus()
}

function toggle() {
  if (open.value) close()
  else openMenu()
}

// Arrow keys move between items; Escape closes; Tab leaves the menu.
function onKeydown(event) {
  const list = menuItems()
  const index = list.indexOf(document.activeElement)
  const focusAt = (i) => list[(i + list.length) % list.length]?.focus()

  if (event.key === 'Escape') {
    event.preventDefault()
    close()
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    focusAt(index + 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    focusAt(index - 1)
  } else if (event.key === 'Home') {
    event.preventDefault()
    focusAt(0)
  } else if (event.key === 'End') {
    event.preventDefault()
    focusAt(list.length - 1)
  } else if (event.key === 'Tab') {
    close({ returnFocus: false })
  }
}

// A click anywhere else closes the menu.
function onPointerDown(event) {
  if (!root.value?.contains(event.target)) close({ returnFocus: false })
}

watch(open, (isOpen) => {
  if (isOpen) document.addEventListener('pointerdown', onPointerDown)
  else document.removeEventListener('pointerdown', onPointerDown)
})
onBeforeUnmount(() => document.removeEventListener('pointerdown', onPointerDown))

function logOut() {
  close({ returnFocus: false })
  signOutNow()
}

const item =
  'item font-inherit flex h-10 w-full cursor-pointer items-center gap-3 rounded-[8px] border-0 bg-transparent px-3 text-left text-[15px] text-text ' +
  'hover:bg-hover focus-visible:bg-hover focus-visible:outline-none disabled:cursor-wait disabled:opacity-60'
</script>

<template>
  <div ref="root" class="account-menu relative">
    <Transition
      enter-active-class="transition-[opacity,translate,scale] duration-150 ease-out motion-reduce:transition-none"
      enter-from-class="translate-y-1 scale-[0.98] opacity-0"
      leave-active-class="transition-[opacity,translate,scale] duration-100 ease-in motion-reduce:transition-none"
      leave-to-class="translate-y-1 scale-[0.98] opacity-0"
    >
      <div
        v-if="open"
        id="account-menu"
        ref="menu"
        class="menu absolute bottom-full left-0 z-40 mb-2 w-full min-w-[232px] origin-bottom rounded-[12px] border border-border bg-surface p-1 shadow-[0_12px_32px_rgba(0,0,0,0.55)] desktop:group-[.collapsed]:bottom-0 desktop:group-[.collapsed]:left-full desktop:group-[.collapsed]:mb-0 desktop:group-[.collapsed]:ml-6 desktop:group-[.collapsed]:w-auto desktop:group-[.collapsed]:origin-bottom-left"
        role="menu"
        aria-label="Account"
        @keydown="onKeydown"
      >
        <div class="who mb-1 border-b border-border px-3 pt-2 pb-2.5">
          <p class="m-0 truncate text-[14px] font-semibold">{{ name }}</p>
          <p v-if="email" class="m-0 truncate text-[13px] text-muted">{{ email }}</p>
        </div>

        <button
          :class="item"
          type="button"
          role="menuitem"
          :disabled="signingOut"
          @click="logOut"
        >
          <SidebarIcon name="logout" />
          Log out
        </button>
      </div>
    </Transition>

    <button
      ref="trigger"
      class="trigger font-inherit flex w-full cursor-pointer items-center gap-2.5 rounded-[10px] border-0 bg-transparent px-2.5 py-2 text-left text-text hover:bg-hover aria-expanded:bg-hover desktop:group-[.collapsed]:justify-center desktop:group-[.collapsed]:px-0"
      type="button"
      aria-haspopup="menu"
      :aria-expanded="open"
      aria-controls="account-menu"
      :aria-label="`Account: ${name}`"
      @click="toggle"
      @keydown.down.prevent="openMenu"
    >
      <span
        class="avatar inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-[13px] font-bold text-accent-text"
        aria-hidden="true"
      >
        {{ initial }}
      </span>
      <span class="min-w-0 flex-1 desktop:group-[.collapsed]:hidden">
          <span class="block truncate text-[14px] font-medium">{{ name }}</span>
        <span v-if="email" class="block truncate text-[12px] text-muted">{{ email }}</span>
      </span>
      <!-- Up/down chevrons: this opens a menu. -->
      <svg
        class="size-4 shrink-0 text-muted desktop:group-[.collapsed]:hidden"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
        <path d="M8 9l4-4 4 4M8 15l4 4 4-4" />
      </svg>
    </button>
  </div>
</template>
