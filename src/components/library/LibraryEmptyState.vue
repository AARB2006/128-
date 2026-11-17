<template>
  <div class="app-card empty">
    <h2>Your library is empty</h2>
    <p class="app-muted">
      Import songs from YouTube links to start building your library.
    </p>
    <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary">
      Import Music
    </RouterLink>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 24px;
  text-align: center;
}

h2 {
  margin: 0;
  font-size: 20px;
}

p {
  margin: 0 0 12px;
}
</style>