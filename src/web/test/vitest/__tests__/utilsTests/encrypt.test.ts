import { expect, test } from 'vitest'
import { aes, md5, deAes } from 'src/utils/encrypt'

test('aes', () => {
  const password = 'admin1234'
  const userId = 'admin'

  const key = md5(userId)
  const iv = key.substring(0, 16)
  const encrypt = aes(key, iv, password)
  expect(encrypt).toMatch(/^[0-9a-f]+$/)

  const decrypt = deAes(key, iv, encrypt)
  expect(decrypt).toBe(password)
})
