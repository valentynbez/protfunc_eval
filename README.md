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
- Also downloads data for `FunFams`, `Domain-PFP`, `DeepGOMeta`, `DeepGO2`, `MSRep` 

### 2.2. `po2go` data
- go to a [Google Drive](https://drive.google.com/drive/folders/1P4ExHz0iFCXq5kwRqmAG8XXNZAvoQcX5) and download manually
- replace the paths in `predict-go.py`

## 3. Run `predict-go.py`
- since the only software that doesn't work within `deepgometa` environment is eggnog-mapper, this was unelegantly hacked with `conda run -n [cmd]`
- the script produces predictions from following tools
    - DeepGOMeta
    - DeepGO2
    - MSRep
    - Domain-PFP
    - FunFams
    - PO2GO
    - eggnog-mapper (v2.1.13, database version )