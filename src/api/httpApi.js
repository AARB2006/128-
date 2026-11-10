
import { ApiError } from './errors.js'

const API_BASE_URL = 'http://127.0.0.1:8000'

async function request(endpoint, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError(
      0,
      'Could not connect to the backend. Make sure the FastAPI server is running.',
    )
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail

    if (typeof detail === 'object' && detail !== null) {
      throw new ApiError(
        response.status,
        detail.message || 'The request failed.',
        detail.problems || [],
      )
    }

    throw new ApiError(
      response.status,
      typeof detail === 'string' ? detail : 'The request failed.',
    )
  }

  return data
}

export async function listPlaylists() {
  return request('/playlists')
}

export async function importPlaylist(name, urls) {
  return request('/playlists', {
    method: 'POST',
    body: JSON.stringify({ name, urls }),
  })
}

export async function exportPlaylist(playlistId) {
  let response

  try {
    response = await fetch(
      `${API_BASE_URL}/playlists/${playlistId}/export`,
      { method: 'POST' },
    )
  } catch {
    throw new ApiError(
      0,
      'Could not connect to the backend. Make sure the FastAPI server is running.',
    )
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail

    throw new ApiError(
      response.status,
      typeof detail === 'string'
        ? detail
        : detail?.message || 'Could not export this playlist.',
      detail?.problems || [],
    )
  }

  // Read the filename supplied by FastAPI.
  const disposition = response.headers.get('Content-Disposition') || ''

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  const regularMatch = disposition.match(/filename="?([^";]+)"?/i)

  let filename = 'playlist.zip'

  if (utf8Match) {
    filename = decodeURIComponent(utf8Match[1])
  } else if (regularMatch) {
    filename = regularMatch[1]
  }

  // Convert the response into a downloadable browser file.
  const blob = await response.blob()
  const downloadUrl = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename

  document.body.appendChild(link)
  link.click()
  link.remove()

  // Release the temporary browser URL.
  setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000)

  return { filename }
}
