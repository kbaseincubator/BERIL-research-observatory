CREATE TABLE gtdb_species_clade (
    gtdb_species_clade_id STRING,
    representative_genome_id STRING,
    GTDB_species STRING,
    GTDB_taxonomy STRING,
    ANI_circumscription_radius DOUBLE,
    mean_intra_species_ANI DOUBLE,
    min_intra_species_ANI DOUBLE,
    mean_intra_species_AF DOUBLE,
    min_intra_species_AF DECIMAL(10,4),
    no_clustered_genomes_unfiltered INT,
    no_clustered_genomes_filtered INT
);
