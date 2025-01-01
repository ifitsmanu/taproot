#!/usr/bin/env bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DIR=$(realpath ${SCRIPT_DIR}/..)
PYTHONPATH=$DIR/src/:$PYTHONPATH
export PYTHONPATH

export CUDA_MODULE_LOADING=LAZY
export KMP_DUPLICATE_LIB_OK=TRUE

if [ "${CONDA_PREFIX}" != "" ]; then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/
fi

CUDNN_PATH=$(python -c "import nvidia.cudnn; print(nvidia.cudnn.__file__)" 2> /dev/null)
if [ "${CUDNN_PATH}" != "" ]; then
    CUDNN_PATH=$(dirname ${CUDNN_PATH})
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDNN_PATH/lib
fi

python -m taproot "$@"
