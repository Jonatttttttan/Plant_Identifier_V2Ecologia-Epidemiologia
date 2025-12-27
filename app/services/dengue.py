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

def get_chikungunha_SJC():
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\chikungunya_30-52.csv"
    df = pd.read_csv(caminho).loc[:,["data_iniSE", "casos"]]
    data = df["data_iniSE"] # 2025-11-16
    df["anos"] = list(map(lambda x : x.split("-")[0], data))
    anos = [str(x) for x in range(2010, 2026)]
    dic = { x : df[df["anos"] == x] for x in anos}
    dic = { x : {list(dic[x]["data_iniSE"])[d] : list(dic[x]["casos"])[d] for d in range(len(list(dic[x]["data_iniSE"])))} for x in anos}
    return dic

def get_zikka_SJC():
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\zika_30-52.csv"
    df = pd.read_csv(caminho).loc[:, ["data_iniSE", "casos"]]
    data = df["data_iniSE"]  # 2025-11-16
    df["anos"] = list(map(lambda x: x.split("-")[0], data))
    anos = [str(x) for x in range(2010, 2026)]
    dic = {x: df[df["anos"] == x] for x in anos}
    dic = {x: {list(dic[x]["data_iniSE"])[d]: list(dic[x]["casos"])[d] for d in range(len(list(dic[x]["data_iniSE"])))}
           for x in anos}
    return dic


