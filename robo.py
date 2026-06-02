import os
import re
import requests

# Lista de canais alvos
CANAIS_ALVO = {
    "Premiere": "https://canaistops.biz/aovivo/premiere-ao-vivo-online-gratis-live/",
    "Globoplay Novelas": "https://canaistops.biz/aovivo/globoplay-novelas-online/",
    "Gloob": "https://canaistops.biz/aovivo/gloob-ao-vivo-online-gratis-live/",
    "Globo SP": "https://canaistops.biz/online/assistir-globo-sp-sao-paulo-ao-vivo/"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def pegar_link_limpo(url_canal):
    try:
        resposta = requests.get(url_canal, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return None
        
        html = resposta.text
        links_m3u8 = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
        
        if links_m3u8:
            return links_m3u8[0]
            
        iframe_match = re.search(r'iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            url_iframe = iframe_match.group(1)
            if url_iframe.startswith('//'):
                url_iframe = 'https:' + url_iframe
            
            res_iframe = requests.get(url_iframe, headers=headers, timeout=15)
            links_m3u8_iframe = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', res_iframe.text)
            if links_m3u8_iframe:
                return links_m3u8_iframe[0]
                
        return None
    except Exception as e:
        print(f"Erro ao raspar canal: {e}")
        return None

def atualizar_lista_inteligente():
    # Se o arquivo lista.txt já existir, ele lê o que está lá para não apagar nada
    conteudo_antigo = []
    if os.path.exists("lista.txt"):
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_antigo = f.readlines()

    # Organiza o conteúdo antigo em um dicionário para atualizar apenas o necessário
    lista_canais_atualizada = []
    canais_processados = set()
    
    # Se a lista antiga estiver vazia, coloca o cabeçalho obrigatório
    if not conteudo_antigo:
        lista_canais_atualizada.append("#EXTM3U\n")
    
    # Coleta os links novos limpos
    novos_links = {}
    print("Iniciando a varredura inteligente dos sinais, comandante...")
    for nome_canal, url in CANAIS_ALVO.items():
        print(f"Buscando link atualizado para: {nome_canal}...")
        link = pegar_link_limpo(url)
        if link:
            novos_links[nome_canal] = link
            print(f"-> Sinal encontrado para {nome_canal}!")
        else:
            novos_links[nome_canal] = "https://exemplo.com/sem-sinal.m3u8"
            print(f"-> Canal {nome_canal} protegido ou fora do ar. Usando link reserva.")

    # Passo 1: Varre a lista antiga. Se achar um dos 4 canais, atualiza o link dele.
    # Se achar qualquer outro canal seu, mantém intacto!
    i = 0
    while i < len(conteudo_antigo):
        linha = conteudo_antigo[i]
        
        # Ignora cabeçalho duplicado se já existir
        if linha.strip() == "#EXTM3U" and i == 0:
            lista_canais_atualizada.append(linha)
            i += 1
            continue
            
        match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
        if match:
            nome_canal_lista = match.group(1).strip()
            # Se for um dos canais que o robô monitora
            if nome_canal_lista in CANAIS_ALVO:
                lista_canais_atualizada.append(linha) # Mantém a linha do nome
                lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n") # Bota o link novo
                canais_processados.add(nome_canal_lista)
                i += 2 # Pula o link antigo
                continue
        
        lista_canais_atualizada.append(linha)
        i += 1

    # Passo 2: Se algum dos 4 canais não existia na sua lista antes, adiciona no final
    for nome_canal, link_novo in novos_links.items():
        if nome_canal not in canais_processados:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{link_novo}\n")

    # Grava as alterações com total segurança
    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    
    print("Missão cumprida! Sua lista foi atualizada sem apagar seus outros canais!")

if __name__ == "__main__":
    atualizar_lista_inteligente()
