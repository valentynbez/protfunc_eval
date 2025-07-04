#! /usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import gzip
from parsers import process_cath_hits, process_po2go, process_emapper
from Bio import SeqIO
import argparse


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
    parser = argparse.ArgumentParser(
        description="Run protein function prediction using DeepGO, Domain-PFP, FunFams, PO2GO, and eggNOG-mapper."
    )
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="Path to input FASTA file"
    )
    parser.add_argument(
        "-o", "--output", required=True, type=Path, help="Path to output directory"
    )
    parser.add_argument(
        "-t", "--threads", default=8, type=int, help="Number of CPU threads to use (default: 8)"
    )
    args = parser.parse_args()

    input_file = args.input.resolve()
    output_folder = args.output.resolve()
    threads = args.threads

    # stable output paths
    intermediate_folder = output_folder / "intermediate"
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

    # # ----------------- Domain-PFP Section ----------------- 
    print("[STEP] Running Domain-PFP predictions...")

    # open input file and split into single sequences
    with open(input_file, "r") as infile:
        headers, sequences = [], []
        for record in SeqIO.parse(infile, "fasta"):
            headers.append(record.id)
            sequences.append(str(record.seq))
        for header, seq in zip(headers, sequences):
            with open(f"predictions/intermediate/{header}.fa", "w") as outfile:
                outfile.write(f">{header}\n{seq}\n")

    domain_pfp_dir = Path("vendor/domain-pfp")
    inputs = intermediate_folder.glob("*.fa")
    for input_seq in inputs:
        domain_pfp_output = intermediate_folder / f"{input_seq.stem}_domain_pfp_go_preds.csv"
        cmd = (
            f"python3 predict_functions.py "
            f"--fasta {input_seq} "
            f"--outfile {domain_pfp_output} "
            f"--blast_flag --diamond_path {diamond_path}"
        )
        run_command(cmd, cwd=domain_pfp_dir)

    intermediate_preds = intermediate_folder.glob("*domain_pfp_go_preds.csv")
    with open(output_folder / "domain_pfp_go_preds.tsv", "w") as outfile:
        for pred_file in intermediate_preds:
            protein_id = pred_file.stem.split('_')[0]
            with open(pred_file, "r") as infile:
                next(infile)  # Skip header
                for line in infile:
                    tsv_line = line.strip().replace(",", "\t")
                    outfile.write(f"{protein_id}\t{tsv_line}\n")

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



