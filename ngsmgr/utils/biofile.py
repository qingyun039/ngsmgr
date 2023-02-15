def fasta_dict_file(fastafile):
    """参考基因组fasta文件的dict文件"""
    if fastafile[-3:] == '.fa':
        return fastafile[:-3] + '.dict'
    if fastafile[-6:] == '.fasta':
        return fastafile[:-6] + '.dict'