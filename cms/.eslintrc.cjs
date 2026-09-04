module.exports = {
    root: true,
    env: { browser: true, es2022: true },
    globals: { React: 'readonly' },
    parser: '@typescript-eslint/parser',
    parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } },
    plugins: ['@typescript-eslint', 'react-hooks', 'react-refresh'],
    extends: ['eslint:recommended'],
    rules: {
        'no-unused-vars': 'off',
        '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
        'react-hooks/rules-of-hooks': 'error',
        'react-hooks/exhaustive-deps': 'warn',
        'react-refresh/only-export-components': 'warn'
    }
};