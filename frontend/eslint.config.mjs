import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';

export default defineConfig([
  ...nextVitals,
  globalIgnores([
    '.next/**',
    '.next-dev/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
  {
    files: [
      'src/components/**/*.ts',
      'src/components/**/*.tsx',
      'src/app/(agency)/**/*.ts',
      'src/app/(agency)/**/*.tsx',
      'src/app/(traveler)/**/*.ts',
      'src/app/(traveler)/**/*.tsx',
      'src/app/(auth)/**/*.ts',
      'src/app/(auth)/**/*.tsx',
    ],
    rules: {
      'no-restricted-globals': [
        'warn',
        {
          name: 'fetch',
          message:
            'Use the centralized API client (@/lib/api-client) instead of bare fetch() in UI components.',
        },
      ],
    },
  },
]);
