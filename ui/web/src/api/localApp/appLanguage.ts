import { isLocalAppAvailable } from './healthCheck'
import { localHttpClient } from './localHttpClient'

interface AppLanguageResponse {
  language: string
}

export async function getAppLanguage (): Promise<string | null> {
  if (!await isLocalAppAvailable()) return null

  const response = await localHttpClient.get<AppLanguageResponse>('/language')
  return response.data.language || null
}

export async function setAppLanguage (language: string): Promise<string> {
  const response = await localHttpClient.post<AppLanguageResponse, { language: string }>('/language', {
    data: {
      language
    }
  })
  return response.data.language || language
}

