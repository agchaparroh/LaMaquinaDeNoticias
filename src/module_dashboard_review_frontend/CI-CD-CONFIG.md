# CI/CD Configuration for Dashboard Review Frontend Tests

## GitHub Actions Workflow

```yaml
name: Dashboard Review Frontend - Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'src/module_dashboard_review_frontend/**'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'src/module_dashboard_review_frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
        cache-dependency-path: src/module_dashboard_review_frontend/package-lock.json
    
    - name: Install dependencies
      working-directory: ./src/module_dashboard_review_frontend
      run: npm ci
    
    - name: Run type checking
      working-directory: ./src/module_dashboard_review_frontend
      run: npm run type-check
    
    - name: Run all tests with coverage
      working-directory: ./src/module_dashboard_review_frontend
      run: npm run test:coverage -- --run
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        directory: ./src/module_dashboard_review_frontend/coverage
        flags: dashboard-frontend
        name: dashboard-review-frontend
```

## GitLab CI Configuration

```yaml
stages:
  - install
  - test
  - coverage

variables:
  NODE_VERSION: "20"

.frontend-base:
  image: node:${NODE_VERSION}
  before_script:
    - cd src/module_dashboard_review_frontend
    - npm ci --cache .npm --prefer-offline

install-dependencies:
  extends: .frontend-base
  stage: install
  script:
    - echo "Dependencies installed"
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - src/module_dashboard_review_frontend/.npm
      - src/module_dashboard_review_frontend/node_modules

test-unit:
  extends: .frontend-base
  stage: test
  script:
    - npm test -- --run tests/unit
  needs: ["install-dependencies"]

test-integration:
  extends: .frontend-base
  stage: test
  script:
    - npm test -- --run tests/integration
  needs: ["install-dependencies"]
  timeout: 15 minutes

coverage-report:
  extends: .frontend-base
  stage: coverage
  script:
    - npm run test:coverage -- --run
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  needs: ["test-unit", "test-integration"]
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: src/module_dashboard_review_frontend/coverage/cobertura-coverage.xml
```

## Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    tools {
        nodejs 'NodeJS-20'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                dir('src/module_dashboard_review_frontend') {
                    sh 'npm ci'
                }
            }
        }
        
        stage('Type Check') {
            steps {
                dir('src/module_dashboard_review_frontend') {
                    sh 'npm run type-check'
                }
            }
        }
        
        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        dir('src/module_dashboard_review_frontend') {
                            sh 'npm test -- --run tests/unit'
                        }
                    }
                }
                
                stage('Integration Tests') {
                    steps {
                        dir('src/module_dashboard_review_frontend') {
                            sh 'npm test -- --run tests/integration'
                        }
                    }
                }
            }
        }
        
        stage('Coverage') {
            steps {
                dir('src/module_dashboard_review_frontend') {
                    sh 'npm run test:coverage -- --run'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'coverage',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
    }
    
    post {
        always {
            junit 'src/module_dashboard_review_frontend/test-results/*.xml'
        }
    }
}
```

## Local Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run tests before commit
cd src/module_dashboard_review_frontend

echo "Running type check..."
npm run type-check || exit 1

echo "Running tests..."
npm test -- --run --changed || exit 1

echo "All tests passed! ✅"
```
