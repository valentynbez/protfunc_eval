import gzip
from collections import defaultdict
from pathlib import Path
import re

# # Paths
# cath_file = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/predictions/example.crh"
# mapping_file = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/data/cath_v4_3_0_go_mapping.tsv.gz"
# output_file = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/predictions/protein_go_annotations.tsv"

# # Run processing
# process_cath_hits(cath_file, mapping_file, output_file)


def process_emapper(raw_result: str, output_file: str):
    with open(raw_result, "r") as infile, open(output_file, "w") as outfile:
        for line in infile:
            if line.startswith("#"):
                continue
            else:
                # GO is a 10th column
                columns = line.strip().split("\t")
                protein_name = columns[0]
                go_terms = columns[9].split(",")
                for term in go_terms:
                    outfile.write(f"{protein_name}\t{term}\t1\n")



def process_po2go(raw_result: str, output_file: str):
    """
    Process the output from PO2GO predictions and extract GO terms.
    Args:
        infile (str): Path to the raw PO2GO output file.
        output_file (str): Path to the final output file.
    """

    go_pattern = re.compile(r"GO:\d{7}")
    with open(raw_result, "r") as infile, open(output_file, "w") as outfile:
        next(infile)  # Skip header
        for line in infile:
            _, prot_name, go_terms = line.strip().split(",", 2)
            go_terms = go_pattern.findall(go_terms)
            for term in go_terms:
                outfile.write(f"{prot_name}\t{term}\t1\n")


def load_funfam_go_mapping(mapping_file: Path) -> dict[str, list[str]]:
    """
    Load FunFam to GO term mappings from a gzipped TSV file.

    Args:
        mapping_file (Path): Path to gzipped mapping file.

    Returns:
        dict[str, list[str]]: Mapping of FunFam IDs to GO terms.
    """
    funfams_to_go = defaultdict(list)
    with gzip.open(mapping_file, "rt") as f:
        for line in f:
            funfam_id, go_term = line.strip().split("\t")
            funfams_to_go[funfam_id].append(go_term)
    return funfams_to_go


def load_cath_hits(cath_file: Path) -> dict[str, list[str]]:
    """
    Load CATH hits from file and map proteins to FunFam IDs.

    Args:
        cath_file (Path): Path to CATH hits file.

    Returns:
        dict[str, list[str]]: Mapping of protein IDs to FunFam IDs.
    """
    protein_to_funfams = defaultdict(list)
    with cath_file.open("r") as f:
        for line in f:
            if line.startswith("#"):
                continue  # Skip header/comment lines
            parts = line.strip().split()
            if len(parts) >= 2:
                protein_id, funfam_id = parts[0], parts[1]
                protein_to_funfams[protein_id].append(funfam_id)
    return protein_to_funfams


def write_go_annotations(
    protein_to_funfams: dict[str, list[str]],
    funfams_to_go: dict[str, list[str]],
    output_file: Path,
):
    """
    Write GO annotations for proteins based on FunFam mappings.

    Args:
        protein_to_funfams (dict): Protein-to-FunFam mapping.
        funfams_to_go (dict): FunFam-to-GO mapping.
        output_file (Path): Output file path.
    """
    with output_file.open("w") as f:
        for protein_id, funfam_ids in protein_to_funfams.items():
            for funfam_id in funfam_ids:
                go_terms = funfams_to_go.get(funfam_id, [])
                for go_term in go_terms:
                    f.write(f"{protein_id}\t{go_term}\t1\n")


def process_cath_hits(cath_file: str, mapping_file: str, output_file: str):
    """
    Main function to process CATH hits and annotate with GO terms.

    Args:
        cath_file (str): Path to CATH hits file.
        mapping_file (str): Path to gzipped FunFam-to-GO mapping file.
        output_file (str): Path to output file.
    """
    cath_file = Path(cath_file)
    mapping_file = Path(mapping_file)
    output_file = Path(output_file)

    print("[INFO] Loading FunFam-GO mappings...")
    funfams_to_go = load_funfam_go_mapping(mapping_file)

    print("[INFO] Loading CATH hits...")
    protein_to_funfams = load_cath_hits(cath_file)

    print(f"[INFO] Writing GO annotations to {output_file}...")
    write_go_annotations(protein_to_funfams, funfams_to_go, output_file)

    print("[DONE] Annotation complete.")
