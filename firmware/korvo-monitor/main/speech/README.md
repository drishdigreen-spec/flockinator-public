# Speech samples (not shipped in this repository)

The Korvo firmware embeds ten spoken-event samples at build time
(`EMBED_FILES` in `../CMakeLists.txt`): `takeoff.pcm`, `seen.pcm`,
`friend.pcm`, `target.pcm`, `engage.pcm`, `assign.pcm`, `share.pcm`,
`rtb.pcm`, `crash.pcm`, `kill.pcm`. The build fails until files with
those names exist in this directory.

They are excluded from the public tree because the originals were
generated with a platform text-to-speech voice whose output terms are
the operator's to evaluate. Generate your own in the same format:

- Raw signed 16-bit little-endian PCM, mono, 16 kHz.
- At most three seconds each; keep levels modest (the reference set was
  attenuated to about 20% before conversion).
- Any short spoken phrase per event works; the state-to-phrase mapping
  is listed in the Korvo monitor README ("SD-card speech").

Example (macOS `say` + `ffmpeg`; any TTS + converter is equivalent):

```sh
say -v Karen -r 175 -o seen.aiff "Contact spotted"
ffmpeg -i seen.aiff -af volume=0.2 -f s16le -ac 1 -ar 16000 seen.pcm
```

On first boot the firmware copies the embedded defaults to
`/sdcard/flockinator/audio/`; samples on the card can then be replaced
without reflashing (see the Korvo monitor README).
