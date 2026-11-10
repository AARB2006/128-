// MOCK API: stands in for the FastAPI backend until it is connected.
// Data lives in memory only, so it resets when the page reloads.
//
// Function shapes match the planned endpoints:
//   listLinks()        ~ GET  /links  -> { links, count, max }
//   importLinks(urls)  ~ POST /links  -> { added, skipped, count, max }
//   exportLinks()      ~ POST /export -> { filename, note? }
//
// Failures throw ApiError(status, message, problems), like the real API's
// 4xx responses.

import { ApiError } from './errors.js'

const MAX_LINKS = 10
const LATENCY_MS = 400
const EXPORT_LATENCY_MS = 1500

let store = []
let nextId = 1

const wait = (ms = LATENCY_MS) => new Promise((resolve) => setTimeout(resolve, ms))

// ---- fake "server side" helpers -------------------------------------------

const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/
const HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'])

// Returns https://www.youtube.com/watch?v=ID for any single-video YouTube
// link, or throws Error. Playlist-only and non-YouTube links are rejected.
function canonicalUrl(raw) {
  let text = raw.trim()
  if (!text.includes('://')) text = 'https://' + text

  let url
  try {
    url = new URL(text)
  } catch {
    throw new Error('Not a valid YouTube video link')
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new Error('Not a valid YouTube video link')
  }

  const host = url.hostname.toLowerCase()
  let id = null
  if (host === 'youtu.be') {
    id = url.pathname.replace(/^\//, '').split('/')[0]
  } else if (HOSTS.has(host)) {
    if (url.pathname === '/watch') {
      id = url.searchParams.get('v')
    } else {
      const parts = url.pathname.replace(/^\/|\/$/g, '').split('/')
      if (parts.length >= 2 && ['shorts', 'embed', 'live'].includes(parts[0])) id = parts[1]
    }
  }

  if (!id || !VIDEO_ID.test(id)) throw new Error('Not a valid YouTube video link')
  return `https://www.youtube.com/watch?v=${id}`
}

// The real backend will read the title from YouTube; the mock just invents one.
const fakeTitle = (url) => `Demo title for ${url.slice(-11)}`

// ---- public API -------------------------------------------------------------

export async function listLinks() {
  await wait()
  return {
    links: store.map((link) => ({ ...link })),
    count: store.length,
    max: MAX_LINKS,
  }
}

// `urls` is one entry per textarea line (blank lines allowed and ignored).
// All-or-nothing: any invalid line, or going over the cap, stores nothing.
// Duplicates are skipped and reported rather than treated as errors.
export async function importLinks(urls) {
  await wait()

  const entries = urls
    .map((raw, i) => ({ line: i + 1, raw: raw.trim() }))
    .filter((entry) => entry.raw)
  if (entries.length === 0) throw new ApiError(422, 'Enter at least one link.')

  const existing = new Set(store.map((link) => link.url))
  const seen = new Set()
  const problems = []
  const skipped = []
  const toAdd = []

  for (const { line, raw } of entries) {
    let url
    try {
      url = canonicalUrl(raw)
    } catch (err) {
      problems.push({ line, url: raw, reason: err.message })
      continue
    }
    if (existing.has(url) || seen.has(url)) {
      skipped.push({ line, url: raw, reason: 'Already in the list' })
      continue
    }
    seen.add(url)
    toAdd.push(url)
  }

  if (problems.length) {
    throw new ApiError(422, 'Some links are not valid YouTube video links.', problems)
  }

  const room = MAX_LINKS - store.length
  if (toAdd.length > room) {
    throw new ApiError(
      409,
      `Limit is ${MAX_LINKS} links. You can add ${Math.max(room, 0)} more but submitted ${toAdd.length} new link(s).`,
    )
  }

  const nextPosition = store.reduce((max, link) => Math.max(max, link.position), 0) + 1
  const added = toAdd.map((url, offset) => ({
    id: nextId++,
    url,
    title: fakeTitle(url),
    position: nextPosition + offset,
    created_at: new Date().toISOString(),
  }))
  store = store.concat(added)

  return { added, skipped, count: store.length, max: MAX_LINKS }
}

// The real version will return the zip itself; the mock only simulates the wait.
// Turn the playlist name into a safe file name. The real backend must do this
// too: the name is user input and ends up in file paths.
function safeFileName(name) {
  const cleaned = name
    .replace(/[\\/:*?"<>|\x00-\x1f]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\.+|\.+$/g, '')
  return cleaned || 'playlist'
}

// The real version will return the zip itself; the mock only simulates the wait.
// `playlistName` is optional and falls back to "playlist".
export async function exportLinks(playlistName = '') {
  if (store.length === 0) throw new ApiError(409, 'Nothing to export.')
  await wait(EXPORT_LATENCY_MS)
  return { filename: `${safeFileName(playlistName)}.zip`, note: 'demo mode, no file created' }
}
