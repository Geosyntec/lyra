#! /usr/bin/env sh

conda activate base
conda env remove -n lyra
conda env create -f lyra/conda_env.yml
conda activate lyra
conda install -y --file lyra/requirements_conda.txt \
  --channel conda-forge --channel defaults
pip install \
  -r lyra/requirements.txt \
  -r lyra/requirements_test.txt
conda activate base
