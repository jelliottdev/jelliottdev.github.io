"""Build the guarded Windows port from pinned upstream source and explicit local edits.

Requires an existing clean upstream Git checkout and MinGW GCC. No downloads,
vendor build scripts, reused objects or execution of the resulting program.
The output directory must not exist. All compiled source hashes are checked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--gcc', default='gcc')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    spec = json.loads((HERE/'build-spec.json').read_bytes())
    patches = json.loads((HERE/'source-audit.json').read_bytes())['exact_patches']
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != spec['commit']:
        raise ValueError('Source revision differs from the declared commit')
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Use a clean upstream checkout')
    gcc = Path(shutil.which(args.gcc) or args.gcc).resolve()
    version = subprocess.check_output([str(gcc), '--version'], text=True).splitlines()[0]
    if 'MinGW' not in version:
        raise ValueError('This recipe requires MinGW GCC on Windows')
    output.mkdir(parents=False, exist_ok=False)
    src = output/'src'
    shutil.copytree(source/'src', src)
    for path in src.rglob('*'):
        if path.is_file() and path.suffix in ('.c', '.h'):
            path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
    p = src/'outguess.c'
    text = p.read_text(encoding='utf-8')
    for before, after in spec['portability_changes']:
        if text.count(before) != 1:
            raise ValueError('Portability edit does not match exactly once')
        text = text.replace(before, after)
    p.write_text(text, encoding='utf-8', newline='\n')
    for name, content in spec['configs'].items():
        (src/name).write_text(content, encoding='utf-8', newline='\n')
    for patch in patches:
        p = src/patch['source']
        text = p.read_text(encoding='utf-8')
        for edit in patch['exact_edits']:
            if text.count(edit['before']) != 1:
                raise ValueError('Guard edit does not match exactly once')
            text = text.replace(edit['before'], edit['after'])
        p.write_text(text, encoding='utf-8', newline='\n')
    for name, expected in spec['expected_normalized_source_sha256'].items():
        if sha(src/name) != expected:
            raise ValueError('Patched source hash mismatch: '+name)
    commands, logs, objects = [], [], []

    def run(command):
        commands.append(command)
        result = subprocess.run(command, cwd=output, capture_output=True, text=True, timeout=60)
        logs.append(result.stdout + result.stderr)
        (output/'build.log').write_text('\n'.join(logs), encoding='utf-8', newline='\n')
        if result.returncode:
            raise RuntimeError(result.stderr)

    for name in spec['sources']:
        obj = Path(name).stem+'.o'
        if obj in objects:
            raise ValueError('Duplicate object basename')
        objects.append(obj)
        run([str(gcc), '-O2', '-std=gnu99', '-fcommon', '-Wno-incompatible-pointer-types',
             '-Wno-implicit-function-declaration', '-Isrc', '-Isrc/jpeg-6b-steg',
             '-include', 'src/compat.h', '-c', 'src/'+name, '-o', obj])
    run([str(gcc), *objects, '-o', 'outguess.exe', '-lm', '-static'])
    report = {'schema': 'liberpedia-guarded-clean-build-v1', 'source_commit': revision,
              'compiler_version': version, 'compiler_sha256': sha(gcc),
              'build_script_sha256': sha(Path(__file__)), 'build_spec_sha256': sha(HERE/'build-spec.json'),
              'patch_audit_sha256': sha(HERE/'source-audit.json'),
              'source_hashes': spec['expected_normalized_source_sha256'],
              'commands': [[Path(c[0]).name, *c[1:]] for c in commands],
              'executable_sha256': sha(output/'outguess.exe'),
              'limits': 'Compilation only. No extraction validation or bit-identical executable guarantee. Compiler runtime/linker versions can affect binary bytes.'}
    (output/'build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Compiled', len(objects), 'fresh objects; executable SHA-256', report['executable_sha256'])


if __name__ == '__main__':
    main()
