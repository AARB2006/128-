/*
Supabase calls to create, read, update and delete playlists and their songs.
*/

import { supabase } from '@/lib/supabase.js'

// Like the library service, nothing here takes an owner id for reading. The
// signed-in session identifies the user and row-level security does the rest.

const CHUNK_SIZE = 100

const PLAYLIST_COLUMNS = 'playlist_id, name, description, created_at'

// Postgres says "invalid input syntax for type uuid" when the URL contains
// something that isn't an id. That just means "no such playlist".
function isBadId(error) {
  return error?.code === '22P02'
}

/**
 * All of the user's playlists, newest first. Each has its song count, its
 * total length in seconds, and when it was last exported (null if never).
 */
export async function getPlaylists() {
  const { data, error } = await supabase
    .from('playlists')
    .select(
      `${PLAYLIST_COLUMNS}, playlist_songs(songs(duration_seconds)), exports(created_at)`,
    )
    // Only exports that produced a file, and only the newest one.
    .in('exports.status', ['completed', 'partial'])
    .order('created_at', { ascending: false })
    .order('created_at', { referencedTable: 'exports', ascending: false })
    .limit(1, { referencedTable: 'exports' })

  if (error) throw error

  return data.map(({ playlist_songs, exports, ...playlist }) => ({
    ...playlist,
    song_count: playlist_songs?.length ?? 0,
    total_seconds: (playlist_songs ?? []).reduce(
      (sum, link) => sum + (Number(link.songs?.duration_seconds) || 0),
      0,
    ),
    last_exported_at: exports?.[0]?.created_at ?? null,
  }))
}

/** One playlist, or null if it doesn't exist (or isn't yours). */
export async function getPlaylist(playlistId) {
  const { data, error } = await supabase
    .from('playlists')
    .select(PLAYLIST_COLUMNS)
    .eq('playlist_id', playlistId)
    .maybeSingle()

  if (isBadId(error)) return null
  if (error) throw error
  return data
}

/** The songs in a playlist, in playlist order. */
export async function getPlaylistSongs(playlistId) {
  const { data, error } = await supabase
    .from('playlist_songs')
    .select('song_id, position, songs(title, source_url, video_id, duration_seconds, date_added)')
    .eq('playlist_id', playlistId)
    .order('position', { ascending: true })

  if (isBadId(error)) return []
  if (error) throw error

  return data
    .filter((row) => row.songs) // can't happen, but never render a half row
    .map(({ song_id, position, songs }) => ({ song_id, position, ...songs }))
}

export async function createPlaylist({ name, description }) {
  // The insert policy requires owner_id to be you, so it has to be sent.
  const { data: sessionData } = await supabase.auth.getSession()
  const ownerId = sessionData.session?.user?.id
  if (!ownerId) throw new Error('You are signed out. Sign in again and retry.')

  const { data, error } = await supabase
    .from('playlists')
    .insert({ owner_id: ownerId, name, description })
    .select(PLAYLIST_COLUMNS)
    .single()

  if (error) throw error
  return data
}

export async function updatePlaylist(playlistId, { name, description }) {
  const { data, error } = await supabase
    .from('playlists')
    .update({ name, description })
    .eq('playlist_id', playlistId)
    .select(PLAYLIST_COLUMNS)
    .maybeSingle()

  if (error) throw error
  if (!data) throw new Error('This playlist no longer exists.')
  return data
}

/**
 * Deletes playlists (their songs stay in the library) and returns the ids that
 * were actually deleted. Like song deletes, RLS skips rows silently.
 */
export async function deletePlaylists(playlistIds) {
  const deleted = []

  for (let i = 0; i < playlistIds.length; i += CHUNK_SIZE) {
    const chunk = playlistIds.slice(i, i + CHUNK_SIZE)

    const { data, error } = await supabase
      .from('playlists')
      .delete()
      .in('playlist_id', chunk)
      .select('playlist_id')

    if (error) throw error
    deleted.push(...data.map((row) => row.playlist_id))
  }

  return deleted
}

/** Takes songs out of one playlist. The songs stay in the library. */
export async function removeSongsFromPlaylist(playlistId, songIds) {
  const removed = []

  for (let i = 0; i < songIds.length; i += CHUNK_SIZE) {
    const chunk = songIds.slice(i, i + CHUNK_SIZE)

    const { data, error } = await supabase
      .from('playlist_songs')
      .delete()
      .eq('playlist_id', playlistId)
      .in('song_id', chunk)
      .select('song_id')

    if (error) throw error
    removed.push(...data.map((row) => row.song_id))
  }

  return removed
}

/**
 * Saves a new order. `songIds` must list every song in the playlist exactly
 * once; the database function renumbers them 1..n in a single transaction.
 */
export async function reorderPlaylistSongs(playlistId, songIds) {
  const { error } = await supabase.rpc('reorder_playlist_songs', {
    p_playlist_id: playlistId,
    p_song_ids: songIds,
  })
  if (error) throw error
}

/**
 * Appends songs to the end of a playlist, skipping any already in it.
 * Returns how many were really added.
 */
export async function addSongsToPlaylist(playlistId, songIds) {
  const { data, error } = await supabase.rpc('add_songs_to_playlist', {
    p_playlist_id: playlistId,
    p_song_ids: songIds,
  })
  if (error) throw error
  return data ?? 0
}