import pandas as pd


def geleiras(ano_inicio = 1980, ano_fim= 2023):
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\S_seaice_extent_daily_v4.0.csv"

    df = pd.read_csv(caminho, skiprows=1).iloc[:,[0, 1, 3]]
    anos = [x for x in range(ano_inicio, ano_fim, 1)]

    dic = {x : list(map(lambda k: k.split("-")[0],filter(lambda u: u.split("-")[1] == str(x).strip(), map(lambda y: str(y[0]) + "-" + str(y[1]), enumerate(df.iloc[:,0]))))) for x in anos}
    dic = {x : df.iloc[int(dic[x][0]): int(dic[x][-1]), :] for x in anos}


    dic = { x: {y: list(dic[x][dic[x].iloc[:, 1] == y].iloc[:,2]) for y in set(dic[x].iloc[:,1])} for x in range(ano_inicio, ano_fim, 1)}
    dic = {x : dic[x] for x in range(ano_inicio, ano_fim, 1)}
    return dic


