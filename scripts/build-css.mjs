import { execSync } from 'child_process'
import { existsSync, mkdirSync, writeFileSync, readFileSync, watch } from 'fs'
import { join } from 'path'
import process from 'process'

const STATIC_DIR = 'static'
const OUTPUT_FILE = join(STATIC_DIR, 'uno.css')

function ensureStaticDir() {
  if (!existsSync(STATIC_DIR)) {
    mkdirSync(STATIC_DIR, { recursive: true })
  }
}

function extractPyClasses(dir = '.') {
  const classes = new Set<string>()
  const { globSync } = await import('glob')
  
  const pyFiles = globSync(join(dir, '**/*.py'))
  
  for (const file of pyFiles) {
    const content = readFileSync(file, 'utf-8')
    const regex = /class\s*=\s*["']([^"']+)["']/g
    let match
    while ((match = regex.exec(content)) !== null) {
      match[1].split(/\s+/).filter(Boolean).forEach(c => classes.add(c))
    }
  }
  
  return Array.from(classes)
}

function build(watchMode = false) {
  ensureStaticDir()
  
  const classes = extractPyClasses()
  const classList = classes.join(' ')
  
  console.log(`Found ${classes.length} unique classes`)
  
  const tempFile = join(STATIC_DIR, 'temp.html')
  writeFileSync(tempFile, `<div class="${classList}"></div>`)
  
  try {
    execSync(`npx unocss ${tempFile} ${OUTPUT_FILE} --minify`, { 
      stdio: 'inherit',
      cwd: process.cwd()
    })
    console.log(`CSS generated: ${OUTPUT_FILE}`)
  } catch (e) {
    console.error('Failed to generate CSS:', e)
  }
}

const args = process.argv.slice(2)
const watchMode = args.includes('--watch')

if (watchMode) {
  console.log('Watching for changes...')
  build()
  
  const { globSync } = await import('glob')
  const watcher = watch('.', { recursive: true }, (eventType, filename) => {
    if (filename && filename.endsWith('.py')) {
      console.log(`\n${eventType}: ${filename}`)
      build()
    }
  })
  
  process.on('SIGINT', () => {
    watcher.close()
    process.exit()
  })
} else {
  build()
}
