# Function prediction methods

## Instalation

Please, install `conda` on your computer to navigate different environments. It is necessary. 

## 1. Clone repository with submodules
```
git clone --recurse-submodules https://github.com/valentynbez/protfunc_eval
```

## 2. Install ALL environments from `envs` directory
Tools are built in a very messy way, it is what it is. **Please, do not rename environments**

### 2.1. `deepgometa` data 
- Run script `data_download.sh` 
- Might take a very, very long time.
- Also downloads data for `FunFams`, `DeepGOMeta`, `DeepGO2`, `eggnog-mapper`

### 2.2. `po2go` data
- go to a [Google Drive](https://drive.google.com/drive/folders/1P4ExHz0iFCXq5kwRqmAG8XXNZAvoQcX5) and download manually
- replace the paths in `predict-go.py`
### 2.3. Install repo 
In the root of the repository run:
```
pip install -e . 
```

## 3. Run `predict-go`
- since the only software that doesn't work within `deepgometa` environment is eggnog-mapper, this was unelegantly hacked with `conda run -n [cmd]`
- the script produces predictions from following tools
    - DeepGOMeta
    - DeepGO2
    - FunFams
    - PO2GO
    - eggnog-mapper (v2.1.13) 

Domain-PFP is broken, since it only processes a single function from a file, and I don't want to fix it. 

