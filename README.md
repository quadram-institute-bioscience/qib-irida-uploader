# IRIDA Uploader Script

This Python script (`irida.py`) is rather a wrapper of `iridauploader` to provide functionality to interact with IRIDA ("legacy"), allowing users to create projects, prepare sample lists, and upload data.

## Features

- Create projects in IRIDA
- Prepare sample lists for uploading
- Upload run folders to IRIDA
- Support for both single and batch uploads
- Flexible configuration options (file, environment variables, or interactive prompt)

## Prerequisites

- Python 3.x
- Required Python packages are listed in `requirements.txt`

## Installation

1. Clone this repository or download the `irida.py` script.
2. Install the required packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Usage

The script provides two main commands: `prepare` and `upload`.

### Prepare Command

Prepares a folder of fastq files for uploading to IRIDA by creating a project (if needed) and generating a sample list.

```bash
python irida.py prepare [OPTIONS] [PATH]
```

Options:
- `--pid`: Project ID (optional)
- `--name`: Project Name (optional), if not provided, the script will use the provided folder name
- `--pe/--se`: Are the fastq files Paired-End? (default: False)
- `--sort/--no-sort`: Sort samples by name (default: False)
- `--pattern`: Scan fastq files with a pattern (default: "*_R1_001.fastq.gz")
- `--config`: Path to IRIDA config file

### Upload Command

Uploads a run folder to IRIDA.

```bash
python irida.py upload [OPTIONS] DIRECTORY
```

Options:
- `--force-upload`: Force upload (flag)
- `--continue-upload`: Start uploading from where the last upload left off (flag)
- `--upload_mode`: Upload mode (choices: default, assemblies, fast5; default: default)
- `--config`: Path to IRIDA config file

## Configuration

The script can be configured using a configuration file, environment variables, or interactive prompts. The configuration includes:

- IRIDA base URL
- Client ID
- Client Secret
- Username
- Password
- API timeout

You can provide configuration in one of the following formats:

### Config file
```
[Settings]
client_id = CHANGE-ME
client_secret = CHANGE-ME
username = CHANGE-ME
password = CHANGE-ME
base_url = CHANGE-ME
parser = directory
timeout = 1500
```

### Environment variables
```
export IRIDA_BASE_URL=CHANGE-ME
export IRIDA_CLIENT_ID=CHANGE-ME
export IRIDA_CLIENT_SECRET=CHANGE-ME
export IRIDA_USERNAME=CHANGE-ME
export IRIDA_PASSWORD=CHANGE-ME
export IRIDA_TIMEOUT=CHANGE-ME
```
### Prompting
If neither the config file nor environment variables provide all the necessary configuration parameters, the script will prompt you for any missing information. For example, if your config file only contains `base_url`, you will be asked to provide the remaining 5 parameters interactively.

## Examples

1. Prepare a folder for upload:
```bash
python irida.py prepare --pe --sort /path/to/fastq/folder
```

2. Upload a prepared folder to IRIDA:
```bash
python irida.py upload --force-upload /path/to/prepared/folder
```

## Notes

- Ensure you have the necessary permissions to access IRIDA and the local directories.
- The script creates temporary configuration files that are automatically deleted upon script exit.
- For security, avoid storing sensitive information like passwords in plain text configuration files.

## Dependencies

All required dependencies are listed in the `requirements.txt` file. To view the specific versions and packages required, please refer to this file.

## Contributing

Contributions to improve the script are welcome. Please ensure to follow the existing code style and add unit tests for any new functionality.

## License

MIT License

Copyright (c) [2024] [Thanh Le Viet]
