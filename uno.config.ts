import { defineConfig, presetUno, presetWebFonts } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetWebFonts({
      provider: 'google',
      fonts: {
        sans: 'Inter:400,600,700',
        mono: 'JetBrains Mono',
      },
    }),
  ],
  extractors: [
    {
      name: 'python-extractor',
      supportLargeTree: false,
      extract({ content }) {
        const classes: string[] = []
        const regex = /class\s*=\s*["']([^"']+)["']/g
        let match
        while ((match = regex.exec(content)) !== null) {
          classes.push(...match[1].split(/\s+/).filter(Boolean))
        }
        return classes
      },
    },
  ],
  // Column header colors use f-strings so extractor never sees literal classes; safelist Uno preset colors
  safelist: [
    'border-b-3',
    'bg-gray-500/20', 'border-gray-500',
    'bg-blue-500/20', 'border-blue-500',
    'bg-amber-500/20', 'border-amber-500',
    'bg-violet-500/20', 'border-violet-500',
    'bg-emerald-500/20', 'border-emerald-500',
  ],
  preflights: [
    {
      getCSS: () => `
        :root { --un-bg: #ffffff; --un-bg-reverse: #1a1a1a; }
        body, html { margin: 0; padding: 0; box-sizing: border-box; }
        #wawa-app, #main-content, #kanban-board {
          margin-left: 0 !important; margin-right: 0 !important;
          padding-left: 0 !important; padding-right: 0 !important;
          width: 100%; max-width: 100%; box-sizing: border-box;
        }
        #wawa-app { overflow-x: hidden; }
        #main-content > div:first-child, #main-content > div:first-child > div {
          padding-left: 0 !important; padding-right: 0 !important;
        }
      `,
    },
  ],
})
