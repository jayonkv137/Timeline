"""Build an offline HTML prototype and optional inline conversation preview."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--preview', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
fragment = (root / 'src/scene.html').read_text() + '\n<style>\n' + (root / 'src/styles.css').read_text() + '\n</style>\n'
for source in ('vendor/three.min.js', 'src/sample-data.js', 'src/brain.js'):
    fragment += '\n<script>\n' + (root / source).read_text() + '\n</script>\n'
document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>COTRACE · Brain study</title><style>body{margin:0;background:#080b10}#cotrace-brain{border-radius:0!important}</style></head><body>' + fragment + '</body></html>'
(root / 'cotrace-brain-prototype.html').write_text(document)
if args.preview:
    args.preview.write_text(fragment)
print('Built', root / 'cotrace-brain-prototype.html')
