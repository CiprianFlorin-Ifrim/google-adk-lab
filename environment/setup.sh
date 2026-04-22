#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------
# ADK Environment Setup
#
# Creates a conda environment, installs Python dependencies, registers
# a Jupyter kernel, and pulls the Ollama model.
#
# Prerequisites:
#   - miniconda or anaconda installed
#   - ollama installed and running (https://ollama.com)
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# -----------------------------------------------------------------------

ENV_NAME="adk-env"
PYTHON_VERSION="3.13"
OLLAMA_MODEL="gemma4:e4b"

echo "--- checking prerequisites ---"

if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found. Install miniconda first."
    echo "       https://docs.anaconda.com/miniconda/"
    exit 1
fi

if ! command -v ollama &> /dev/null; then
    echo "ERROR: ollama not found. Install ollama first."
    echo "       https://ollama.com"
    exit 1
fi

echo "--- creating conda environment: ${ENV_NAME} ---"

if conda info --envs | grep -q "^${ENV_NAME} "; then
    echo "environment ${ENV_NAME} already exists, updating"
else
    conda create -n "${ENV_NAME}" python="${PYTHON_VERSION}" -y
fi

echo "--- activating environment ---"

eval "$(conda shell.bash hook)"
conda activate "${ENV_NAME}"

echo "--- installing python dependencies ---"

pip install --upgrade pip
pip install -r requirements.txt

echo "--- registering jupyter kernel ---"

python -m ipykernel install --user --name "${ENV_NAME}" --display-name "${ENV_NAME}"

echo "--- pulling ollama model: ${OLLAMA_MODEL} ---"

ollama pull "${OLLAMA_MODEL}"

echo ""
echo "--- setup complete ---"
echo ""
echo "to activate:  conda activate ${ENV_NAME}"
echo "to run:       cd notebooks && jupyter lab"
echo "ollama model:  ${OLLAMA_MODEL}"
echo ""
echo "make sure ollama is running before starting notebooks."
