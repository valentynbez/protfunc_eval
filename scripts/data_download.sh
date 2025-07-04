# FILES FOR PO2GO need TO BE ADDED MANUALLY
# https://drive.google.com/drive/folders/1P4ExHz0iFCXq5kwRqmAG8XXNZAvoQcX5

# model downloads from KAUST are very slow, might take long time
mkdir -p data

# deepgo2 
wget https://deepgo.cbrc.kaust.edu.sa/data/deepgo2/data.tar.gz
# unpack into deepgo2/data
mkdir -p vendor/deepgo2/data
tar -xzf data.tar.gz -C vendor/deepgo2/data
rm data.tar.gz

# deepgometa
wget https://deepgo.cbrc.kaust.edu.sa/data/deepgometa/data.tar.gz
# unpack into deepgometa/data
mkdir -p vendor/deepgometa/data
tar -xzf data.tar.gz -C vendor/deepgometa/data
rm data.tar.gz

# download funfams hmms 
wget http://download.cathdb.info/cath/releases/all-releases/v4_3_0/sequence-data/funfam-hmm3-v4_3_0.lib.gz
# extract to data directory
gunzip -c funfam-hmm3-v4_3_0.lib.gz > data/funfam-hmm3-v4_3_0.lib 
# check and move hmmsearch to a proper place within funfams directory
HMMSEARCH_PATH=$(which hmmsearch)
mkdir -p vendor/funfams/bin/hmmer3
if [ -z "$HMMSEARCH_PATH" ]; then
    echo "hmmsearch not found in PATH. Please install hmmer3 and add it to PATH."
else
    cp $HMMSEARCH_PATH vendor/funfams/bin/hmmer3/
fi

# download domain-pfp data
mkdir -p vendor/domain-pfp/data
wget https://kiharalab.org/domainpfp/data.zip
unzip data.zip -d vendor/domain-pfp
wget https://kiharalab.org/domainpfp/saved_models.zip
unzip saved_models.zip -d vendor/domain-pfp
wget https://kiharalab.org/domainpfp/blast_ppi_database.zip
unzip blast_ppi_database.zip -d vendor/domain-pfp
