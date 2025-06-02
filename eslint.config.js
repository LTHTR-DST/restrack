// eslint.config.js - Minimal ESLint config for ResTrack

export default [
    {
        ignores: [
            'node_modules/**',
            'dist/**',
            'build/**',
            '**/*.min.js',
        ],
    },
    {
        files: ['**/*.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            globals: {
                document: 'readonly',
                window: 'readonly',
                htmx: 'readonly',
                fetch: 'readonly',
                console: 'readonly',
                setTimeout: 'readonly',
                clearTimeout: 'readonly',
                setInterval: 'readonly',
                clearInterval: 'readonly',
                confirm: 'readonly',
                bootstrap: 'readonly',
                // Add project-specific globals only if needed
            },
        },
        rules: {
            'no-undef': 'error',
            'no-unused-vars': 'warn',
            'no-unreachable': 'error',
            'no-console': 'warn',
        },
    },
];
