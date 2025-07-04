#! /usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import gzip
from utils import process_cath_hits, process_po2go, process_emapper


def run_command(cmd, cwd=None):
    """Run a shell command and handle errors."""
    print(f"[RUNNING] {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}", file=sys.stderr)
        sys.exit(1)

def cleanup_file(file_path):
    """Delete a file if it exists."""
    if file_path.exists():
        print(f"[CLEANUP] Removing {file_path}")
        file_path.unlink()

def move_and_concat_prediction_files(source_dir: Path, tool_name: str, output_folder: Path):
    """
    Concatenate all gzipped prediction files in source_dir and move as a single gzipped file to output_folder.
    """
    pred_files = list(source_dir.glob("*preds*.gz"))
    if not pred_files:
        print(f"[WARN] No gzipped prediction files found in {source_dir}")
        return

    combined_file = output_folder / f"{tool_name}_go_preds.tsv"
    print(f"[CONCAT] Combining {len(pred_files)} gzipped files into {combined_file}")

    with open(combined_file, "w") as outfile:
        for pred_file in pred_files:
            with gzip.open(pred_file, "rt") as infile:
                for line in infile:
                    outfile.write(line)
            # Remove the original file after concatenation
            pred_file.unlink()

    print(f"[DONE] Combined gzipped predictions saved to: {combined_file}")


def main():
    # user input
    input_file = Path(
        "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/data/example.fa"
    ).resolve()
    output_folder = Path("predictions").resolve()

    # stable output paths
    intermediate_folder = output_folder / "intermediate"
    domain_pfp_output = intermediate_folder / "domain_pfp_go_preds.csv"
    po2go_output = intermediate_folder / "po2go_go_preds.csv"
    po2go_final = output_folder / "po2go_go_preds.tsv"
    threads = 16

    # Resolve diamond path
    diamond_path = subprocess.run(
        "which diamond", shell=True, capture_output=True, text=True
    ).stdout.strip()
    if not diamond_path:
        print("[ERROR] Diamond executable not found. Please install Diamond and ensure it's in your PATH.")
        sys.exit(1)
    diamond_path = Path(diamond_path).resolve()

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # ----------------- DeepGO Section -----------------
    print("[STEP] Running DeepGO predictions...")

    deepgo_tools = {
        "deepgo2": {
            "script": Path("vendor/deepgo2/predict.py"),
            "model": Path("vendor/deepgo2/data"),
        },
        "deepgometa": {
            "script": Path("vendor/deepgometa/predict.py"),
            "model": Path("vendor/deepgometa/data"),
        },
    }

    for name, config in deepgo_tools.items():
        script, model = config["script"], config["model"]

        if not (script.exists() and model.exists()):
            print(f"[WARNING] Skipping {name}: Missing script or model.")
            continue

        cmd = f"python3 {script} --data-root {model} -if {input_file} --device cpu"
        run_command(cmd)

        # Cleanup intermediate ESM file
        cleanup_file(input_file.parent / "example_esm.pkl")

        # Move predictions to output folder
        move_and_concat_prediction_files(input_file.parent, name, output_folder)

    # # ----------------- Domain-PFP Section ----------------- BROKEN!
    # print("[STEP] Running Domain-PFP predictions...")

    # domain_pfp_dir = Path("vendor/domain-pfp")
    # cmd = (
    #     f"python3 predict_functions.py "
    #     f"--fasta {input_file} "
    #     f"--outfile {domain_pfp_output} "
    #     f"--blast_flag --diamond_path {diamond_path}"
    # )

    # if domain_pfp_dir.exists():
    #     run_command(cmd, cwd=domain_pfp_dir)
    # else:
    #     print(f"[WARNING] Domain-PFP directory {domain_pfp_dir} not found. Skipping.")
    # # Open output csv and rewrite as tsv
    # with open(domain_pfp_output, "r") as infile, open(output_folder / "domain_pfp_go_preds.tsv", "w") as outfile:
    #     for line in infile:
    #         outfile.write(line.replace(",", "\t"))


    # ----------------- FunFams Section -----------------
    print("[STEP] Running FunFams predictions...")
    funfams_script = Path("vendor/funfams/apps/cath-genomescan.pl")
    funfams_hmm_lib = Path("data/funfam-hmm3-v4_3_0.lib")

    if funfams_script.exists() and funfams_hmm_lib.exists():
        cmd = f"{funfams_script} -i {input_file} -l {funfams_hmm_lib} -o {intermediate_folder}"
        run_command(cmd)
    else:
        print(f"[WARNING] Missing FunFams script or HMM library. Skipping.")

    process_cath_hits((intermediate_folder / input_file.name.split('.')[0]).with_suffix(".crh"),
                      Path("data/cath_v4_3_0_go_mapping.tsv.gz"),
                      output_folder / "funfams_go_preds.tsv")

    # ----------------- PO2GO Section -----------------
    print("[STEP] Running PO2GO predictions...")

    cmd = (
        f"python vendor/po2go/inference_fasta_cpu.py "
        f"-i {input_file} "
        f"-o {po2go_output} "
        f"--terms-file data/terms_annotated_embeddings.pkl "
        f"--resume data/model_best.pth.tar -T {threads}"
    )
    run_command(cmd)
    
    process_po2go(po2go_output, po2go_final)

    print("[INFO] All predictions complete. Results saved in:", output_folder)

    # ------- eggnog-mapper Section -------
    cmd = f"""emapper.py \
    -i {input_file} \
    -o {intermediate_folder}/go_preds \
    --cpu {threads} \
    --data_dir data \
    --sensmode ultra-sensitive --override \
    --temp_dir {intermediate_folder} \
    """

    # run with conda run 
    run_command(f"conda run -n eggnog {cmd}")

    # # process emapper output
    raw_result = intermediate_folder / "go_preds.emapper.annotations"
    final_result = output_folder / "emapper_go_preds.tsv"
    process_emapper(raw_result, final_result)


if __name__ == "__main__":
    main()



