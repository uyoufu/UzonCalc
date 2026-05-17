import HttpClient from 'src/api/base/httpClient'
import { useConfig } from 'src/config'

class LocalHttpClient extends HttpClient {
  constructor () {
    super({
      notifyError: false,
      removeRequestInterceptors: true,
      baseUrl: () => useConfig().localAppBaseUrl,
      api: () => useConfig().localAppApi
    })
  }
}

export const localHttpClient = new LocalHttpClient()
