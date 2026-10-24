# OmixForge Project Overview

## 1. Project summary
OmixForge is a desktop bioinformatics workflow application built with Python and PyQt6. It helps researchers and bioinformaticians manage Nextflow pipelines, prepare sample data, run workflow jobs, monitor outputs, and configure the app through a graphical interface.

The project is designed to run pipeline orchestration in an offline-friendly environment, with Docker and Nextflow as key system dependencies. It focuses on nf-core-style workflow execution and a user-friendly desktop experience for scientific data analysis.

## 2. Main purpose
OmixForge exists to simplify complex bioinformatics execution by hiding command-line complexity behind a desktop UI. It makes it easier to:

- browse available Nextflow workflows
- import or manage local pipelines
- prepare sample sheets and metadata
- configure pipeline parameters
- run jobs in public or private mode
- monitor pipeline status and logs
- review output artifacts
- extend the app with plugins

## 3. Project type
- Type: Desktop application
- Language: Python
- UI framework: PyQt6
- Workflow engine: Nextflow
- Container runtime: Docker
- Packaging: Debian package, executable build, Snap support

## 4. Core architecture

### Application entry
- src/__main__.py
  - main app window
  - central navigation shell
  - startup/access page flow
  - main app loading logic

### Bootstrap and environment checks
- src/core/initiate.py
  - checks whether Docker and Nextflow are installed
  - loads constants/configuration
  - initializes runtime dependencies

### Startup / access flow
- src/core/profile_page/startup_page.py
  - welcome screen and mode selection
- src/core/profile_page/profile.py
  - profile/login UI and state
- src/core/profile_page/login.py
  - login handling
- src/core/profile_page/signup.py
  - sign-up flow
- src/core/profile_page/requirements.py
  - requirements validation for missing dependencies

### Dashboard and workflow management
- src/core/dashboard/pipeline_dashboard.py
  - main dashboard container
- src/core/dashboard/pipeline_dash_tab/local_pipeline.py
  - local pipeline list and management operations
- src/core/dashboard/pipeline_import_tab/pipeline_import.py
  - import pipeline workflows
- src/core/dashboard/pipeline_editor_tab/pipeline_editor.py
  - pipeline editor view
- src/core/dashboard/pipeline_dash_tab/pipeline_args.py
  - parameter form dialog for pipeline inputs

### Sample preparation
- src/core/sample/sample_page.py
  - sample workspace entry
- src/core/sample/sample_prep_tab/sample_prep.py
  - sample sheet editing UI
- src/core/sample/ena_fastq_downloader_tab/ena_fastq_downloader.py
  - ENA data download interface

### Status and results
- src/core/status_page/pipeline_status.py
  - pipeline status overview
- src/core/status_page/status/run_status.py
  - active run status UI
- src/core/status_page/results/run_results.py
  - result viewing and archive extraction logic

### Settings and plugins
- src/core/settings_page/settings.py
  - general app settings page
- src/core/plugin_manager/manager.py
  - plugin management logic
- src/core/plugin_manager/plugin_page.py
  - plugin page UI
- src/core/plugin_manager/plugin_installer.py
  - plugin store installer UI
- src/core/about_page/about.py
  - about page

## 5. Key classes

### App shell
- MainWindow
  - central app shell and navigation
  - controls sidebar and page switching

### Startup flow
- AccessModePage
  - public/private access selection
- ProfilePage
  - user account logic UI
- Login
  - login process
- SignUp
  - signup flow
- RequirementsNotSatisfied
  - missing dependency handling

### Pipeline engine UI
- PipelineDashboard
- PipelineLocal
- PipelineImport
- PipelineEditorTab
- PipelineArgsDialog
- PipelineCard

### Sample workflow
- Sample
- SamplePrepPage
- ENAFastqDownloader
- ENADownloaderManager

### Monitoring/results
- PipelineStatus
- PipelineRunStatus
- PipelineResultsPage

### Utilities
- InitiateApp
- NfcoreUtils
- OmixForgeLogger
- PluginBase
- PluginManager
- SettingsPage

## 6. Important data flow
1. App starts in src/__main__.py
2. MainWindow creates a startup page
3. InitiateApp checks installation prerequisites
4. User chooses public or private access
5. Main desktop shell loads if requirements are met
6. Dashboard displays pipelines and allows import/editing
7. Samples are prepared for workflows
8. Pipeline execution runs through Nextflow/Docker
9. Results and logs are surfaced in status/result pages

## 7. Where to find the most important logic

### Startup and app flow
- src/__main__.py
- src/core/initiate.py
- src/core/profile_page/startup_page.py

### Pipeline functionality
- src/core/dashboard/pipeline_dashboard.py
- src/core/dashboard/pipeline_dash_tab/local_pipeline.py
- src/core/dashboard/pipeline_import_tab/pipeline_import.py
- src/core/dashboard/pipeline_editor_tab/pipeline_editor.py

### Sample and data prep
- src/core/sample/sample_page.py
- src/core/sample/sample_prep_tab/sample_prep.py
- src/core/sample/ena_fastq_downloader_tab/ena_fastq_downloader.py

### Settings and plugins
- src/core/settings_page/settings.py
- src/core/plugin_manager/manager.py
- src/core/plugin_manager/plugin_installer.py

### Shared utilities
- src/utils/nfcore_utils.py
- src/utils/fileops/file_handle.py
- src/utils/constants.py
- src/utils/logger_module/omix_logger.py

## 8. Typical developer workflow
- Start the app with the project virtual environment and run:
  - make dev
- Inspect the startup flow first when debugging UI entry points
- Use the dashboard files to understand pipeline import and execution flow
- Use the status pages for logs/result rendering
- Use settings and plugin modules for configuration and extension behavior

## 9. Repo structure overview
```text
OmixForge/
├── src/
│   ├── __main__.py
│   ├── core/
│   │   ├── about_page/
│   │   ├── dashboard/
│   │   ├── plugin_manager/
│   │   ├── profile_page/
│   │   ├── sample/
│   │   ├── settings_page/
│   │   ├── status_page/
│   │   └── initiate.py
│   ├── utils/
│   └── assets/
├── tests/
├── docs/
├── scripts/
├── README.md
├── Makefile
├── pyproject.toml
├── omixforge.spec
├── snapcraft.yaml
└── LICENSE
```

## 10. Key technologies
- Python 3.13+
- PyQt6
- Nextflow
- Docker
- JSON configuration files
- SVG/image assets
- Plugin-based UI extension model

## 11. Notes for AI agents
When working in this repo, the most useful starting points are:

- entry point: src/__main__.py
- app initialization: src/core/initiate.py
- dashboard logic: src/core/dashboard/**
- sample workflow: src/core/sample/**
- status logic: src/core/status_page/**
- settings/plugins: src/core/settings_page/** and src/core/plugin_manager/**

This makes the repo easier to navigate and understand without reading the whole tree at once.

## 12. AI implementation guidelines for feature and bug work

These rules apply to any AI assistant or contributor working on this repository.

### 12.1 Before making changes
- Read the relevant module and surrounding code before editing.
- Identify the exact feature, bug, or UI screen affected.
- Trace the data flow from entry point to the specific widget or service involved.
- Prefer the narrowest edit that resolves the problem.
- Do not change unrelated logic or styles unless required.

### 12.2 Required workflow for bug fixes
1. Reproduce the issue or read the failing test.
2. Identify the root cause in the code path.
3. Add or update a focused test that captures the bug when possible.
4. Implement the smallest root-cause fix.
5. Re-run the relevant tests to verify the fix.
6. Check whether the change impacts adjacent UI or workflow behavior.

### 12.3 Required workflow for feature implementation
1. Locate the correct screen/module and understand its existing behavior.
2. Map the feature to the relevant classes and widgets.
3. Confirm the integration points: navigation, state, config, actions, and persistence.
4. Add tests for new behavior where practical.
5. Implement the feature with minimal scope expansion.
6. Validate the changed flows with the relevant test subset or smoke checks.
7. Update documentation or project notes if user-facing behavior changes.

### 12.4 Validation rules
- Validate with the smallest relevant test command, not broad unrelated suites.
- Prefer Python tests under tests/ for logic and UI regression coverage.
- If the change affects PyQt widgets, run the relevant UI tests.
- If the change affects workflow execution or config integrity, verify the surrounding behavior manually or through a focused test.
- Do not claim a fix is complete without fresh test output evidence.

### 12.5 Testing expectations
- New behavior should ideally have a test that exercises it.
- Bug fixes should include a regression check if feasible.
- Keep tests focused and deterministic.
- Avoid mock-heavy assertions that only validate mock behavior; test the real UI or logic path when possible.

### 12.6 Documentation and repo maintenance
- Update project docs when behavior, setup, or flow changes.
- Keep this file current when major architectural or workflow changes happen.
- If a new feature introduces new modules or screens, document where they live and how they fit into the app flow.
- If a bug fix changes usage or setup requirements, update README or project notes accordingly.

### 12.7 Recommended validation commands
Use the project environment before running tests:

```bash
source /home/sinan/.cache/pypoetry/virtualenvs/omixforge-1Xmc9--o-py3.13/bin/activate
cd /home/sinan/Projects/OmixForge
pytest tests/test_ui/test_main_page.py -q
```

For targeted validation, use a filtered run when possible:

```bash
pytest tests/test_ui/test_main_page.py -q -k <test_name>
```

### 12.8 AI quality bar
Before finishing work, an AI agent should confirm:
- the root cause was identified
- the fix is minimal and targeted
- the relevant tests pass
- no unrelated files were changed unnecessarily
- project docs were updated when needed
- the change is explainable in plain language

## 13. Short description for human users
OmixForge is a GUI-driven bioinformatics pipeline manager that helps users run and track Nextflow workflows without writing long shell commands. It is aimed at researchers who want a streamlined, organized interface for workflow execution and sample management.
