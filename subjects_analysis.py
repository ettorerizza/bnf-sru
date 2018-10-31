# coding: utf-8
"""
Extraction de l'indexation sujet d'un corpus de notices
pour évaluation statistique
L'objectif est de trouver des méthodes de comparaison
entre indexation automatisée et indexation manuelle
qui ne s'appuie pas sur une comparaison portant sur le même corpus
(sortir de l'évaluation par le rappel et la précision)
Pistes :
    - graphe des concepts (complexité, liens)
    - dispersion
"""

from collections import defaultdict

from stdf import create_file, line2report, close_files
import SRUextraction as sru


def analyse(url, fields, max_records, output_filename):
    output_file = create_file(output_filename)
    nb_results = sru.query2nbresults(url)
    metas = defaultdict(list)
    if nb_results < max_records:
        max_records = nb_results
    i = 1
    print("Nombre total de résultats : ", nb_results)
    while i < max_records:
        page_of_results(url, fields, i, max_records, metas, output_file)
        i += 1000
    EOT([output_file])


def page_of_results(url, fields, i, max_records, metas, output_file):
    query, url_root, params = sru.url2params(url)
    params["maximumRecords"] = "1000"
    if (max_records < int(params["maximumRecords"])):
        params["maximumRecords"] = str(max_records)
    params["startRecord"] = str(i)
    results = sru.SRU_result(query, url_root, params)
    for recordid in results.dict_records:
        if (i <= max_records):
            dict_metas_record = extract_metas(
                                    recordid,
                                    results.dict_records[recordid]["record"],
                                    fields)
            metas[recordid] = dict_metas_record
            print(i, recordid, str(dict_metas_record))
            i += 1
    output_file.write(str(metas))


def extract_metas(recordid, xml_record, fields):
    """
    Extraction des informations pour une notice
    Si une notice contient :
    600 .. $3 12032352 $a Stanislas $u 2 Auguste Poniatowski
           $h II Auguste Poniatowski $e roi de Pologne $d 1732-1798
    606 .. $3 11939093 $a Guerre mondiale $g 1914-1918
           $3 11934225 $x Historiographie
    607 .. $3 11957734 $a Varsovie $g Pologne
           $3 14533294 $z +* 1800......- 9900......+:1800-....:
    607 .. $3 11932826 $a Pologne $x Histoire
    607 .. $3 12033836 $a Pologne $x Relations extérieures
           $3 11934444 $x Histoire
    La liste en sortie sera :
    ['600':
        [
            ["12032352"]
        ],
     '606':
        [
            ["11939093", "11934225"]
        ],
     '607':
        [
            ["11957734", "14533294"],
            ["11932826"],
            ["12033836", "11934444"]
        ]

    """
    list_metas = []
    for field in fields:
        field_values = extract_values(recordid, xml_record, field, list_metas)
        if field_values:
            list_metas.append({field: field_values})
    return list_metas


def extract_values(recordid, xml_record, fieldname, list_metas):
    """
    Doit renvoyer une liste de listes
    Par exemple
    [
            ["11957734", "14533294"],
            ["11932826"],
            ["12033836", "11934444"]
        ]
    """
    liste_values = []
    for field in xml_record.xpath(f"*[@tag='{fieldname}']"):
        field_val = []
        if field.find("*[@code='3']") is not None:
            for subf3 in field.xpath("*[@code='3']"):
                field_val.append(subf3.text)
        else:
            for subf in field.xpath("*"):
                code = subf.get("code")
                subf_list = "abcdefghijlmnopqrstuvwxyz"
                if code in subf_list:
                    field_val.append(subf.text)
        liste_values.append(field_val)
    return liste_values


def EOT(list_files):
    close_files(list_files)


if __name__ == "__main__":
    fields = input("Liste des zones contenant l'indexation : ")
    url = input("URL du SRU à interroger (requête complète) : ")
    max_records = int(input("Nombre max de résultats à analyser : "))
    output_filename = input("Nom du rapport : ")
    print("\n", "-"*20, "\n")
    fields = fields.split(";")
    if (len(fields) == 1):
        fields = fields[0].split(",")
    analyse(url, fields, max_records, output_filename)