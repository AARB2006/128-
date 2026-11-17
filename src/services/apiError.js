// Thrown for any failed call to the import server, so the UI can show
// `error.message` without caring what went wrong.
export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}