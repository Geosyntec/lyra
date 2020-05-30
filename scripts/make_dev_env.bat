call conda activate base
call conda env remove -n lyra
call conda env create -f lyra\conda_env.yml
call conda activate lyra
call conda install -y --file lyra\requirements_conda.txt ^
  --channel conda-forge --channel defaults
call pip install ^
  -r lyra\requirements.txt ^
  -r lyra\requirements_test.txt
call conda activate base
