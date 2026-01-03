"""
Build `mkdocs` documentation subprojects stored in the `docs` directory
into the `docs/gh-pages-build` directory.

Specifically:
- The `docs/gh-pages-build` directory is first cleared before usage.
- Each documentation project is built into a corresponding subdirectory of the
  `docs/gh-pages-build` directory with the same name.
- The `docs/theme` directory is also copied into `docs/gh-pages-build/theme`.

Requirements:
- `pip install mkdocs`
"""
import os, traceback, shutil, subprocess, sys, argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Build mkdocs documentation subprojects.')
    parser.add_argument('--docs-dir', default='docs',
                        help='Directory containing documentation subprojects (default: docs)')
    parser.add_argument('--out-dir', default='gh-pages-build',
                        help='Name of the build output directory (default: gh-pages-build)')
    args = parser.parse_args()

    docs_dir: str = args.docs_dir
    gh_pages_dir: str = args.out_dir
    build_dir: str = os.path.join(docs_dir, gh_pages_dir)

    try:
        # Clear the gh-pages-build directory if it exists
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        print(f'Cleared build directory: "{build_dir}".')
        print()
    except Exception as e:
        traceback.print_exception(e)
        print(f'Could not remove existing build directory: "{build_dir}". See previous error.')
        exit(2)

    # Find subdirectories with mkdocs.yml and build them
    for item in os.listdir(docs_dir):
        item_path = os.path.join(docs_dir, item)
        try:
            if os.path.isdir(item_path):
                mkdocs_yml = os.path.join(item_path, 'mkdocs.yml')
                if os.path.isfile(mkdocs_yml):
                    # Run mkdocs build
                    print(f'Building docs in "{item_path}"...')
                    result = subprocess.run([  # python -m mkdocs
                        sys.executable, '-m', 'mkdocs',
                        'build',  # build documentation
                        '-s',     # strict mode (fail on warnings)
                        # output directory relative to item_path:
                        '-d', f'../{gh_pages_dir}/{item}'
                    ], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                        cwd=item_path,
                    )
                    if result.returncode:
                        print(f'Error building docs in "{item_path}". See output above.')
                        exit(1)
                    print(f'Built docs in "{item_path}".')
                    print()
        except Exception as e:
            traceback.print_exception(e)
            print(f'Error detecting project in directory "{item_path}". See previous error.')
            exit(3)

    try:
        # Copy the theme subdirectory
        theme_src = os.path.join(docs_dir, "theme")
        theme_dest = os.path.join(build_dir, "theme")
        if os.path.exists(theme_src):
            shutil.copytree(theme_src, theme_dest)
            print(f'Copied theme directory to "{theme_dest}".')
        else:
            print(f'No theme directory found at "{theme_src}".')
    except Exception as e:
        traceback.print_exception(e)
        print(f'Could not copy theme directory. See previous error.')
        exit(2)
