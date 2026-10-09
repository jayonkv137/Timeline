"""Create a self-contained offline HTML from the workspace production build."""
from pathlib import Path
import re
web=Path(__file__).resolve().parents[1];dist=web/'dist-workspace';html=(dist/'workspace.html').read_text()
css=next((dist/'assets').glob('*.css')).read_text();js=next((dist/'assets').glob('*.js')).read_text().replace('</script','<\\/script')
html=re.sub(r'<script[^>]+src="[^"]+"[^>]*></script>','',html)
html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>',lambda _: '<style>'+css+'</style>',html)
html=html.replace('</body>', '<script type="module">'+js+'</script></body>')
path=web/'cotrace-workspace.html';path.write_text(html);print(path, path.stat().st_size)
