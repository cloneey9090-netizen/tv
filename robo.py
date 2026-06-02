import os
import re
import requests

# NOVA LISTA DE CANAIS ALVOS (REDECANAIS - ATUALIZADA PELO COMANDANTE)
CANAIS_ALVO = {
    "Premiere": "https://redecanaistv.be/player3/ch.php?canal=premiereclubes",
    "Globoplay Novelas": "https://rdcanais.com/globoplaynovelas",
    "Gloob": "https://redecanaistv.be/player3/ch.php?canal=gloob",
    "Globo SP": "https://redecanaistv.be/player3/ch.php?canal=bobosp"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://redecanaistv.be/"
}

def pegar_link_limpo(url_canal):
    try:
        resposta = requests.get(url_canal, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return None
        
        html = resposta.text
        # Procura por links m3u8 diretos ou com tokens na página
        links_m3u8 = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
        
        if links_m3u8:
            return links_m3u8[0]
            
        # Se não achar de primeira, tenta caçar se tem outro player embutido (iframe)
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
    conteudo_antigo = []
    if os.path.exists("lista.txt"):
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_antigo = f.readlines()

    lista_canais_atualizada = []
    canais_processados = set()
    
    if not conteudo_antigo:
        lista_canais_atualizada.append("#EXTM3U\n")
    
    novos_links = {}
    print("Iniciando a varredura inteligente na RedeCanais, comandante...")
    for nome_canal, url in CANAIS_ALVO.items():
        print(f"Buscando sinal atualizado para: {nome_canal}...")
        link = pegar_link_limpo(url)
        if link:
            novos_links[nome_canal] = link
            print(f"-> Sinal encontrado com sucesso para {nome_canal}!")
        else:
            novos_links[nome_canal] = "https://exemplo.com/sem-sinal.m3u8"
            print(f"-> Canal {nome_canal} protegido por token pesado. Usando link reserva.")

    i = 0
    while i < len(conteudo_antigo):
        linha = conteudo_antigo[i]
        
        if linha.strip() == "#EXTM3U" and i == 0:
            lista_canais_atualizada.append(linha)
            i += 1
            continue
            
        match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
        if match:
            nome_canal_lista = match.group(1).strip()
            if nome_canal_lista in CANAIS_ALVO:
                lista_canais_atualizada.append(linha) 
                lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n") 
                canais_processados.add(nome_canal_lista)
                i += 2 
                continue
        
        lista_canais_atualizada.append(linha)
        i += 1

    for nome_canal, link_novo in novos_links.items():
        if nome_canal not in canais_processados:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{link_novo}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    
    print("Sua lista foi atualizada com a nova fonte sem mexer nos canais fixos!")

if __name__ == "__main__":
    atualizar_lista_inteligente()
