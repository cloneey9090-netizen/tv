import os
import re
import requests

# LISTA DE CANAIS ALVOS - RE-CALIBRADA PARA CAÇAR LINKS DINÂMICOS
CANAIS_ALVO = {
    "Premiere": "https://redecanaistv.be/player3/ch.php?canal=premiereclubes",
    "Globoplay Novelas": "https://rdcanais.com/globoplaynovelas",
    "Gloob": "https://redecanaistv.be/player3/ch.php?canal=gloob",
    "Globo SP": "https://redecanaistv.be/player3/ch.php?canal=bobosp"
}

def pegar_link_estilo_idm(url_canal):
    # Criamos uma sessão para guardar cookies e parecer um navegador real
    sessao = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://redecanaistv.be/",
        "Origin": "https://redecanaistv.be"
    }
    
    try:
        # 1ª Tentativa: Entrar na página principal do player
        resposta = sessao.get(url_canal, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return None
        
        html = resposta.text
        
        # O IDM acha os links caçando padrões dentro do tráfego. Vamos vasculhar tudo:
        # Padrão 1: Links diretos com qualquer tipo de token ou query
        padrao_m3u8 = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
        links = re.findall(padrao_m3u8, html)
        
        if links:
            # Filtra links falsos ou de exemplo
            for l in links:
                if "exemplo.com" not in l and "micineovs.com" in l:
                    return l
                    
        # Padrão 2: Capturar se o link estiver escondido em variáveis JavaScript (como 'file:', 'source:', etc)
        js_match = re.search(r'(?:file|source|src)\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.IGNORECASE)
        if js_match:
            return js_match.group(1)

        # 2ª Tentativa: Se tiver iframe embutido, vamos seguir o rastro dele
        iframe_match = re.search(r'iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            url_iframe = iframe_match.group(1)
            if url_iframe.startswith('//'):
                url_iframe = 'https:' + url_iframe
            
            # Atualiza o Referer para parecer que estamos dentro do iframe
            headers["Referer"] = url_canal
            res_iframe = sessao.get(url_iframe, headers=headers, timeout=15)
            
            links_iframe = re.findall(padrao_m3u8, res_iframe.text)
            if links_iframe:
                for l in links_iframe:
                    if "exemplo.com" not in l:
                        return l
                        
            js_match_iframe = re.search(r'(?:file|source|src)\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', res_iframe.text, re.IGNORECASE)
            if js_match_iframe:
                return js_match_iframe.group(1)

        return None
    except Exception as e:
        print(f"Erro na varredura: {e}")
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
    print("Iniciando a varredura estilo IDM...")
    
    for nome_canal, url in CANAIS_ALVO.items():
        link = pegar_link_estilo_idm(url)
        if link:
            # Garante que o link use HTTPS se necessário e limpa espaços
            link = link.strip().replace("\\/", "/")
            novos_links[nome_canal] = link
            print(f"-> Sucesso! Capturado link dinâmico para {nome_canal}")
        else:
            novos_links[nome_canal] = "https://exemplo.com/sem-sinal.m3u8"
            print(f"-> Bloqueio detectado para {nome_canal}. Usando link reserva.")

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
    
    print("Processo concluído, comandante!")

if __name__ == "__main__":
    atualizar_lista_inteligente()
