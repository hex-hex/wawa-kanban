import { defineConfig, presetUno, presetWebFonts, presetIcons, presetTypography } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetTypography(),
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
    'bg-blue-600', 'hover:bg-blue-500',
    'bg-amber-500/20', 'border-amber-500', 'text-amber-400', 'bg-amber-500/50',
    'bg-violet-500/20', 'border-violet-500', 'text-violet-400', 'bg-violet-500/50',
    'bg-emerald-500/20', 'border-emerald-500', 'text-emerald-400', 'bg-emerald-500/50',
    'bg-amber-600', 'bg-amber-500', 'text-amber-50',
    'bg-amber-800', 'text-amber-200', 'bg-amber-900', 'hover:bg-amber-800', 'text-stone-300',
    'bg-amber-700', 'text-amber-50', 'hover:bg-amber-600',
    'bg-orange-900', 'hover:bg-orange-800',
    'bg-emerald-600', 'bg-emerald-500', 'bg-emerald-700', 'text-emerald-50', 'hover:bg-emerald-600',
    'text-white',
    'active:bg-amber-600', 'active:bg-amber-500',
    'bg-red-900', 'text-red-200', 'hover:bg-red-800',
    'bg-red-800', 'text-red-100', 'hover:bg-red-700',
    'bg-green-900', 'text-green-200', 'hover:bg-green-800',
    // Icons: ensure they compile (extractor may miss; Python uses cls)
    'i-mdi-view-kanban', 'i-mdi-refresh',
    'i-mdi-checkbox-blank-outline', 'i-mdi-progress-clock', 'i-mdi-clock-outline',
    'i-mdi-check-circle-outline', 'i-mdi-check-circle',
    'i-mdi-close',
    'hidden',
    // Ticket card + modal actions (slate)
    'bg-slate-700/95', 'border-slate-600/80', 'hover:border-slate-500', 'text-slate-100', 'text-slate-500', 'text-slate-300',
    // Markdown prose (typography preset)
    'prose', 'prose-invert', 'prose-sm', 'prose-p:text-gray-300', 'prose-headings:text-gray-100',
    'bg-slate-600/70', 'bg-slate-600', 'hover:bg-slate-500', 'text-slate-200',
  ],
  preflights: [
    {
      getCSS: () => `
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.96); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes modalOut {
          from { opacity: 1; transform: scale(1); }
          to { opacity: 0; transform: scale(0.96); }
        }
        .modal-animate-in { animation: modalIn 0.2s ease-out; }
        .modal-animate-out { animation: modalOut 0.15s ease-in forwards; }
        :root { --un-bg: #ffffff; --un-bg-reverse: #1a1a1a; }
        html, body {
          margin: 0 !important; padding: 0 !important;
          width: 100% !important; min-width: 100vw !important;
          box-sizing: border-box;
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        }
        button {
          appearance: none;
          -webkit-appearance: none;
          background: none;
          border: none;
          margin: 0;
          padding: 0;
          font: inherit;
          color: inherit;
          cursor: pointer;
          box-shadow: none;
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
