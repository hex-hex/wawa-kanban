import { execSync } from 'child_process'
import { existsSync, mkdirSync, writeFileSync, readFileSync, watch } from 'fs'
import { join, resolve } from 'path'
import process from 'process'
import { globSync } from 'glob'

const STATIC_DIR = resolve('static')
const OUTPUT_FILE = join(STATIC_DIR, 'uno.css')

// Column header colors: f-strings in Python are not extracted; inject so UnoCSS generates them (must match uno.config.ts safelist)
const SAFELIST_CLASSES = [
  'border-b-3', 'px-5', 'px-6',
  'bg-gray-500/20', 'border-gray-500', 'text-gray-400', 'bg-gray-500/50',
  'bg-blue-500/20', 'border-blue-500', 'text-blue-400', 'bg-blue-500/50',
  'bg-amber-500/20', 'border-amber-500', 'text-amber-400', 'bg-amber-500/50',
  'bg-violet-500/20', 'border-violet-500', 'text-violet-400', 'bg-violet-500/50',
  'bg-emerald-500/20', 'border-emerald-500', 'text-emerald-400', 'bg-emerald-500/50',
  'i-mdi-view-kanban', 'i-mdi-refresh',
  'i-mdi-checkbox-blank-outline', 'i-mdi-progress-clock', 'i-mdi-clock-outline',
  'i-mdi-check-circle-outline', 'i-mdi-check-circle',
]

function ensureStaticDir() {
  if (!existsSync(STATIC_DIR)) {
    mkdirSync(STATIC_DIR, { recursive: true })
  }
}

function extractPyClasses(dir = '.') {
  const classes = new Set()
  
  const pyFiles = globSync(join(dir, '**/*.py'))
  
  for (const file of pyFiles) {
    const content = readFileSync(file, 'utf-8')
    const regex = /(?:class|cls)\s*=\s*["']([^"']+)["']/g
    let match
    while ((match = regex.exec(content)) !== null) {
      match[1].split(/\s+/).filter(Boolean).forEach(c => classes.add(c))
    }
  }
  
  return Array.from(classes)
}

function build() {
  ensureStaticDir()
  
  const classes = new Set(extractPyClasses())
  SAFELIST_CLASSES.forEach(c => classes.add(c))
  const classList = Array.from(classes).join(' ')
  
  console.log(`Found ${classes.size} unique classes`)
  
  const tempFile = join(STATIC_DIR, 'temp.html')
  writeFileSync(tempFile, `<div class="${classList}"></div>`)
  
  try {
    execSync(`npx unocss ${tempFile} -o ${OUTPUT_FILE} --minify`, { 
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
