import sys
import requests
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyhmmer
import tqdm
import sys
import re
import threading
import requests
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyhmmer.plan7

# CATH version
version = "v4_3_0"

# Regex patterns
go_term_pattern = re.compile(r"GO:\d{7}")
ec_term_pattern = re.compile(r"\d+\.\d+\.\d+\.\d+")

# Lock for thread-safe writes
file_lock = threading.Lock()

# Output mapping files
go_mapping_file = f"cath_{version}_go_mapping.tsv"
ec_mapping_file = f"cath_{version}_ec_mapping.tsv"

# Clear existing files
open(go_mapping_file, "w").close()
open(ec_mapping_file, "w").close()


def process_hmm(hmm):
    try:
        superfamily, funfam_ID = hmm.split("-FF-", 1)
        cath_superfamily_ID = superfamily
        cath_funfam_ID = funfam_ID

        url = (
            f"http://www.cathdb.info/version/{version}/superfamily/"
            f"{cath_superfamily_ID}/funfam/{cath_funfam_ID}/files/stockholm"
        )

        response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)

        if response.ok:
            # Extract GO terms
            go_lines = [
                line.replace("#=GS ", "").replace("DR GO; ", "")
                for line in response.text.splitlines()
                if "DR GO;" in line
            ]
            go_terms = {term for line in go_lines for term in go_term_pattern.findall(line)}

            # Extract EC terms
            ec_lines = [
                line.replace("#=GS ", "").replace("DR EC; ", "")
                for line in response.text.splitlines()
                if "DR EC;" in line
            ]
            ec_terms = {term for line in ec_lines for term in ec_term_pattern.findall(line)}

            # Write mappings (thread-safe)
            with file_lock:
                with open(go_mapping_file, "a") as go_file:
                    for go_term in go_terms:
                        go_file.write(f"{hmm}\t{go_term}\n")
                with open(ec_mapping_file, "a") as ec_file:
                    for ec_term in ec_terms:
                        ec_file.write(f"{hmm}\t{ec_term}\n")

        else:
            print(f"[ERROR] Failed to fetch {hmm}: {response.status_code} {response.reason}", file=sys.stderr)

    except Exception as e:
        print(f"[EXCEPTION] Error processing {hmm}: {e}", file=sys.stderr)


def main():
    hmms_path = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/funfam-hmm3-v4_3_0.lib"
    with pyhmmer.plan7.HMMFile(hmms_path) as hmm_loader:
        hmm_cath = [h.name.decode("utf-8") for h in hmm_loader]

    print(f"[INFO] Loaded {len(hmm_cath)} HMMs from {hmms_path}")

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(process_hmm, hmm): hmm for hmm in hmm_cath}
        for future in tqdm.tqdm(as_completed(futures), total=len(futures), desc="Processing HMMs"):
            try:
                future.result()  # Wait for the thread to complete
            except Exception as e:
                print(f"[ERROR] Exception in thread for {futures[future]}: {e}")


if __name__ == "__main__":
    main()