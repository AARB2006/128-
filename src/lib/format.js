/*
Small display formatters shared by the list pages.
*/

/** 75 -> "1:15", 3725 -> "1:02:05". Unknown or negative -> "–". */
export function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '–'
  const total = Math.round(seconds)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = String(total % 60).padStart(2, '0')
  return h ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`
}

/** The sum of the songs' lengths, formatted like formatDuration. */
export function totalDuration(songs) {
  return formatDuration(
    songs.reduce((sum, song) => sum + (Number(song.duration_seconds) || 0), 0),
  )
}

/** "Nov 18, 2026" */
export function formatDay(value) {
  return value ? new Date(value).toLocaleDateString(undefined, { dateStyle: 'medium' }) : ''
}

/** "youtube.com/watch?v=abc": the address without "https://www.". */
export function shortUrl(url) {
  return String(url ?? '').replace(/^https?:\/\/(www\.)?/i, '')
}

/** "1 song", "3 songs" */
export function plural(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`
}
