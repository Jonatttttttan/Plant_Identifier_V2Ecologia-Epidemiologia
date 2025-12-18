import pandas as pd


def leis(ano: int = "1981"):
    caminho = "C:\\Users\\Nitro\\PyCharmMiscProject\\Plant_Identifier-master\\app\\leis.xlsx"

    df = pd.read_excel(caminho)
    df = df.loc[:,["Data","Ementa"]]
    df["Ano"] = list(map(lambda x: x.split("/")[-1],list(df["Data"])))

    anos = set(map(lambda x: x.split("/")[-1],df["Data"]))
    print("leis")
    dic = {x : df[df["Ano"] == x]["Ementa"] for x in anos}
    print(dic[str(ano)])
    return list(dic[str(ano)])

