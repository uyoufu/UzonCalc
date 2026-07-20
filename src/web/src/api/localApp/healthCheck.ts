import { localHttpClient } from './localHttpClient'

let localAppAvailable: boolean | null = null

export async function isLocalAppAvailable(): Promise<boolean> {
  if (localAppAvailable !== null) return localAppAvailable

  localAppAvailable = await localHttpClient
    .get<boolean>('/health-check', {
      timeout: 1000,
      stopNotifyError: true
    })
    .then((response) => response.data === true)
    .catch(() => false)

  return localAppAvailable
}

