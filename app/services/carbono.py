import pandas as pd




def captura_carbono(ano_inicial: str, ano_final: str):
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\co2_mm_mlo.csv"
    #variavel1 = "2000"
    #variavel2  = "2020"
    df = pd.read_csv(caminho, skiprows=40).loc[:,["year","month","average"]]
    print(list(map(lambda x: x[-1], enumerate(df["year"]))))

    dic = { x : list(map(lambda f: f.split("-")[0],filter(lambda u: u.split("-")[-1] == str(x).strip(), map(lambda y: str(y[0]) +"-" + str(y[1]), enumerate(df["year"]))))) for x in range(1958, 2025)}
    dic = {x : df.iloc[int(dic[x][0]) : int(dic[x][-1])+1, :] for x in range(1958,2025)}
    chaves = list(dic.keys())
    k = list(filter(lambda x: int(x) >= int(ano_inicial) and int(x) <= int(ano_final), chaves))
    dic = {x : dic[x] for x in k}
    return dic
