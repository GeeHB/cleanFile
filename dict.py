#!/bin/python3
#
# coding=UTF-8
#
#   File     :   dict.py
#
#   Auteur      :   JHB
#
#   Description :   Classe dict : dictionnaire contenant les numéros remplacés avec leur items anaonymisés
#
#   Remarque    :   Nécessite Python 3
#

import csv

# dict : Dictionnaire
#
class dict(object):

    # Construction
    #
    def __init__(self, fileName):

        self.fileName_ = fileName
        self.__load()   # Chargement du dictionnaire (si il existe)

    #
    # Accès
    #

    # Nombres d'élements
    def len(self):
        return len(self.values_)

    # Rechargement
    def reload(self):
        self.save()
        self.__load()

    # Sauvegarde
    def save(self):
        # Conversion en liste
        myList = self.values_.items()
        myList = list(myList)

        try:
            with open(self.fileName_, mode='w') as dictFile:
                dictWriter = csv.writer(dictFile, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in myList:
                    dictWriter.writerow(row)
        except:
            return

    # Chargement du dictionnaire
    def __load(self):

        # Le distionnaire d'anonymisation est vide
        self.values_ = {}

        if 0 == len(self.fileName_):
            return False

        # Y a t'il un fichier d'une instance précédente ?
        try:
            with open(self.fileName_) as dictFile:
                csvReader = csv.reader(dictFile, delimiter=";")
                lineCount = 0
                for row in csvReader:
                    self.values_[row[0]] = row[1] # ajout de l'entrée

                return len(self.values_)
        except:
            self.values_ = {}
            return False


# EOF
