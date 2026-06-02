import os
import re
import requests
import datetime

# =====================================================================
#                      PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
# Mude para True para LIGAR a busca automática de canais.
# Mude para False para DESLIGAR a busca (mantém a lista viva e limpa).
ROBO_ATIVO =  False 

# Canais que o robô vai monitorar quando estiver LIGADO
CANAIS_ALVO = {
    "Premiere": "https://redecanaistv.be/player3/ch.php?canal=premiereclubes",
    "Globoplay Novelas": "https://rdcanais.com/globoplaynovelas",
    "Gloob": "https://redecanaistv.be/player3/ch.php?canal=gloob",
    "Globo SP": "https://redecanaistv.be/player3/ch.php?canal=bobosp"
}
# =====================================================================

def pegar_link_dinamico(url_canal):
    sessao = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "com.redecanais.app",
        "Referer": "https://redecanaistv.be/",
        "Origin": "https://redecanaistv.be"
    }
    try:
        resposta = sessao.get(url_canal, headers=headers, timeout=12)
        if resposta.status_code == 200:
            html = resposta.text
            match_m3u8 = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if match_m3u8 and "exemplo" not in match_m3u8.group(1):
                return match_m3u8.group(1).replace("\\/", "/")
    except Exception:
        pass
    return None

def gerenciar_fortaleza():
    conteudo_antigo = []
    if os.path.exists("lista.txt"):
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_antigo = f.readlines()

    if not conteudo_antigo:
        conteudo_antigo = ["#EXTM3U\n"]
    
    # Carimbo de data para manter o GitHub ativo
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    linha_data = f"# LISTA MANTIDA VIVA EM: {data_atual}\n"
    
    lista_canais_atualizada = []
    lista_canais_atualizada.append(conteudo_antigo[0]) # Mantém o #EXTM3U
    
    inicio = 1
    if len(conteudo_antigo) > 1 and conteudo_antigo[1].startswith("# LISTA MANTIDA VIVA"):
        inicio = 2
        
    lista_canais_atualizada.append(linha_data)
    
    novos_links = {}
    
    # SE O ROBÔ ESTIVER LIGADO, ELE BUSCA OS LINKS NOVOS
    if ROBO_ATIVO:
        print("🤖 [INTERRUPTOR: LIGADO] Iniciando pescaria de links...")
        for nome_canal, url in CANAIS_ALVO.items():
            link = pegar_link_dinamico(url)
            if link:
                novos_links[nome_canal] = link
            else:
                novos_links[nome_canal] = "MANTER_ANTIGO"
    else:
        print("😴 [INTERRUPTOR: DESLIGADO] Robô em repouso. Apenas limpando e mantendo a lista ativa.")
        for nome_canal in CANAIS_ALVO:
            novos_links[nome_canal] = "MANTER_ANTIGO"

    # Processando o arquivo linha por linha
    i = inicio
    canais_processados = set()
    
    while i < len(conteudo_antigo):
        linha = conteudo_antigo[i]
        
        # Filtra e remove links antigos de "sem-sinal" para limpar o arquivo
        if "exemplo.com/sem-sinal.m3u8" in linha:
            if lista_canais_atualizada and lista_canais_atualizada[-1].startswith("#EXTINF"):
                lista_canais_atualizada.pop()
            i += 1
            continue
            
        match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
        if match:
            nome_canal_lista = match.group(1).strip()
            if nome_canal_lista in CANAIS_ALVO:
                lista_canais_atualizada.append(linha)
                
                # Se o robô achou link novo e está ligado, atualiza. Se não, mantém o seu atual liso.
                if novos_links[nome_canal_lista] != "MANTER_ANTIGO":
                    lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n")
                else:
                    if i + 1 < len(conteudo_antigo):
                        lista_canais_atualizada.append(conteudo_antigo[i+1])
                        
                canais_processados.add(nome_canal_lista)
                i += 2
                continue
                
        lista_canais_atualizada.append(linha)
        i += 1

    # Se o robô estiver ligado e achar canais novos que não estavam na lista, joga no final
    if ROBO_ATIVO:
        for nome_canal, link_novo in novos_links.items():
            if nome_canal not in canais_processados and link_novo != "MANTER_ANTIGO":
                lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
                lista_canais_atualizada.append(f"{link_novo}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Processo concluído com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
