"""
Use `blender` to package any extensions found in the current directory
into the `build` directory.

Specifically:
- List all immediate subdirectories that contain a `blender_manifest.toml` file.
- Parse their `blender_manifest.toml` file to extract `id`s and `version`s (only for better logging).
- For each extension, run the `blender --command extension build` command.

Requirements:
- `blender` must be installed and available as a command.
- `tomllib` (available since Python 3.11+)
"""
from __future__ import annotations

import argparse
import shutil
import os
import subprocess
import tomllib
import traceback
from dataclasses import dataclass


def is_blender_available():
    try:
        subprocess.run([  # blender --version
            'blender', '--version'
        ],
            shell=True,
            check=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def is_extension_directory(path):
    return os.path.exists(os.path.join(path, 'blender_manifest.toml'))


@dataclass
class ExtensionInfo:
    id: str
    version: str
    source_directory: str


def parse_extension_info(path: str) -> ExtensionInfo:
    with open(os.path.join(path, 'blender_manifest.toml'), 'br') as f:
        manifest = tomllib.load(f)
    try:
        return ExtensionInfo(
            id=manifest['id'],
            version=manifest['version'],
            source_directory=path,
        )
    except KeyError as e:
        raise ValueError(f"Invalid manifest: missing '{e.args[0]}' key") from e


def build_extension_with_blender(extension: ExtensionInfo, build_dir: str):
    try:
        result = subprocess.run([  # blender --command extension build
            'blender', '--command', 'extension', 'build',
            '--source-dir', extension.source_directory,
            '--output-dir', build_dir,
        ], capture_output=True,
            shell=True,  # Otherwise Python doesn't recognize `.bat` files available on Windows' PATH as executable aliases
            # check=True,  # We cannot rely on this since Blender currently always crashes from the command line on my system
        )
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        error_excerpts = [
            'usage: blender',
            'FATAL_ERROR',
        ]
        if any(exc in stdout or exc in stderr for exc in error_excerpts):
            print(stdout)
            print(stderr)
            raise Exception('Error using blender to build the extension. See log above.')
        print(f'Extension should have been built successfully, check the "{build_dir}" directory.')
    except Exception as e:
        traceback.print_exception(e)
        print(f'Failed to build extension {extension.id} from "{extension.source_directory}" using `blender --command extension build`. See log above.')
        exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Build Blender extensions using the blender command line tool.'
    )
    parser.add_argument(
        '--build-dir',
        default='build',
        help='Directory where built extensions will be placed (default: build)'
    )
    parser.add_argument(
        '--extensions-dir',
        default='.',
        help='Directory to scan for extensions (default: current directory)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear the build directory before building'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    build_directory = args.build_dir
    extensions_directory = args.extensions_dir

    if not is_blender_available():
        print(f"'blender' command not found. Please ensure your Blender installation is available on the system path.")
        exit(1)

    if args.clear and os.path.exists(build_directory):
        shutil.rmtree(build_directory)
        print(f'Cleared build directory: "{build_directory}".')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)
        print(f'Created build directory: "{build_directory}".')

    extensions: list[ExtensionInfo] = []
    for dir in os.listdir(extensions_directory):
        path = os.path.join(extensions_directory, dir)
        if is_extension_directory(path):
            extensions.append(parse_extension_info(path))

    print(f'Found {len(extensions)} extensions to build.')
    for ext in extensions:
        print(f'Building "{ext.id}" (v{ext.version}) from "{ext.source_directory}"...')
        build_extension_with_blender(ext, build_directory)
        print(f'Built "{ext.id}"')

    print(f'Done. Built {len(extensions)} extensions into "{build_directory}".')
