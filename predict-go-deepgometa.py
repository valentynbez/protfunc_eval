# predict DeepGO2 and DeepGOMeta
import os
import sys
from glob import glob

input_file = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/vendor/deepgo2/data/example.fa"
output_folder = "predictions"
diamond_path = "/nfs/home/vbezshapkin/palm_annot/bin/diamond"


input_file = os.path.abspath(input_file)
# Create output folder if it does not exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

################### DeepGO ####################
print("Running DeepGO predictions...")
# Paths to prediction scripts and models
deepgos = {
    "deepgo2": {
        "script": "vendor/deepgo2/predict.py",
        "model": "vendor/deepgo2/data"
    },
    # "deepgometa": {
    #     "script": "vendor/deepgometa/predict.py",
    #     "model": "vendor/deepgometa/data"
    # }
}

# DeepGO prediction command
for name, config in deepgos.items():
    script = config["script"]
    model = config["model"]
    cmd = (
        f"python3 {script} "
        f"--data-root {model} "
        f"-if {input_file}"
    )

    if os.path.exists(script) and os.path.exists(model):
        os.system(cmd)

    # remove esm file in input folder
    esm_file = os.path.join(os.path.dirname(input_file), "example_esm.pkl")
    if os.path.exists(esm_file):
        os.remove(esm_file)

    preds = glob(os.path.join(os.path.dirname(input_file), "*preds*"))
    for pred_file in preds:
        if os.path.exists(pred_file):
            # add name with _ to prediction file
            new_pred_file = os.path.join(output_folder, f"{name}_{os.path.basename(pred_file)}")
            os.rename(pred_file, new_pred_file)


######### Domain-PFP ################
print("Running Domain-PFP predictions...")
# only possible to run in the domain-pfp folder
os.chdir("vendor/domain-pfp")
# Domain-PFP prediction command
output_file = os.path.join(output_folder, "domain_pfp_predictions.tsv")
cmd = f"""python3 predict_functions.py --fasta {input_file} --outfile {output_file} --blast_flag --diamond_path {diamond_path}"""
os.system(cmd)
os.chdir("../..")  # Go back to the original directory



