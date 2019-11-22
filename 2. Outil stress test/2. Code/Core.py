# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 12:14:36 2019

@author: b79534
"""
import pandas as pd
import numpy as np

def get_projection(path,stock_file,parameter_file):
    #Import du fichier stock
    stock=pd.read_csv(path+stock_file,sep=';',decimal=',')
    #Conversion des taux de provision en montant de provision
    stock[['Prov S1','Prov S2', 'Prov S3']]=stock[['Exp S1','Exp S2', 'Exp S3']].mul(
            stock[['Prov S1','Prov S2', 'Prov S3']].rename(
                    columns={'Prov S1':'Exp S1','Prov S2':'Exp S2','Prov S3':'Exp S3'}))
    stock=stock.groupby(by=['Segment','Date']).sum().reset_index()
    #Ajout d'une colonne Old S3 (montant de provision S3 avant projection)
    stock['Prov Old S3']=stock['Prov S3']
    
    #Import du fichier de paramètres
    parameter=pd.read_csv(path+parameter_file,sep=';',decimal=',')
    #Creation des taux de transition depuis le Stage 3 (absorbant)
    parameter['TR31']=0.
    parameter['TR32']=0.
    parameter['TR33']=1.
    
    #Année du stock
    starting_year=stock.Date[0]
    #Première année de projection
    first_year=parameter.Date.min()
    #Dernière année de projection
    final_year=parameter.Date.max()
    #Liste des scenarii
    scenarii=['Baseline','Adverse']
    
    print('Starting Point: '+str(starting_year))
    print('Projection over  '+str(parameter.Date.unique().size) + ' years')
    print('First year  '+str(first_year))
    print('Final year  '+str(final_year))
    #Test sur les dates
    test1=(starting_year+1==first_year)
    test2=True
    test3=True
    tmp=starting_year
    for i in parameter.Date.unique():
        if i!=tmp+1:
            test2=False
        tmp=i
    for i in stock.Segment.unique():
        if i not in parameter.Segment.unique():
            test3=False
    print('La projection commence à l\'année suivant le starting point: ' + str(test1))
    print('Les dates de projection se suivent: ' + str(test2))
    print('Tous les segments du stock sont présent dans la table de paramètres: ' + str(test3))
    
    #Initialisation du dataframe de projection (copie du stock originale dans une version baseline et une version adverse)
    df_tmp=stock.copy()
    df_tmp['Scenario']='Baseline'
    projection=df_tmp.copy()
    df_tmp['Scenario']='Adverse'
    projection=pd.concat([projection,df_tmp])
    for i in range(first_year,final_year+1):
        for j in scenarii: 
            df_tmp['Date']=i
            df_tmp['Scenario']=j
            projection=pd.concat([projection,df_tmp])
    
    #Merge des paramètres avec la base de projection
    projection=projection.merge(parameter, how='left', on=['Segment','Date','Scenario'])
    #Projection de l'exposition
    for i in range(first_year,final_year+1):
        for j in scenarii:
            #Définition des filtres
            n=(projection['Date']==i)
            n_1=(projection['Date']==(i-1))
            n_next=(projection['Date']==(i+1))
            n_init=(projection['Date']==starting_year)
            scen=(projection['Scenario']==j)
            scen_b=(projection['Scenario']=='Baseline')                
    
            #Projection des expositions
            projection.loc[n&scen,'Exp S1']=(
                            projection.loc[n_1&scen,'Exp S1'].values*projection.loc[n&scen,'TR11']
                            +projection.loc[n_1&scen,'Exp S2'].values*projection.loc[n&scen,'TR21'])
    
            projection.loc[(n&scen),'Exp S2']=(
                            projection.loc[(n_1&scen),'Exp S2'].values*projection.loc[(n&scen),'TR22']
                            +projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR12'])
        
            projection.loc[(n&scen),'Exp S3']=(
                            projection.loc[(n_1&scen),'Exp S3'].values*projection.loc[(n&scen),'TR33']
                            +projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR13']
                            +projection.loc[(n_1&scen),'Exp S2'].values*projection.loc[(n&scen),'TR23'])
    
            #Calcul des membres intermédiaires pour la projection des provisions dans le cas du scenario Baseline et de la dernière année de projection
            #Les formules proviennent des guidelines EBA        
            if i==final_year and j=='Baseline':
                provS2S1=(projection.loc[(n_1&scen),'Exp S2'].values
                *projection.loc[(n&scen),'TR21']
                *projection.loc[(n&scen),'TR13']
                *projection.loc[(n&scen),'LGD13'])
                
                provS1S1=(projection.loc[(n_1&scen),'Exp S1'].values
                *(1-projection.loc[(n&scen),'TR12']-projection.loc[(n&scen),'TR13'])
                *projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13'])
                
                provS1S2=projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR12']*projection.loc[(n&scen),'LR12']
                
                provS2S2=(projection.loc[(n_1&scen),'Exp S2'].values
                *(1-projection.loc[(n&scen),'TR21']-projection.loc[(n&scen),'TR23'])
                *projection.loc[(n&scen),'LR22'])            
                
                provS1S3=projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13']
                
                provS2S3=projection.loc[(n_1&scen),'Exp S2'].values*projection.loc[(n&scen),'TR23']*projection.loc[(n&scen),'LGD23']            
            #Calcul des membres intermédiaires pour la projection des provisions dans le cas du scenario Adverse et de la dernière année de projection
            #Les formules proviennent des guidelines EBA        
            elif i==final_year and j=='Adverse':
                provS2S1=(projection.loc[(n_1&scen),'Exp S2'].values
                *projection.loc[(n&scen),'TR21']
                *(5/6*projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13']
                +1/6*projection.loc[(n&scen_b),'TR13'].values*projection.loc[(n&scen_b),'LGD13'].values))
                
                provS1S1=(projection.loc[(n_1&scen),'Exp S1'].values
                *(1-projection.loc[(n&scen),'TR12']-projection.loc[(n&scen),'TR13'])
                *(5/6*projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13']
                +1/6*projection.loc[(n&scen_b),'TR13'].values*projection.loc[(n&scen_b),'LGD13'].values))
                
                provS1S2=(projection.loc[(n_1&scen),'Exp S1'].values
                *projection.loc[(n&scen),'TR12']
                *(5/6*projection.loc[(n&scen),'LR12']+1/6*projection.loc[(n&scen_b),'LR12'].values))
                
                provS2S2=(projection.loc[(n_1&scen),'Exp S2'].values
                *(1-projection.loc[(n&scen),'TR21']-projection.loc[(n&scen),'TR23'])
                *(5/6*projection.loc[(n&scen),'LR22']+1/6*projection.loc[(n&scen_b),'LR22'].values))         
                
                provS1S3=projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13']
                
                provS2S3=projection.loc[(n_1&scen),'Exp S2'].values*projection.loc[(n&scen),'TR23']*projection.loc[(n&scen),'LGD23']        
            #Calcul des membres intermédiaires pour la projection des provisions (hors dernière année de projection)
            #Les formules proviennent des guidelines EBA
            else:
                provS2S1=(projection.loc[(n_1&scen),'Exp S2'].values
                                         *projection.loc[(n&scen),'TR21']
                                         *projection.loc[(n_next&scen),'TR13'].values
                                         *projection.loc[(n_next&scen),'LGD13'].values)
                provS1S1=(projection.loc[(n_1&scen),'Exp S1'].values
                                         *(1-projection.loc[(n&scen),'TR12']-projection.loc[(n&scen),'TR13'])
                                         *projection.loc[(n_next&scen),'TR13'].values
                                         *projection.loc[(n_next&scen),'LGD13'].values)
                
                provS1S2=projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR12']*projection.loc[(n_next&scen),'LR12'].values
                provS2S2=projection.loc[(n_1&scen),'Exp S2'].values*(1-projection.loc[(n&scen),'TR21']-projection.loc[(n&scen),'TR23'])*projection.loc[(n_next&scen),'LR22'].values
                provS1S3=projection.loc[(n_1&scen),'Exp S1'].values*projection.loc[(n&scen),'TR13']*projection.loc[(n&scen),'LGD13']
                provS2S3=projection.loc[(n_1&scen),'Exp S2'].values*projection.loc[(n&scen),'TR23']*projection.loc[(n&scen),'LGD23']
            
            #Projection des provisions   
            projection.loc[(n&scen),'Prov S1']=provS2S1+provS1S1
            projection.loc[(n&scen),'Prov S2']=provS1S2+provS2S2
            projection.loc[(n&scen),'Prov New S3']=provS1S3+provS2S3
            
            k=projection.loc[(n_init&scen),'Exp S3'].values*projection.loc[(n&scen),'LR33']
            l=projection.loc[(n_1&scen),'Prov Old S3']
            
            projection.loc[(n&scen),'Prov Old S3']=np.max([np.array(k),np.array(l)],axis=0)
            projection.loc[(n&scen),'Prov S3']=projection.loc[(n&scen),'Prov Old S3']+projection.loc[(n&scen),'Prov New S3']
    
    #Affichage de l'encours initial
    print('Encours initial: ' + str(round(projection.loc[projection['Date']==starting_year,['Exp S1','Exp S2','Exp S3']].sum().sum()/2,0)))
    print('Encours final: ' + str(round(projection.loc[projection['Date']==final_year,['Exp S1','Exp S2','Exp S3']].sum().sum()/2,0)))
    return projection
    
def affichage(projection):
    #Affichage des graphiques
    a=projection.loc[(projection['Scenario']=='Baseline'),['Date','Exp S1','Exp S2','Exp S3']].groupby('Date').sum()
    b=projection.loc[(projection['Scenario']=='Adverse'),['Date','Exp S1','Exp S2','Exp S3']].groupby('Date').sum()
    a.plot(kind='bar',stacked=True,title='Baseline')
    b.plot(kind='bar',stacked=True,title='Adverse')
    c=projection.loc[(projection['Scenario']=='Baseline'),['Date','Prov S1','Prov S2','Prov S3']].groupby('Date').sum()
    d=projection.loc[(projection['Scenario']=='Adverse'),['Date','Prov S1','Prov S2','Prov S3']].groupby('Date').sum()
    c.plot(kind='bar',stacked=True,title='Baseline')
    d.plot(kind='bar',stacked=True,title='Adverse')
    
def test_it(path,stock_file,parameter_file,test_file):
    projection=get_projection(path,stock_file,parameter_file)[['Segment','Date','Scenario','Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3','Prov Old S3','Prov New S3']]
    projection_test=pd.read_csv(path+test_file,sep=';',decimal=',')
    a=projection[['Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3']]-projection_test[['Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3','Prov Old S3','Prov New S3']]
    a=pd.concat([projection[['Date','Segment','Scenario']],a],axis=1).set_index(['Date','Segment','Scenario'])
    b=a[['Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3','Prov Old S3','Prov New S3']].sum().sum()
    if b>1:
        print('Erreur de traitement')
    else:
        print('Pas d erreur significative')
    a.plot()
    return a
    
if __name__=='__main__':
    #chemin des fichiers
    path="C:\\Users\\b79534\\Documents\\2. Outil stress test\\1. Input\\"
    stock_file="Stock.csv"
    parameter_file="Parameter.csv"
    
    stock_test="Stock_test.csv"
    parameter_test="Parameter_test.csv"
    projection_test="Projection_test.csv"
    a=test_it(path,stock_test,parameter_test,projection_test)
    
    #b=a[0][['Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3','Prov Old S3','Prov New S3']]-a[1][['Exp S1','Exp S2','Exp S3','Prov S1','Prov S2','Prov S3','Prov Old S3','Prov New S3']]
    #c=a[0][['Date','Segment','Scenario']]
    #d=pd.concat([c,b],axis=1).set_index(['Date','Segment','Scenario'])
    #projection=get_projection(path,stock_file,parameter_file)
    #affichage(projection)