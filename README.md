# OmixForge

OmixForge is a comprehensive, offline-capable bioinformatics workflow manager designed to simplify the execution and management of Nextflow pipelines (nf-core). It provides a user-friendly desktop interface for researchers and bioinformaticians to orchestrate complex data analysis pipelines without needing extensive command-line expertise 
[User guide](https://github.com/mohdsinanm/OmixForge/wiki).


## Features

OmixForge comes packed with features to streamline your bioinformatics workflows:

### Pipeline Dashboard
-   **Local Pipeline Management**: View and manage your locally available Nextflow pipelines from nf-core.
-   **One-Click Import**: Easily import pipelines from `nf-core` or other sources (TODO).
-   **Visual Launch Interface**: Configure pipeline parameters using a generated UI form instead of editing JSON/YAML files manually.

### Sample Preparation
-   **Smart Data Table**: An Excel-like interface to create and edit sample sheets.
-   **Auto-Discovery**: Automatically scan directories to find FASTQ/FASTA files and populate sample sheets, detecting paired-end reads intelligently.
-   **CSV Support**: Import and export your sample configurations to CSV format compatible with most pipelines.

### Pipeline Status
-   **Real-time Monitoring**: Track the progress of your running pipelines.
-   **Logs & Outputs**: Access execution logs and output directories directly from the interface.

### Plugin System
-   **Extensible Architecture**: Enhance OmixForge's capabilities with plugins.
-   **Plugin Store**: Browse and install plugins to add new tools or visualizations.
- Refer the repo Please refer this repo for more details [OmixForge-plugins](https://github.com/mohdsinanm/OmixForge-plugins)

### Access Modes
-   **Public Mode**: Use without restrictions for general pipeline execution.
-   **Private Mode**: Secure access for sensitive environments (requires configuration).

## Prerequisites

Before running OmixForge, ensure you have the following installed:

*   **Docker**: Required for containerized pipeline execution.
*   **Nextflow**: The workflow engine used to run the pipelines.
*   **Python 3.13+**: Required if running from source.

## Installation

### For Users (Debian/Ubuntu)

1.  Download the latest `.deb` package from the [Releases](https://github.com/mohdsinanm/OmixForge/releases/) page (or build it yourself).
2.  Install the package:
    ```bash
    sudo dpkg -i omixforge_x.y.z_amd64.deb
    ```
3.  Launch OmixForge from your application menu.

### For Developers (Source)

1.  Clone the repository:
    ```bash
    git clone https://github.com/mohdsinanm/OmixForge.git
    cd OmixForge
    ```

2.  Install dependencies using Poetry:
    ```bash
    poetry install
    $(poetry env activate)
    ```

3.  Run the application:
    ```bash
    make dev
    ```

## Building from Source

To build a standalone executable or a Debian package, use the included `Makefile`.

### Build binary
```bash
make build-bin
```
This will create a single-file executable in `dist/omixforge`.

### Build Debian Package
```bash
make package
```
This will generate a `.deb` installer in the current directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
