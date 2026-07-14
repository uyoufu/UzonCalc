import path from 'path'
import fs from 'fs'
import os from 'os'
import { fileURLToPath } from 'url'
import ts from 'typescript'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

function findWebRoot(startDir) {
  let current = startDir
  const { root } = path.parse(current)
  while (current && current !== root) {
    if (fs.existsSync(path.join(current, 'package.json')) && fs.existsSync(path.join(current, 'src'))) {
      return current
    }
    current = path.dirname(current)
  }
  return process.cwd()
}

function parseArgs(argv) {
  const args = {
    from: 'zh-CN',
    to: 'en-US'
  }

  for (let i = 0; i < argv.length; i++) {
    const current = argv[i]
    if (current === '--from' && argv[i + 1]) {
      args.from = argv[i + 1]
      i++
      continue
    }
    if (current === '--to' && argv[i + 1]) {
      args.to = argv[i + 1]
      i++
    }
  }

  return args
}

async function importTsModule(filePath) {
  const source = fs.readFileSync(filePath, 'utf8')
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022
    },
    fileName: filePath
  })

  const moduleUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(transpiled.outputText)}`
  return import(moduleUrl)
}

function extractKeys(localeObj, prefix = '', result = []) {
  if (!localeObj || typeof localeObj !== 'object' || Array.isArray(localeObj)) {
    return result
  }

  Object.entries(localeObj).forEach(([key, value]) => {
    const currentKey = prefix ? `${prefix}.${key}` : key
    result.push(currentKey)
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      extractKeys(value, currentKey, result)
    }
  })

  return result
}

async function main() {
  const webRoot = findWebRoot(__dirname)
  const localesDir = path.join(webRoot, 'src', 'i18n', 'locales')
  const { from, to } = parseArgs(process.argv.slice(2))

  const fromFile = path.join(localesDir, `${from}.ts`)
  const toFile = path.join(localesDir, `${to}.ts`)

  if (!fs.existsSync(fromFile)) {
    throw new Error(`Source locale file not found: ${fromFile}`)
  }
  if (!fs.existsSync(toFile)) {
    throw new Error(`Target locale file not found: ${toFile}`)
  }

  const fromLocale = await importTsModule(fromFile)
  const toLocale = await importTsModule(toFile)

  const fromKeys = extractKeys(fromLocale.default || fromLocale)
  const toKeys = extractKeys(toLocale.default || toLocale)

  const toSet = new Set(toKeys)
  const missing = fromKeys.filter((k) => !toSet.has(k))
  console.log(`Total ${from} keys:`, fromKeys.length)
  console.log(`Total ${to} keys:`, toKeys.length)
  console.log(`Missing in ${to} (count):`, missing.length)
  missing.forEach((k) => console.log(k))

  // const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'uzoncalc-i18n-'))
  // const outputFile = path.join(outputDir, 'missing_i18n_keys.txt')
  // fs.writeFileSync(outputFile, missing.join('\n'))
  // console.log('Wrote', outputFile)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})
