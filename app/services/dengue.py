import pandas as pd
import numpy as np


def dengue():
    caminho =  "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\dengue_2-50.csv"

    df = pd.read_csv(caminho).loc[:,["data_iniSE", "casos"]]
    #df.to_excel("C:\\Users\\Nitro\\Desktop\\Xip\\teste.xlsx")
    anos = [x.split("-")[0] for x in df["data_iniSE"]]
    dic = {x : [j for j in list(map(lambda o: o.split("-")[-1], filter(lambda u: u.split("-")[0] == x, map(lambda i: str(i[1]) + "-" + str(i[0]), enumerate(df["data_iniSE"])))))] for x in anos}
    dic = { x : df.iloc[int(dic[x][0]):int(dic[x][-1]), : ] for x in anos}
    print(dic)
    return dic

def dengue_df():
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\dengue_2-50.csv"

    df = pd.read_csv(caminho).loc[:, ["data_iniSE", "casos"]]
    return df


