<!--
Landing page with Google sign-in: the violet brand panel and the sign-in panel.
-->
<script setup>
import { ref } from 'vue'
import { useAuth } from '@/composables/useAuth.js'
import logoUrl from '@/assets/brand/ytmp3-logo-on-violet.svg'
import googleLogoUrl from '@/assets/brand/google-g.svg'

const { signInWithGoogle } = useAuth()
const busy = ref(false)
const error = ref('')

async function onContinue() {
  busy.value = true
  error.value = ''
  try {
    // On success the browser leaves for Google, so there is nothing to do after.
    await signInWithGoogle()
  } catch (e) {
    error.value = e.message || 'Could not start Google sign-in.'
    busy.value = false
  }
}

// The three things the app does, shown as cards on the violet panel.
const features = [
  {
    title: 'Import',
    text: 'Paste up to ten YouTube links at once.',
    icon: 'M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7',
  },
  {
    title: 'Playlists',
    text: 'Group songs and drag them into order.',
    icon: 'M3 6h12M3 12h12M3 18h8M19 4v12',
    circle: true,
  },
  {
    title: 'Export',
    text: 'Download a playlist as numbered MP3s.',
    icon: 'M12 3v12M7 10l5 5 5-5M4 17v3h16v-3',
  },
]
</script>

<template>
  <!-- The landing page sits outside .app-shell, so it uses literal colours that
       match the app's tokens: violet #6d5bff, page #0f0f0f, light violet #a99cff. -->
  <main
    class="landing flex min-h-screen flex-wrap bg-[#0f0f0f] font-[family-name:Inter,system-ui,sans-serif] text-[#f5f5f5] [color-scheme:dark]"
  >
    <!-- Brand side -->
    <section
      class="brand relative flex min-w-0 flex-[1_1_560px] flex-col justify-center overflow-hidden bg-[#6d5bff] p-16 mobile:p-10 phone:px-6 phone:py-10"
      aria-labelledby="tagline"
    >
      <!-- The logo's list lines, scaled up as a quiet pattern that drifts slowly.
           Plain divs animated with `transform` only (see landing-drift in
           app.css): no JavaScript, no repainting. Still for reduced motion. -->
      <div
        class="pattern pointer-events-none absolute -right-[120px] -bottom-10 h-[360px] w-[560px]"
        aria-hidden="true"
      >
        <span
          class="absolute top-0 left-0 h-[72px] w-[420px] rounded-full bg-white/[0.08] [--drift-x:-56px] [--drift-y:6px] animate-[landing-drift_19s_ease-in-out_infinite_alternate] motion-reduce:animate-none"
        ></span>
        <span
          class="absolute top-[144px] left-0 h-[72px] w-[420px] rounded-full bg-white/[0.08] [--drift-x:40px] [--drift-y:-8px] animate-[landing-drift_24s_ease-in-out_-6s_infinite_alternate] motion-reduce:animate-none"
        ></span>
        <span
          class="absolute top-[288px] left-0 h-[72px] w-[260px] rounded-full bg-white/[0.08] [--drift-x:-32px] [--drift-y:4px] animate-[landing-drift_29s_ease-in-out_-12s_infinite_alternate] motion-reduce:animate-none"
        ></span>
      </div>

      <div class="relative flex max-w-[600px] flex-col gap-10 phone:gap-7">
        <img :src="logoUrl" alt="YT-MP3" class="block h-auto w-[min(420px,100%)]" />

        <p
          id="tagline"
          class="m-0 font-display text-[44px] leading-[1.08] font-extrabold tracking-[-0.025em] text-white phone:text-[32px]"
        >
          Listen to the music you love. Offline.
        </p>

        <ul class="features m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(160px,1fr))] gap-3 p-0">
          <li
            v-for="feature in features"
            :key="feature.title"
            class="group/card flex flex-col gap-3.5 rounded-[16px] border border-white/20 bg-white/10 p-5 text-white transition-[translate,background-color,border-color] duration-200 ease-out hover:-translate-y-1 hover:border-white/40 hover:bg-white/[0.16] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
          >
            <span
              class="inline-flex size-10 items-center justify-center rounded-[12px] bg-white text-[#6d5bff] transition-transform duration-200 ease-out group-hover/card:scale-110 motion-reduce:transition-none motion-reduce:group-hover/card:scale-100"
              aria-hidden="true"
            >
              <svg
                class="size-[22px]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path :d="feature.icon" />
                <circle v-if="feature.circle" cx="17" cy="17" r="2.5" />
              </svg>
            </span>
            <span class="flex flex-col gap-1">
              <strong class="text-[16px] font-semibold">{{ feature.title }}</strong>
              <span class="text-[14px] leading-[1.45] text-white/85">{{ feature.text }}</span>
            </span>
          </li>
        </ul>
      </div>
    </section>

    <!-- Sign-in side -->
    <section
      class="sign-in flex min-w-0 flex-[1_1_480px] flex-col items-center justify-center p-16 mobile:p-10 phone:px-6 phone:py-12"
      aria-labelledby="title"
    >
      <div class="flex w-full max-w-[400px] flex-col gap-7">
        <h1
          id="title"
          class="m-0 font-display text-[48px] leading-[1.05] font-extrabold tracking-[-0.03em] text-white phone:text-[36px]"
        >
          Start your personal <span class="text-[#a99cff]">playlist</span> today!
        </h1>

        <!-- Google's dark sign-in button: the page's own background, a grey
             outline and the official "G". It grows slightly on hover. -->
        <button
          class="flex h-[52px] w-full cursor-pointer items-center justify-center gap-3 rounded-full border border-[#8e918f] bg-[#0f0f0f] px-6 font-[family-name:Inter,system-ui,sans-serif] text-[16px] font-medium text-[#e3e3e3] transition-[scale,border-color] duration-200 ease-out enabled:hover:scale-[1.04] enabled:hover:border-white enabled:active:scale-[0.98] focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#a99cff] disabled:cursor-wait disabled:opacity-70 motion-reduce:transition-none motion-reduce:enabled:hover:scale-100"
          type="button"
          :disabled="busy"
          @click="onContinue"
        >
          <img :src="googleLogoUrl" alt="" class="block size-5" />
          {{ busy ? 'Redirecting…' : 'Continue with Google' }}
        </button>

        <p v-if="error" class="error m-0 text-[14px] text-[#f97066]" role="alert">{{ error }}</p>
      </div>
    </section>
  </main>
</template>
