FROM mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt

RUN python -m pip install -r /tmp/requirements.txt

RUN python -m pip install --no-build-isolation --no-deps \
    git+https://github.com/bowang-lab/MedSAM.git@d71e8a1a99ad751840a22a7fa3ecfb4166fb1488

# Dependency validation.
#
# MedSAM 0.0.1 declares ipympl / ipywidgets / jupyterlab as unconditional
# install_requires. They are notebook-authoring tools with no role in
# inference, and --no-deps above deliberately skips them — but the installed
# dist-info still advertises them, so `pip check` reports them as missing and
# exits 1.
#
# Rather than drop the check, tolerate exactly those three package names and
# fail the build on anything else. A genuine problem — a real version conflict,
# or MedSAM requiring something that actually matters like torch — still fails.
RUN <<'SH'
set -eu

echo "--- pip check ---"
pip_out="$(python -m pip check 2>&1 || true)"
printf '%s\n' "$pip_out"

unexpected="$(printf '%s\n' "$pip_out" \
    | grep -v '^No broken requirements found\.$' \
    | grep -vE '^medsam [0-9.]+ requires (ipympl|ipywidgets|jupyterlab), which is not installed\.$' \
    | grep -v '^[[:space:]]*$' || true)"

if [ -n "$unexpected" ]; then
    echo
    echo "ERROR: unexpected dependency problems detected:"
    printf '%s\n' "$unexpected"
    exit 1
fi

echo "OK: dependency graph consistent (MedSAM notebook extras intentionally absent)"
SH

RUN python - <<'PY'
import numpy
import scipy
import cv2
import skimage
import pandas
import torch
import sklearn
import xgboost as xgb

print("numpy", numpy.__version__)
print("scipy", scipy.__version__)
print("cv2", cv2.__version__)
print("skimage", skimage.__version__)
print("pandas", pandas.__version__)
print("torch", torch.__version__)
print("sklearn", sklearn.__version__)
print("xgboost", xgb.__version__)

import numpy as np

m = xgb.XGBClassifier(n_estimators=2)
X = np.random.rand(20, 9)
y = np.random.randint(0, 2, 20)

m.fit(X, y)
m.save_model("/tmp/test.json")

m2 = xgb.XGBClassifier()
m2.load_model("/tmp/test.json")

print("✅ XGBoost save/load round-trip OK")
PY