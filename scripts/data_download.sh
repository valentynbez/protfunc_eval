# model downloads from KAUST are very slow, might take long time
mkdir -p data

# deepgo2 
wget https://deepgo.cbrc.kaust.edu.sa/data/deepgo2/data.tar.gz
# unpack into deepgo2/data
tar -xzf data.tar.gz -C deepgo2/data
rm data.tar.gz

# deepgometa
wget https://deepgo.cbrc.kaust.edu.sa/data/deepgometa/data.tar.gz
# unpack into deepgometa/data
tar -xzf data.tar.gz -C deepgometa/data
rm data.tar.gz

python download_eggnog_data.py --data_dir data

# download funfams hmms 
wget http://download.cathdb.info/cath/releases/all-releases/v4_3_0/sequence-data/funfam-hmm3-v4_3_0.lib.gz
# extract to data directory
gunzip -c funfam-hmm3-v4_3_0.lib.gz > data/funfam-hmm3-v4_3_0.lib 

# download domain-pfp data
mkdir -p vendor/domain-pfp/data
wget https://kiharalab.org/domainpfp/data.zip
unzip data.zip -d vendor/domain-pfp
wget https://kiharalab.org/domainpfp/saved_models.zip
unzip saved_models.zip -d vendor/domain-pfp
wget https://kiharalab.org/domainpfp/blast_ppi_database.zip
unzip blast_ppi_database.zip -d vendor/domain-pfp
