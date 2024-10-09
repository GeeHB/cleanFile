#!/bin/python3
#
# coding=UTF-8
#
#   File     :   cleanFile.py
#
#   Auteur      :   JHB
#
#   Description :   Anonymisation d'un fichier au format csv
#                   Les numéro de tel. des colonnes données seront remplacés par des chaînes aléatoires
#                   Un fichier sera généré au format {path}/clean-{filename}.csv
#
#   Remarque    :   Nécessite Python 3
#
#   Version     :   0.2.2
#
#   Date        :   9 octobre 2024
#
#   Appel       :   ./cleanFile.py   [--src | -s {fichier source}
#                                    --col | -c {col1, col2, ..}]
#
#                                       ou
#                                   
#                                   [ --directory | -d {dossier}]
#
#                                       et
#
#                                   [--delim | -d {delimiteur de colonnes}]
#
#   Exemples     :   
#                       Nettoyage d'un fichier ./cleanFile.py --src ./source.csv --col 0 7 9
#
#                       Nettoyage d'un dossier ./cleanFile.py -f ./taxation/1
#

import os, csv, argparse

#
# Constantes
#

DEF_ENCODING   = "Windows-1252"

FILE_BASE_NAME = "clean-"       # Prefixe du fichier généré

LOG_BASE = 26                   # Génération d'un num. anonyme (alpha en base 26)
BASE_STRING = 'xxx'             # ... commençant par 

DEF_COL_COUNT = 4               # Par défaut, le nombre de colonnes par ligne

PARAM_FILE   = "--src"          # Paramètres de la ligne de commandes
PARAM_FILE_S = "-s"
COMMENT_FILE = "Fichier source"

PARAM_DIR    = "--folder"
PARAM_DIR_S  = "-f"
COMMENT_DIR  = "Dossier à analyser"

PARAM_COL    = "--col"
PARAM_COL_S  = "-c"
COMMENT_COL  = "Colonnes à anonymiser"

PARAM_DELIM  = "--delim"
PARAM_DELIM_S= "-d"
COMMENT_DELIM= "Délimiteur de colonnes"
DEF_DELIM    = ";"

DICT_FILE = "./.dict.csv" # Tableau associatif

# Type prédéfinis de fichiers
#
#   colonnes à anonymiser en fonction du nom du fichier
#
FILE_ENTRANT = "entrant"
LIST_ENTRANT = [1,2,4]

FILE_INTERNE = "interne"
LIST_INTERNE = [0, 1, 2, 3]

FILE_SORTANT = "sortant"
LIST_SORTANT = [0]

# cleanFile : Fichier anonymisé
#
class cleanFile(object):

    # Construction
    #
    def __init__(self, source : str, cols = None, delim = DEF_DELIM):
        
        # Nom du fichier de sortie
        self.__genName(source)
        
        # Récupération de la liste des dcolonnes à anonymiser
        if cols is not None :
            self.anonimyzedCols_ = cols
        else:
            self.anonimyzedCols_ = []

        self.delim_ = delim
        
        self.__loadDict()   # Chargement du dictionnaire (si il existe)
        self.values_ = []   # ... et la matrice de données est vide
        
        self.colID_ = 0     # Première case
        self.rowID_ = -1
        self.colCount_ = DEF_COL_COUNT

    #
    # Accès
    #
    def name(self):
        return self.outputName_
    def columns(self):
        return self.colCount_
    def lines(self):
        return self.rowID_
    
    # Ajout d'une ligne
    def addRow(self):
        cols = self.colCount_ if len(self.values_) == 0 else len(self.values_[0])
        self.values_.append(['' for _ in range(cols)])   # new empty line
        self.colID_ = 0
        self.rowID_+=1

    # Ajout d'une colonne
    def addColumn(self):
        self.colID_+=1

        # La première ligne a une longueur variable
        # alors que les suivantes ont la même taille que la première (une fois qu'elle est passée)
        if self.rowID_ == 0 and self.colID_ >= self.colCount_:
            self.colCount_+=1
            self.values_[0].append('')

    # Ajout d'une valeur
    def set(self, value):
        
        # Sommes-nous dans une colonne dont les valeurs doivent-être remplacées ?
        if self.__inAnonymizedCol():
            self.values_[self.rowID_][self.colID_] = self.__anonymize(value)
        else :
            # Non => copie de la valeur
            self.values_[self.rowID_][self.colID_] = value
    
    # Sauvegarde du fichier
    #
    def save(self):
        try:
            with open(self.outputName_, mode='w', encoding = DEF_ENCODING) as outputFile:
                outputWriter = csv.writer(outputFile, delimiter=self.delim_, quotechar='"', quoting=csv.QUOTE_MINIMAL)

                # Copie ligne à ligne
                for row in self.values_:
                    outputWriter.writerow(row)

            # Le "nouveau" fichier est généré, je peux conserver le dictionnaire
            self.__saveDict()

            return True # Généré avec succès
        except:
            return False
        #print(self.values_)

    # Génération du nom du fichier à partir du nom source
    #
    def __genName(self, name : str) -> str:
        path = os.path.split(name)
        self.outputName_ =  os.path.join(path[0], FILE_BASE_NAME + path[1])
        return self.outputName_

    # La colonne courante doit-elle être anonymisée ?
    #
    def __inAnonymizedCol(self):
        if len(self.anonimyzedCols_) > 0 and self.rowID_ > 0:
            for id in self.anonimyzedCols_:
                if id == self.colID_:
                    return True     # Oui, elle figure dans la liste (et ce n'est pas la 1ère ligne)
        return False

    # Transformation d'un nombre en son equivalent chaine en base 26
    #
    def __2String(self, src) -> str:
        
        if type(src) != "<type 'int'>" :
            source = int(src)
        else:
            source = src
        
        #orig = source
        digits = []
        while source:
            digits.append(int(source % LOG_BASE) + ord('a'))
            source //= LOG_BASE
        
        # Ajustement par la gauche
        left = BASE_STRING
        for _ in range(3 - len(digits)) :
            left += 'a'

        # Conversion
        for i in reversed(range(len(digits))):
            left += chr(digits[i])

        #print(f"{orig} : {left}")
        return left
    
    # Valeur de remplacement -> anonymisation (ou pas)
    #
    def __anonymize(self, value):
        # Il doit s'agir d'un numéro !
        try:
            if int(value) == 0:
                return value
        except ValueError:
            return value
          
        # Dans le dictionnaire ?
        if value in self.dict_:
            # oui => on retourne la valeur
            return self.dict_[value]
        
        # Sinon on l'ajoute
        newValue = self.__2String(len(self.dict_))
        self.dict_[value] = newValue

        # et on la retourne
        return newValue
    
    # Chargement du dictionnaire
    def __loadDict(self):
        
        # Le distionnaire d'anonymisation est vide
        self.dict_ = {}

        # Y a t'il un fichier d'une instance précédente ?
        try:
            with open(DICT_FILE, encoding=DEF_ENCODING) as dictFile:
                csvReader = csv.reader(dictFile, delimiter=delim)
                lineCount = 0
                for row in csvReader:
                    self.dict_[row[0]] = row[1] # ajout de l'entrée
                    lineCount+=1

            print(f"{lineCount} valeurs dans le dictionnaire")
        except:
            print("Erreur lors de la lecture du dictionnaire")
            self.dict_ = {}

    # Sauvegarde du catalogue
    def __saveDict(self):
        # Conversion en liste     
        myList = self.dict_.items()
        myList = list(myList)
        
        try:
            with open(DICT_FILE, mode='w', encoding = DEF_ENCODING) as dictFile:
                outputWriter = csv.writer(dictFile, delimiter=self.delim_, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in myList:
                    #print("ligne", row)
                    outputWriter.writerow(row)
        except:
            return 

# Analyse d'un fichier
#
def __cleanSingleFile(fName, delim, cols):
    # Le fichier source doit exister
    try:
        file = open(fName, 'r')
        file.close()
    except FileNotFoundError :
        print(f"Le fichier {fName} n'existe pas")
        exit(3)
    except IOError:
        print(f"Erreur lors de l'ouverture de {fName}")
        exit(3)

    print(f"Source : {fName}")
    print(f"Colonnes à analyser : {cols}")
    print(f"Séparateur de colonnes : \"{delim}\"")
    
    # "Création" du fichier anonymisé
    cFile = cleanFile(fName, cols, delim)

    # Transfert des valeurs des cellulles
    with open(fName, encoding=DEF_ENCODING) as csvFile:
        csvReader = csv.reader(csvFile, delimiter=delim)
        line_count = 0
        for row in csvReader:
            cFile.addRow()          # On commence par créer une ligne (avec une seule colonne)
            for val in row:
                cFile.set(val)
                cFile.addColumn()   # Colonne suivante
         
    # Terminé ...
    if cFile.save():
        print(f"Le fichier '{cFile.name()}' a été généré avec succès")
        print(f"\t - {cFile.columns()} cols x {cFile.lines()} lignes")

# Analyse de tous les fichiers d'un dossier (sans recursivité)
#
def __cleanFolder(folderName, delim, baseCols):
    print(f"Analyse du dossier {folderName}")
    for fileName in os.listdir(folderName):
        if not os.path.isdir(fileName): # c'est un fichier
            fullName = os.path.join(folderName, fileName) # nom complet

            # Choix des colonnes
            if -1 != fileName.find(FILE_ENTRANT) :
                cols = LIST_ENTRANT
            else :
                if -1 != fileName.find(FILE_SORTANT):
                    cols = LIST_SORTANT
                else:
                    if -1 != fileName.find(FILE_INTERNE):
                        cols = LIST_INTERNE
                    else:
                        cols = baseCols

            print(f"Colonnes : {cols}" )
            __cleanSingleFile(fullName, delim, cols)

#
# Point d'entrée du programme
#
if '__main__' == __name__:

    # Lecture de la ligne de commandes
    #
    parser = argparse.ArgumentParser()
    
    # Arguments mutuellement exclusifs
    source = parser.add_mutually_exclusive_group()
    source.add_argument(PARAM_FILE_S, PARAM_FILE, help = COMMENT_FILE, nargs=1)
    source.add_argument(PARAM_DIR_S, PARAM_DIR, help = COMMENT_DIR, nargs=1)

    parser.add_argument(PARAM_COL_S, PARAM_COL, help = COMMENT_COL, nargs='*')
    parser.add_argument(PARAM_DELIM_S, PARAM_DELIM, help = COMMENT_DELIM, required = False, nargs=1)
    
    args = parser.parse_args()

    # Vérification des paramètres
    delim = DEF_DELIM if args.delim is None else args.delim[0]

    # On récupère les colonnes (valeurs uniques)
    cols = []
    if args.col is not None:
        for s in args.col:
            x = int(s)
            if x not in cols:
                cols.append(x)
        
    if args.src is None:
        # C'est un dossier
        __cleanFolder(args.folder[0], delim, cols)
    else :
        # C'est un fichier    
        __cleanSingleFile(args.src[0], delim, cols)

# EOF
