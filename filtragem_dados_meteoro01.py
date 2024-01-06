# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 10:31:54 2023

@author: LUIZ CLAUDIO CINDRA DE SOUZA
"""

import os
import pandas as pd
from pandas.errors import ParserError
import shutil
from pandas.errors import EmptyDataError
lista=[]
caminho__origem = r'C:\Users\aenge\Desktop\meteoro julho'
caminho_destino = r'C:\Users\aenge\Desktop\Nova pasta\erro'  
for root, dirs, files in os.walk(caminho__origem):
    for filename in files:
        try:
            try:
                df = pd.read_csv(f'{caminho__origem}\{filename}', sep=',', header=3 )
                df.columns = ['DATETIME','WIND_SPEED','WIND_DIR','TEMPERATURE','HUMIDITY','PRESSURE','BATTERY']
                num_colunas = len(df.columns)
                if num_colunas !=7:
                    lista.append(filename)
                try:
                    df1sum=df['WIND_SPEED']**1
                    df1sum=df['WIND_DIR']**1
                    df1sum=df['PRESSURE']**1
                    df1sum=df['HUMIDITY']**1
                    df1sum=df['TEMPERATURE']**1
                    df1sum=df['BATTERY']**1



                except TypeError:
                    lista.append(filename)                                  

            except EmptyDataError:
                lista.append(filename)
        except ParserError:
            lista.append(filename)           
for filename in lista: 
    caminho_arquivo = f'{caminho__origem}\{filename}'
    shutil.move(caminho_arquivo, caminho_destino)

# print(len(lista))
       
        


            # print(dfsum)
            # break
        
    

            
    

