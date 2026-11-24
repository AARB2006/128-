<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import SidebarIcon from './SidebarIcon.vue'

defineProps({
  // Only used on small screens, where the sidebar is a slide-out drawer.
  mobileOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const router = useRouter()
const { user, signOut } = useAuth()

// Sidebar state stays local: one boolean doesn't need a store.
const collapsed = ref(false)
const signingOut = ref(false)
const signOutError = ref('')

// Text beside an icon: hidden when the desktop sidebar is collapsed.
const label = 'label desktop:group-[.collapsed]:hidden'

// The collapse (desktop) and close (mobile) buttons.
const iconBtn =
  'icon-btn size-9 cursor-pointer items-center justify-center rounded-[10px] border-0 bg-transparent text-muted hover:bg-hover hover:text-text'

// A navigation link, or the Log Out button. Hovering an item, even the active
// one, shows the hover colour.
const navItem =
  'nav-item font-inherit flex w-full cursor-pointer items-center gap-3 rounded-[10px] border-0 bg-transparent px-3 py-2.5 text-left text-[15px] text-muted no-underline ' +
  '[&.active]:bg-accent [&.active]:text-accent-text hover:not-disabled:bg-hover hover:not-disabled:text-text ' +
  'disabled:cursor-not-allowed disabled:opacity-60 desktop:group-[.collapsed]:justify-center'

const items = [
  { name: 'library', label: 'Music Library', icon: 'music' },
  { name: 'import', label: 'Import Music', icon: 'import' },
  { name: 'playlists', label: 'Playlists', icon: 'list' },
  { name: 'export-history', label: 'Export History', icon: 'export' },
  { name: 'account', label: 'Account', icon: 'user' },
]

const displayName = computed(
  () => user.value?.user_metadata?.full_name || user.value?.email || '',
)
const initial = computed(() => displayName.value.charAt(0).toUpperCase())

async function onSignOut() {
  signingOut.value = true
  signOutError.value = ''
  try {
    await signOut()
    router.replace({ name: 'landing' })
  } catch (e) {
    signOutError.value = e.message || 'Could not log out.'
    signingOut.value = false
  }
}
</script>

<template>
  <!-- Desktop: a sticky column that can collapse to icons only.
       Small screens: an off-canvas drawer opened from the top bar; `invisible`
       keeps its hidden links out of the tab order. -->
  <aside
    class="sidebar group flex w-[240px] shrink-0 flex-col gap-4 border-r border-border bg-surface px-3 py-4 desktop:sticky desktop:top-0 desktop:h-screen desktop:transition-[width] desktop:duration-[160ms] desktop:ease-[ease] desktop:[&.collapsed]:w-[72px] mobile:invisible mobile:fixed mobile:inset-y-0 mobile:left-0 mobile:z-30 mobile:w-[260px] mobile:-translate-x-full mobile:[transition:translate_160ms_ease,visibility_0s_linear_160ms] mobile:[&.open]:visible mobile:[&.open]:translate-none mobile:[&.open]:[transition:translate_160ms_ease,visibility_0s]"
    :class="{ collapsed, open: mobileOpen }"
    aria-label="Main navigation"
  >
    <div
      class="sidebar-head flex items-center justify-between gap-2 px-1 desktop:group-[.collapsed]:justify-center"
    >
      <span
        class="brand inline-flex items-center gap-2.5 text-[18px] font-bold desktop:group-[.collapsed]:hidden"
      >
        <SidebarIcon name="music" />
        <span :class="label">YT-MP3</span>
      </span>

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

    <div class="sidebar-foot mt-auto flex flex-col gap-2 border-t border-border pt-3">
      <div
        v-if="displayName"
        class="user flex items-center gap-2.5 px-3 py-1 desktop:group-[.collapsed]:justify-center desktop:group-[.collapsed]:px-0"
      >
        <span
          class="avatar inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-hover text-[13px] font-bold"
          aria-hidden="true"
        >
          {{ initial }}
        </span>
        <span :class="[label, 'user-name overflow-hidden text-[14px] text-ellipsis whitespace-nowrap']">
          {{ displayName }}
        </span>
      </div>

      <button
        :class="navItem"
        type="button"
        :disabled="signingOut"
        :title="collapsed ? 'Log Out' : undefined"
        aria-label="Log Out"
        @click="onSignOut"
      >
        <SidebarIcon name="logout" />
        <span :class="label">{{ signingOut ? 'Logging out…' : 'Log Out' }}</span>
      </button>

      <p v-if="signOutError" class="sign-out-error m-0 px-3 text-[13px] text-danger" role="alert">
        {{ signOutError }}
      </p>
    </div>
  </aside>
</template>
