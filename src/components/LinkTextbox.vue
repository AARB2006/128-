<template>
  <section class="link-input" aria-label="YouTube link input">
    <label class="visually-hidden" for="youtube-links">YouTube video links</label>

    <textarea
      id="youtube-links"
      placeholder="enter links here..."
      spellcheck="false"
    ></textarea>

    <span class="link-count">0/10</span>
  </section>
</template>

<style scoped>
.link-input {
  position: relative;
  width: 100%;
  height: min(52vh, 540px);
  min-height: 300px;
  border: 3px solid #111;
  background: #fff;
}

textarea {
  display: block;
  width: 100%;
  height: 100%;
  padding: 15px 18px 52px;
  resize: vertical;
  border: 0;
  outline: 0;
  color: #111;
  background: transparent;
  font: inherit;
  font-size: 21px;
  line-height: 1.5;
}

textarea::placeholder {
  color: #525151;
  opacity: 1;
}

.link-count {
  position: absolute;
  right: 17px;
  bottom: 10px;
  padding: 2px 0 0 8px;
  background: #fff;
  font-size: 21px;
  font-variant-numeric: tabular-nums;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 640px) {
  .link-input {
    height: 52vh;
    min-height: 260px;
  }

  textarea {
    padding: 12px 13px 48px;
    font-size: 17px;
  }

  .link-count {
    right: 12px;
    font-size: 17px;
  }
}
</style>
