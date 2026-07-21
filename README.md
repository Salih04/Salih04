<div align="center">

<table>
<tr>
<td valign="top" width="50%">
<img src="outputs/portrait.svg" width="100%" alt="ASCII portrait" />
</td>
<td valign="top" width="50%">
<img src="outputs/whoami.svg" width="100%" alt="whoami terminal animation" />
</td>
</tr>
</table>

</div>

## Regenerating

Both panels are terminal recordings converted to animated SVGs.

```bash
# 1. record (asciinema 2.x, so svg-term-cli can read the cast)
pipx install asciinema==2.4.0
TERM=xterm-256color asciinema rec --cols 80 --rows 24 -c "bash scripts/whoami.sh" outputs/whoami.cast
TERM=xterm-256color asciinema rec --cols 82 --rows 42 -c "bash scripts/portrait.sh outputs/portrait_ascii.txt" outputs/portrait.cast

# 2. convert to SVG
npm install -g svg-term-cli
svg-term --in outputs/whoami.cast   --out outputs/whoami.svg   --window --no-cursor
svg-term --in outputs/portrait.cast --out outputs/portrait.svg --window --no-cursor
```

To swap in a different photo for the portrait panel, crop it to a tight
head-and-shoulders shot first (less background = a cleaner silhouette), then:

```bash
python3 -m venv .venv && .venv/bin/pip install Pillow numpy
.venv/bin/python3 scripts/img_to_ascii.py <your-cropped-photo> outputs/portrait_ascii.txt 78
```

`img_to_ascii.py` pushes bright, non-skin-toned pixels (sky, haze, foliage) to
white so only the subject renders, then maps grayscale to ASCII density
characters. Re-record `portrait.cast` afterwards with the command above.
