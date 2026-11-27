<!--
Navigation sidebar (collapsible; a drawer on small screens).
-->
<script setup>
import { ref } from 'vue'
import SidebarIcon from './SidebarIcon.vue'
import AccountMenu from './AccountMenu.vue'
import logoUrl from '@/assets/brand/ytmp3-logo.svg'
import iconUrl from '@/assets/brand/ytmp3-icon.svg'

defineProps({
  // Only used on small screens, where the sidebar is a slide-out drawer.
  mobileOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

// Sidebar state stays local: one boolean doesn't need a store.
const collapsed = ref(false)

// Text beside an icon: hidden when the desktop sidebar is collapsed.
const label = 'label desktop:group-[.collapsed]:hidden'

// The collapse (desktop) and close (mobile) buttons.
const iconBtn =
  'icon-btn size-9 cursor-pointer items-center justify-center rounded-[10px] border-0 bg-transparent text-muted hover:bg-hover hover:text-text'

// A navigation link. Hovering an item, even the active
// one, shows the hover colour.
const navItem =
  'nav-item font-inherit flex w-full cursor-pointer items-center gap-3 rounded-[10px] border-0 bg-transparent px-3 py-2.5 text-left text-[15px] text-muted no-underline ' +
  'hover:not-disabled:bg-hover hover:not-disabled:text-text ' +
  '[&.active]:bg-accent-soft [&.active]:font-semibold [&.active]:text-text [&.active_svg]:text-accent-light ' +
  'disabled:cursor-not-allowed disabled:opacity-60 desktop:group-[.collapsed]:justify-center'

const items = [
  { name: 'library', label: 'Music Library', icon: 'music' },
  { name: 'import', label: 'Import Music', icon: 'import' },
  { name: 'playlists', label: 'Playlists', icon: 'list' },
  { name: 'export-history', label: 'Export History', icon: 'export' },
]
// Log out lives in the account menu at the bottom.
</script>

<template>
  <!-- Desktop: a sticky column that can collapse to icons only.
       Small screens: an off-canvas drawer opened from the top bar; `invisible`
       keeps its hidden links out of the tab order. -->
  <aside
    class="sidebar group flex w-[240px] shrink-0 flex-col gap-4 border-r border-border bg-head px-3 py-4 desktop:sticky desktop:top-0 desktop:h-screen desktop:transition-[width] desktop:duration-[160ms] desktop:ease-[ease] desktop:[&.collapsed]:w-[72px] mobile:invisible mobile:fixed mobile:inset-y-0 mobile:left-0 mobile:z-30 mobile:w-[260px] mobile:-translate-x-full mobile:[transition:translate_160ms_ease,visibility_0s_linear_160ms] mobile:[&.open]:visible mobile:[&.open]:translate-none mobile:[&.open]:[transition:translate_160ms_ease,visibility_0s]"
    :class="{ collapsed, open: mobileOpen }"
    aria-label="Main navigation"
  >
    <div
      class="sidebar-head flex items-center justify-between gap-2 px-1 desktop:group-[.collapsed]:flex-col desktop:group-[.collapsed]:justify-center"
    >
      <!-- The full logo; collapsed, just its icon. -->
      <RouterLink
        :to="{ name: 'library' }"
        class="brand inline-flex items-center rounded-[8px] desktop:group-[.collapsed]:hidden"
        aria-label="YT-MP3, go to Music Library"
      >
        <img :src="logoUrl" alt="" class="block h-[24px] w-auto" />
      </RouterLink>
      <img
        :src="iconUrl"
        alt=""
        class="brand-icon hidden size-8 desktop:group-[.collapsed]:block"
      />

      <button
        :class="[iconBtn, 'collapse-btn inline-flex mobile:hidden']"
        type="button"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-expanded="!collapsed"
        @click="collapsed = !collapsed"
      >
        <SidebarIcon name="chevron" :class="{ 'flipped rotate-180': collapsed }" />
      </button>

      <button
        :class="[iconBtn, 'close-btn hidden mobile:inline-flex']"
        type="button"
        aria-label="Close navigation"
        @click="emit('close')"
      >
        <SidebarIcon name="close" />
      </button>
    </div>

    <nav class="nav flex flex-col gap-1">
      <RouterLink
        v-for="item in items"
        :key="item.name"
        :to="{ name: item.name }"
        :class="navItem"
        active-class="active"
        :title="collapsed ? item.label : undefined"
        :aria-label="item.label"
      >
        <SidebarIcon :name="item.icon" />
        <span :class="label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-foot mt-auto border-t border-border pt-3">
      <AccountMenu />
    </div>
  </aside>
</template>
