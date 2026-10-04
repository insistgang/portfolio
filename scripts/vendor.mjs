import { mkdirSync, copyFileSync } from 'node:fs';
mkdirSync('assets/vendor', { recursive: true });
copyFileSync('node_modules/lucide/dist/umd/lucide.min.js', 'assets/vendor/lucide.min.js');
copyFileSync('node_modules/lucide/LICENSE', 'assets/vendor/lucide-LICENSE');
copyFileSync('node_modules/tailwindcss/LICENSE', 'assets/vendor/tailwindcss-LICENSE');
