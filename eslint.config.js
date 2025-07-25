import js from '@eslint/js';

export default [
  // Configuración recomendada de ESLint
  js.configs.recommended,
  
  // Ignorar archivos
  {
    ignores: ['**/node_modules/**', '**/build/**', '**/dist/**', '**/.venv/**']
  },
  
  // Tu configuración personalizada
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'module',
      globals: {
        console: 'readonly',
        process: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        require: 'readonly',
        module: 'readonly',
        exports: 'readonly'
      }
    },
    rules: {
      // Sobrescribir o agregar reglas personalizadas
      'indent': ['error', 2],
      'quotes': ['error', 'single'],
      'semi': ['error', 'always'],
      'no-unused-vars': 'warn',
      'comma-dangle': ['error', 'never'],
      'space-before-blocks': 'error',
      'keyword-spacing': 'error',
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never']
    }
  }
];