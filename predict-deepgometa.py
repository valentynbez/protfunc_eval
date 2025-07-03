#!/usr/bin/env python3

import subprocess
from pathlib import Path
from glob import glob

# Paths
input_file = Path(
    "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/vendor/deepgo2/data/example.fa"
).resolve()
output_folder = Path("predictions")
diamond_path = Path("/nfs/home/vbezshapkin/palm_annot/bin/diamond").resolve()

# Ensure output folder exists
output_folder.mkdir(parents=True, exist_ok=True)


def run_command(cmd, cwd=None):
    """Run a shell command and handle errors."""
    print(f"[RUNNING] {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}", file=sys.stderr)


def cleanup_file(file_path):
    """Delete a file if it exists."""
    if file_path.exists():
        print(f"[CLEANUP] Removing {file_path}")
        file_path.unlink()


def move_prediction_files(source_dir, tool_name):
    """Move prediction files to output folder with tool prefix."""
    for pred_file in glob(str(source_dir / "*preds*")):
        src = Path(pred_file)
        dest = output_folder / f"{tool_name}_{src.name}"
        print(f"[MOVE] {src} -> {dest}")
        src.rename(dest)


# ----------------- DeepGO Section -----------------
print("\n[STEP] Running DeepGO predictions...")

deepgo_tools = {
    "deepgo2": {
        "script": Path("vendor/deepgo2/predict.py"),
        "model": Path("vendor/deepgo2/data"),
    },
    # "deepgometa": {
    #     "script": Path("vendor/deepgometa/predict.py"),
    #     "model": Path("vendor/deepgometa/data"),
    # },
}

for name, config in deepgo_tools.items():
    script, model = config["script"], config["model"]

    if not (script.exists() and model.exists()):
        print(f"[WARNING] Skipping {name}: Missing script or model.")
        continue

    cmd = f"python3 {script} --data-root {model} -if {input_file}"
    run_command(cmd)

    # Cleanup intermediate ESM file
    cleanup_file(input_file.parent / "example_esm.pkl")

    # Move predictions to output folder
    move_prediction_files(input_file.parent, name)

# ----------------- Domain-PFP Section -----------------
print("\n[STEP] Running Domain-PFP predictions...")

domain_pfp_dir = Path("vendor/domain-pfp")
domain_pfp_output = output_folder / "domain_pfp_predictions.tsv"

cmd = (
    f"python3 predict_functions.py "
    f"--fasta {input_file} "
    f"--outfile {domain_pfp_output} "
    f"--blast_flag --diamond_path {diamond_path}"
)

if domain_pfp_dir.exists():
    run_command(cmd, cwd=domain_pfp_dir)
else:
    print(f"[WARNING] Domain-PFP directory {domain_pfp_dir} not found. Skipping.")

# ----------------- FunFams Section -----------------
print("\n[STEP] Running FunFams predictions...")

funfams_script = Path("vendor/funfams/apps/cath-genomescan.pl")
funfams_hmm_lib = Path("data/funfam-hmm3-v4_3_0.lib")

if funfams_script.exists() and funfams_hmm_lib.exists():
    cmd = f"{funfams_script} -i {input_file} -l {funfams_hmm_lib} -o {output_folder}"
    run_command(cmd)
else:
    print(f"[WARNING] Missing FunFams script or HMM library. Skipping.")

print("\n[INFO] All predictions complete. Results saved in:", output_folder.resolve())



# emapper.py
#     -i /nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/data/example.fa \
#     -o /nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/predictions \
#     --cpu 32 \
#     --data_dir /nfs/nas22/fs2202/biol_micro_sunagawa/Projects/EAN/PROPHAGE_REFSEQ_EAN/scratch/databases \
#     --sensmode ultra-sensitive --override

