"""htdemucs_ft: her kaynak için kendi uzman modeli (weights_only=True ile güvenli yükleme)."""
import fractions
import sys

import numpy as np
import soundfile as sf
import torch
from demucs.apply import apply_model
from demucs.htdemucs import HTDemucs

repo, inp, outdir = sys.argv[1:4]
MODELS = {"drums": "f7e0c4bc-ba3fe64a", "bass": "d12395a8-e57c48e6", "other": "92cfc3b6-ef3bcb9c",
          "vocals": "04573f0d-f3cf25b2"}
allowed = [HTDemucs, fractions.Fraction, np.dtype, (np._core.multiarray.scalar, "numpy.core.multiarray.scalar")]
allowed += [type(np.dtype(t)) for t in ("float32", "float64", "int64", "int32")]
wav, sr = sf.read(inp, dtype="float32", always_2d=True)
x = torch.from_numpy(wav.T.copy())
ref = x.mean(0)
mu, sd = ref.mean(), ref.std()
torch.set_num_threads(4)
for src, name in MODELS.items():
    with torch.serialization.safe_globals(allowed):
        pkg = torch.load(f"{repo}/{name}.th", map_location="cpu", weights_only=True)
    model = HTDemucs(*pkg["args"], **pkg["kwargs"])
    model.load_state_dict(pkg["state"])
    model.eval()
    with torch.no_grad():
        y = apply_model(model, ((x - mu) / sd)[None], shifts=2, split=True, overlap=0.25, progress=False)[0]
    y = (y * sd + mu)[model.sources.index(src)].numpy().T
    sf.write(f"{outdir}/{src}.wav", y, sr)
    print(src, "ok", flush=True)
