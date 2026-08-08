## [1.1.1](https://github.com/geodanchev/DomOS/compare/v1.1.0...v1.1.1) (2026-08-08)


### Bug Fixes

* **frontend:** Fix nginx config structure for Cloud Run ([a7f1ae6](https://github.com/geodanchev/DomOS/commit/a7f1ae6d59e06d4d0801ebca9c6bd88a427b0b67))

# [1.1.0](https://github.com/geodanchev/DomOS/compare/v1.0.0...v1.1.0) (2026-08-08)


### Features

* **scheduler:** Add Cloud Scheduler support for monthly obligations ([bb79efa](https://github.com/geodanchev/DomOS/commit/bb79efa41570a763ca0f87e19a520c865605897c))

# 1.0.0 (2026-08-05)


### Bug Fixes

* add CACHEBUST arg to invalidate Docker cache on each commit ([ab877aa](https://github.com/geodanchev/DomOS/commit/ab877aa2fac95b194f883882c9e3c7abe5588798))
* Add CACHEBUST to frontend build to force rebuild ([8a1ceca](https://github.com/geodanchev/DomOS/commit/8a1ceca306af5e3554b0b3ef5de8c781dde7afb0))
* Add Cyrillic font support to PDF receipts ([a799046](https://github.com/geodanchev/DomOS/commit/a799046373f8d9ac96e92e2bbf863356279b0fd1))
* Add DejaVu fonts to Docker images for Cyrillic PDF support ([a6ccdf1](https://github.com/geodanchev/DomOS/commit/a6ccdf1066b2337887901f804edd25d5ed877c9d))
* Add executable permission to entrypoint scripts ([241abf2](https://github.com/geodanchev/DomOS/commit/241abf2cf416883840a58cfb7fe727e7d98c951c))
* add missing lib/utils.ts to git and fix .gitignore ([626f981](https://github.com/geodanchev/DomOS/commit/626f981ed2a775fd393315383d3c177f0681720e))
* Add values_callable to Enum columns for PostgreSQL compatibility ([e8e95b7](https://github.com/geodanchev/DomOS/commit/e8e95b72c965bb9380d627f1a8e9f950a6f57b3f))
* Add VITE_API_URL build-arg to frontend Docker build ([47e47bc](https://github.com/geodanchev/DomOS/commit/47e47bc8a258f53c6f90902e0f7eb3a59638a315))
* **ci:** add Cloud SQL connection and secrets to Cloud Run deploy ([50f41fe](https://github.com/geodanchev/DomOS/commit/50f41fee970612b5dd2a6c23aec5858b55ca100b))
* **ci:** Update release.yml to use GITHUB_TOKEN and Node.js 22 [skip ci] ([bc51568](https://github.com/geodanchev/DomOS/commit/bc5156893b8566b9d703809c573d5114a59db03f))
* Docker WSL volume mount issues - copy source files instead of mounting ([3cbf70e](https://github.com/geodanchev/DomOS/commit/3cbf70e5acae634a4193137ed4eb4df78399caaa))
* **frontend:** fix vitest path alias resolution for CI environment ([54b2d43](https://github.com/geodanchev/DomOS/commit/54b2d439802a4aaf7560bd763cb5d1a05c2fa14f))
* **frontend:** update test mocks to match current TypeScript interfaces ([d19bdc7](https://github.com/geodanchev/DomOS/commit/d19bdc7916ff6dc14eb3cb2631cda00f0c188f4f))
* **frontend:** use combined alias approach for CI path resolution ([4a51a94](https://github.com/geodanchev/DomOS/commit/4a51a94240d1bd8a8b44f27621f4ef406779d243))
* **frontend:** use native Vite tsconfigPaths for CI compatibility ([4025e42](https://github.com/geodanchev/DomOS/commit/4025e4288268d3a1bbb358fc4db44c66585de3eb))
* **frontend:** use native Vite tsconfigPaths option instead of plugin ([b00970a](https://github.com/geodanchev/DomOS/commit/b00970a8a2625fca3f73eb851cfe981b108b39c9))
* **frontend:** use process.cwd() and comprehensive alias config for CI ([4081c28](https://github.com/geodanchev/DomOS/commit/4081c286cbd04be8f6db51dc79d07b3d9220bf67))
* **frontend:** use server.deps.inline and regex alias for CI ([2e31870](https://github.com/geodanchev/DomOS/commit/2e31870491c52631d2707dd2653fc40f8d46f301))
* **frontend:** use vite-tsconfig-paths for reliable path alias resolution in CI ([e3be5e9](https://github.com/geodanchev/DomOS/commit/e3be5e9fe43077b8a73e591cf67c85cc6aa53c02))
* Payment dialog improvements and API endpoint fix ([352f30c](https://github.com/geodanchev/DomOS/commit/352f30c92f7aa639c18e7973098884e636d33bb4))
* remove default nginx configs before copying nginx.cloudrun.conf ([706cc3c](https://github.com/geodanchev/DomOS/commit/706cc3cc488ae33146d36c93758b326ee6c3d80a))
* Resolve CI/CD workflow failures ([ac3ec73](https://github.com/geodanchev/DomOS/commit/ac3ec731ad85b65f7ef5d7ef1a3945f1b563d4ea))
* Restore executable permission on start-dev.sh ([3eb5a1f](https://github.com/geodanchev/DomOS/commit/3eb5a1f38fb1ffc440f2194cbb51e85c4538d40a))
* support Cloud SQL Unix socket in entrypoint.sh ([ffb61ff](https://github.com/geodanchev/DomOS/commit/ffb61ff7d955c6d309ba5b2c5695ae0cf9aa9663))
* update Dockerfile to expose port 8080 for Cloud Run ([613526d](https://github.com/geodanchev/DomOS/commit/613526d80c725362f459399d2312481223f79df6))
* update frontend Dockerfile to use nginx.cloudrun.conf with PORT env ([6ab3e5f](https://github.com/geodanchev/DomOS/commit/6ab3e5f3f028b41692c35fc7c0f57ce7277e9bf0))
* Update test mocks to include new User fields (email, phone, avatar_url) ([d31eb4b](https://github.com/geodanchev/DomOS/commit/d31eb4b3f3247c81a548a22a4b275154ceb01a1f))
* use PORT env variable for uvicorn in entrypoint.sh ([0933c6f](https://github.com/geodanchev/DomOS/commit/0933c6f5e2ec148b929457af236ba2d9ce61bc17))


### Features

* Add Alembic migrations to deploy process + DB management skills ([de9d00d](https://github.com/geodanchev/DomOS/commit/de9d00dffd9911294f5e9570b673f358614e2888))
* Add comprehensive permissions system and project automation ([e093cff](https://github.com/geodanchev/DomOS/commit/e093cff87b58f451aca172e3aebde079a35f93e1))
* Add Git push skill and new obligation dialog ([aea525d](https://github.com/geodanchev/DomOS/commit/aea525d35deda5dbc17a6f6cedb76168af303ef4))
* Add Google Cloud Run deployment configuration ([124080a](https://github.com/geodanchev/DomOS/commit/124080a26a0dfbc1a43c0d188b7176a389c00ea2))
* Add receipt download button to payments list ([c9b96eb](https://github.com/geodanchev/DomOS/commit/c9b96eb76a1c21b0c8d7aab33648d670fdd62bd7))
* Add User Settings page with profile, password, and avatar management ([08b117d](https://github.com/geodanchev/DomOS/commit/08b117d80fcbd29edee86440ec37f1f97e65b490))
* Add user settings page with profile, security, and account management ([eaa5bc2](https://github.com/geodanchev/DomOS/commit/eaa5bc2e5c1435302dd015f15894c82f05f9f648))
* add version display in UI and health endpoint ([5b0af67](https://github.com/geodanchev/DomOS/commit/5b0af675605eb2c515abf730c96a46e64978d40c))
* **backup:** Add Cloud SQL automated backup infrastructure ([1e74859](https://github.com/geodanchev/DomOS/commit/1e7485965f81d471ad4d074ac292d6089da26187))
* **ci:** add automatic Cloud Run deployment to GitHub Actions ([0d87711](https://github.com/geodanchev/DomOS/commit/0d877116567f4d75483c2435a16a50965804a9c5))
* **ci:** add semantic-release for automatic versioning ([cbcea3f](https://github.com/geodanchev/DomOS/commit/cbcea3f3ca8b6da7a68fad98001ffa98f3a7fbb8))
* Complete test suite with 158 passing tests ([7238fdb](https://github.com/geodanchev/DomOS/commit/7238fdb8ce0cd598d9c1cf0f2cc844d672254fa0))
* **frontend:** add comprehensive unit tests for MVP1 Cashier ([82b6435](https://github.com/geodanchev/DomOS/commit/82b6435718931fbbf06bb729368fd735277d2551))
* Phase 2 - Production Environment Setup ([5b40a3c](https://github.com/geodanchev/DomOS/commit/5b40a3c6eafe0b4b8fb5220cff0369845e819db7))
* Добавяне на CI/CD pipeline с автоматични тестове ([7d91bf2](https://github.com/geodanchev/DomOS/commit/7d91bf25c8cbadc027eacc3014f28c9ee58dcf2b))
