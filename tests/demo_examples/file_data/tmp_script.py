#! /usr/bin/env python
chromosome_lengths = {
    "1": 247249719,
    "2": 242951149,
    "3": 199501827,
    "4": 191273063,
    "5": 180857866,
    "6": 170899992,
    "7": 158821424,
    "8": 146274826,
    "9": 140273252,
    "10": 135374737,
    "11": 134452384,
    "12": 132349534,
    "13": 114142980,
    "14": 106368585,
    "15": 100338915,
    "16": 88827254,
    "17": 78774742,
    "18": 76117153,
    "19": 63811651,
    "20": 62435964,
    "21": 46944323,
    "22": 49691432,
    "X": 154913754,
    "Y": 57772954}


with open("coverage_data.txt") as file:
    print("chr\tpos\tcov\tchr_len")
    for idx, line in enumerate(file):
        if idx == 0: continue
        chrm, pos, cov = line.strip().split("\t")
        chr_len = chromosome_lengths[chrm]
        print(f"{chrm}\t{pos}\t{cov}\t{chr_len}")