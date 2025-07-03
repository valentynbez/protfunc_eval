import os
import psutil
import collections
import pyhmmer

example_fasta = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/data/deepgo2/data/example.fa"
hmms = "/nfs/cds-peta/exports/biol_micro_cds_gr_sunagawa/scratch/vbezshapkin/protfunc_eval/funfam-hmm3-v4_3_0.lib"
outfile = "example.out"
cath_threshold = 1e-3

from typing import List

Result = collections.namedtuple(
    "Result",
    [
        "protein",
        "name",
        "bitscore",
        "evalue",
        "protein_length",
        "domain_accession",
        "start",
        "end",
    ],
)


def write_intermediate(results: List[Result], outfile: str) -> None:
    """Write intermediate results to save RAM.
    Args:
        results (list): list of results
        outfile (str): path to output file

    Returns:
        None
    """
    with open(outfile, "w") as outfile_buffer:
        # get FunFams mapping file 
        fun_fams_mapping_file = os.path.join(
            os.path.dirname(__file__), "../data/funfam_mapping.tsv"
        )
        with open(fun_fams_mapping_file, "r") as mapping_file:
            go_tuples = [
                line.strip().split("\t") for line in mapping_file.readlines()
            ]

        for result in results:
             protein_name = result.protein
                if result.name in go_tuples:


def annotate_fasta(
    hmm_file: str,
    amino_acid_fasta_file: str,
    outfile: str,
    evalue: float = 1e-3,
    name: str = None,
    threads: int = 1,
) -> None:
    """Annotate fasta file with hmmscan.

    Args:
        hmm_file (str): path to hmm file.
        amino_acid_fasta_file (str): path to amino acid fasta file.
        outfile (str): path to output file.
        evalue (float): e-value threshold. Usually 1e-5 is enough, for virophage MCP suggested one is 1e-6.
        block_size (int): number of sequences to process in single batch. Saves RAM for large annotation jobs.
        threads (int): number of threads to use.

    Returns:
        None
    """

    # write header
    with open(outfile, "w") as outfile_buffer:
        outfile_buffer.write(
            "protein\thmm\tbitscore\tevalue\tprotein_length\tdomain_interpro_accession\tstart\tend\n"
        )

    # check memory requirements
    available_memory = psutil.virtual_memory().available
    proteins_size = os.stat(amino_acid_fasta_file).st_size
    database_size = os.stat(hmm_file).st_size
    input_size = proteins_size + database_size

    # run hmmsearch and get all results
    results = []

    # hmms
    with pyhmmer.plan7.HMMFile(hmm_file) as hmms:
        if name is not None:
            hmms = [h for h in hmms if name == h.name.decode("utf-8")]
            if len(hmms) == 0:
                raise ValueError(f"HMM {name} not found in {hmm_file}")

        # amino acid sequences
        with pyhmmer.easel.SequenceFile(
            amino_acid_fasta_file, digital=True
        ) as seq_file:
            if input_size < available_memory * 0.1:
                print("Pre-fetching targets into memory...")
                seqs = seq_file.read_block()
            else:
                seqs = seq_file

            for hits in pyhmmer.hmmer.hmmsearch(
                hmms, seqs, cpus=int(threads), E=float(evalue)
            ):
                phrog = hits.query_name.decode()  # get protein from the hit

                for hit in hits:
                    if hit.included:
                        protein = hit.name.decode()
                        prot_length = hit.length

                        for domain in hit.domains.reported:
                            raw_acc = (
                                domain.alignment.hmm_accession
                                or domain.alignment.hmm_name
                            )
                            accession = raw_acc.decode("utf-8")
                            start = domain.alignment.target_from
                            end = domain.alignment.target_to

                        results.append(
                            Result(
                                protein,
                                phrog,
                                hit.score,
                                hit.evalue,
                                prot_length,
                                accession,
                                start,
                                end,
                            )
                        )

        write_intermediate(results, outfile)
        