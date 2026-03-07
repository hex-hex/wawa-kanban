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
  preflights: [
    {
      getCSS: () => `
        :root {
          --un-bg: #ffffff;
          --un-bg-reverse: #1a1a1a;
        }
      `,
    },
  ],
})
