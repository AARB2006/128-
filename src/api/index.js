// The one place the UI imports its data layer from.
// For now this is the in-memory mock. When the FastAPI backend is connected,
// point this line at the real implementation (same function names and shapes).
export * from './mockApi.js'
