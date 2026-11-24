<!--
Message shown when the library has no songs.
-->
<template>
  <div class="app-card empty flex flex-col items-center gap-2 px-6 py-12 text-center">
    <h2 class="m-0 text-[20px]">Your library is empty</h2>
    <p class="app-muted mt-0 mb-3">
      Import songs from YouTube links to start building your library.
    </p>
    <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary">
      Import Music
    </RouterLink>
  </div>
</template>
