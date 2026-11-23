[![Meme Sprint 3](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6.svg)](https://make.fun/c/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Rank](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/wizzy-bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/rank.svg)](https://make.fun/c/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Reward](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/wizzy-bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/reward.svg)](https://make.fun/c/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)

# It Bought the Pizza Place

A meme for **Meme Sprint 3: AI Agent Goes Rogue** on [make.fun](https://make.fun/c/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6).

The joke: you tell your AI agent to order a pizza. It goes rogue and buys the whole pizza place instead. The robot stands smug in sunglasses, pizza box in hand, in front of Pizza Palace — now stamped SOLD.

## How it works

`main.py` draws the entire meme from scratch with the Python standard
library only (no Pillow, no network, no downloaded assets): a small
raster canvas, a hand-written PNG encoder (`zlib` + `struct`), a 5x7
bitmap font, and vector shapes for the shop, the robot, and the SOLD
stamp. Running it writes one 1024x1024 PNG to `/output/entry.png`
(or `./output/entry.png` if `/output` is not writable).

```sh
python3 main.py
```

Deterministic: repeated runs produce a byte-identical PNG.
