import { defineConfig, presetUno, presetWebFonts, presetIcons } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetIcons({ cdn: 'https://esm.sh/' }),
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
    'border-b-3', 'px-5', 'px-6',
    'bg-gray-500/20', 'border-gray-500', 'text-gray-400', 'bg-gray-500/50',
    'bg-blue-500/20', 'border-blue-500', 'text-blue-400', 'bg-blue-500/50',
    'bg-amber-500/20', 'border-amber-500', 'text-amber-400', 'bg-amber-500/50',
    'bg-violet-500/20', 'border-violet-500', 'text-violet-400', 'bg-violet-500/50',
    'bg-emerald-500/20', 'border-emerald-500', 'text-emerald-400', 'bg-emerald-500/50',
    // Icons: ensure they compile (extractor may miss; Python uses cls)
    'i-mdi-view-kanban', 'i-mdi-refresh',
    'i-mdi-checkbox-blank-outline', 'i-mdi-progress-clock', 'i-mdi-clock-outline',
    'i-mdi-check-circle-outline', 'i-mdi-check-circle',
  ],
  preflights: [
    {
      getCSS: () => `
        :root { --un-bg: #ffffff; --un-bg-reverse: #1a1a1a; }
        html, body {
          margin: 0 !important; padding: 0 !important;
          width: 100% !important; min-width: 100vw !important;
          box-sizing: border-box;
        }
        main, main.container {
          margin: 0 !important; padding: 0 !important;
          width: 100% !important; max-width: none !important;
        }
        main.container h1 { margin: 0 !important; padding: 0 !important; }
        #wawa-app {
          width: 100%; min-width: 100vw; max-width: 100%;
          margin: 0; padding: 0; box-sizing: border-box; overflow-x: hidden;
        }
        #main-content, #kanban-board {
          width: 100%; max-width: 100%;
          margin-left: 0 !important; margin-right: 0 !important;
          padding-left: 0 !important; padding-right: 0 !important;
          box-sizing: border-box;
        }
      `,
    },
  ],
})
