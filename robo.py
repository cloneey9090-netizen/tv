import os
import re
import requests
import datetime

# =====================================================================
#                      PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
# LIGADO (True): O robô tenta buscar os links automáticos nos aliados.
# DESLIGADO (False): O robô mantém apenas os links da lista antiga ou manuais.
ROBO_ATIVO = True  

# SEU BANCO DE LINKS FIXOS (Coloque aqui os links que você pegar no App e funcionam)
# Se deixar em branco "", o robô tenta buscar o link automático.
LINKS_MANUAIS = {
    "Gloob": "",  # Se conseguir o link liso no app, cole entre as aspas
    "Globo SP": "",
    "Premiere": "",
    "Globoplay Novelas": ""
}
# =====================================================================

REPOSITORIOS_ALIADOS = [
    "https://raw.githubusercontent.com/Guikiu/m3u8/main/canais.txt",
    "https://raw.githubusercontent.com/Web-Premium/IPTV/master/canais.m3u"
]

CANAIS_ALVO = [
    "Premiere", "Globoplay Novelas", "Gloob", "Globo SP",
    "Sportv 1", "Sportv 2", "Sportv 3", "ESPN 1", "ESPN 2"
]

def caçar_links():
    links_finais = {}
    
    # 1º Passo: Carrega o que você definiu manualmente como prioridade máxima
    for canal, link in LINKS_MANUAIS.items():
        if link.strip():
            links_finais[canal] = link.strip()
            print(f"-> [FIXO] Usando seu link manual para {canal}")

    if not ROBO_ATIVO:
        return links_finais

    print("🤖 Caçador ativo buscando fiação dos canais...")
    for url_repo in REPOSITORIOS_ALIADOS:
        try:
            resposta = requests.get(url_repo, timeout=10)
            if resposta.status_code != 200:
                continue
            linhas = resposta.text.split("\n")
            
            for alvo in CANAIS_ALVO:
                if alvo in links_finais:
                    continue  # Se já tem o manual ou já achou, pula
                    
                for idx, linha in enumerate(linhas):
                    if alvo.lower() in linha.lower():
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_finais[alvo] = link_candidato
                                break
        except Exception:
            continue
            
    return links_finais

def gerenciar_fortaleza():
    conteudo_antigo = []
    if os.path.exists("lista.txt"):
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_antigo = f.readlines()

    if not conteudo_antigo:
        conteudo_antigo = ["#EXTM3U\n"]
    
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    linha_data = f"# LISTA MANTIDA VIVA EM: {data_atual}\n"
    
    lista_canais_atualizada = []
    lista_canais_atualizada.append(conteudo_antigo[0])
    
    inicio = 1
    if len(conteudo_antigo) > 1 and conteudo_antigo[1].startswith("# LISTA MANTIDA VIVA"):
        inicio = 2
        
    lista_canais_atualizada.append(linha_data)
    
    novos_links = caçar_links()
    i = inicio
    canais_processados = set()
    
    while i < len(conteudo_antigo):
        linha = conteudo_antigo[i]
        
        match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
        if match:
            nome_canal_lista = match.group(1).strip()
            if nome_canal_lista in CANAIS_ALVO:
                lista_canais_atualizada.append(linha)
                
                if nome_canal_lista in novos_links:
                    lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n")
                else:
                    if i + 1 < len(conteudo_antigo):
                        lista_canais_atualizada.append(conteudo_antigo[i+1])
                        
                canais_processados.add(nome_canal_lista)
                i += 2
                continue
                
        lista_canais_atualizada.append(linha)
        i += 1

    for nome_canal in CANAIS_ALVO:
        if nome_canal not in canais_processados and nome_canal in novos_links:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{novos_links[nome_canal]}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Processo concluído!")

if __name__ == "__main__":
    gerenciar_fortaleza()
