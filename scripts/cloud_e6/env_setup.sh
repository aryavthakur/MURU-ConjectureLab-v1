#!/usr/bin/env bash
# E6 Cloud Environment Setup and Variable Export
# Strictly for environment activation. Does NOT execute any scientific experiment.

export MURU_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export VENV_DIR="/home/aryav_thakur/venv"
export JULIA_BIN_DIR="/home/aryav_thakur/julia-1.12.6/bin"
export JULIA_PROJECT_DIR="/home/aryav_thakur/muru_julia_env"

# Environment variables for PySR / JuliaCall / Juliapkg isolation
export PYTHON_JULIAPKG_EXE="${JULIA_BIN_DIR}/julia"
export PYTHON_JULIAPKG_PROJECT="${JULIA_PROJECT_DIR}"
export PYTHON_JULIAPKG_OFFLINE="yes"

# Thread capping to prevent oversubscription
export JULIA_NUM_THREADS="1"
export OMP_NUM_THREADS="1"
export MKL_NUM_THREADS="1"
export OPENBLAS_NUM_THREADS="1"
export NUMEXPR_NUM_THREADS="1"
export VECLIB_MAXIMUM_THREADS="1"

# Python path
export PYTHONPATH="${MURU_ROOT}/src:${MURU_ROOT}/scripts:${PYTHONPATH}"

# PATH
export PATH="${VENV_DIR}/bin:${JULIA_BIN_DIR}:${PATH}"

echo "MURU Cloud E6 environment exported successfully."
echo "Python: $(python --version)"
echo "Julia:  $(julia --version)"
