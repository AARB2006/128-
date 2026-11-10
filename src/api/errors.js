// Every API implementation (mock now, real HTTP later) throws this on failure
// so the UI can treat both the same way.
// `problems` is a list of { line, url, reason } for per-line import errors.
export class ApiError extends Error {
  constructor(status, message, problems = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.problems = problems
  }
}
