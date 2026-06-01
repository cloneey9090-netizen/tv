import os
import re
import requests

# Lista de canais que o comandante escolheu com os links alvos
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
        # O robô entra na página do site sujo
        resposta = requests.get(url_canal, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return None
        
        html = resposta.text
        
        # O robô procura pelo link do player oculto (geralemte em um iframe ou script)
        # Procurando padrões comuns de arquivos .m3u8 nas linhas de código
        links_m3u8 = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
        
        if links_m3u8:
            # Retorna o primeiro link de transmissão limpo que encontrar
            return links_m3u8[0]
            
        # Se estiver camuflado em um iframe secundário, buscamos o player do site
        iframe_match = re.search(r'iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            url_iframe = iframe_match.group(1)
            # Se for um link relativo, corrige
            if url_iframe.startswith('//'):
                url_iframe = 'https:' + url_iframe
            
            # Entra no segundo link (o player de verdade) para pegar o sinal
            res_iframe = requests.get(url_iframe, headers=headers, timeout=15)
            links_m3u8_iframe = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', res_iframe.text)
            if links_m3u8_iframe:
                return links_m3u8_iframe[0]
                
        return None
    except Exception as e:
        print(f"Erro ao raspar canal: {e}")
        return None

def atualizar_lista():
    linhas_lista = ["#EXTM3U\n"]
    
    print("Iniciando a limpeza dos canais, comandante...")
    
    for nome_canal, url in CANAIS_ALVO.items():
        print(f"Garimpando sinal do canal: {nome_canal}...")
        link_limpo = pegar_link_limpo(url)
        
        if link_limpo:
            print(f" Sucesso! Sinal encontrado para {nome_canal}")
            # Formata no padrão que o seu player de TV entende
            linhas_lista.append(f'#EXTINF:-1, {nome_canal}\n')
            linhas_lista.append(f'{link_limpo}\n')
        else:
            print(f" Ops, o site mudou a trava do canal {nome_canal}. Usando link temporário.")
            # Link reserva caso o site mude muito a estrutura em algum dia
            linhas_lista.append(f'#EXTINF:-1, {nome_canal} (Fora do Ar)\n')
            linhas_lista.append(f'https://exemplo.com/sem-sinal.m3u8n')
            
    # Escreve tudo e atualiza o seu arquivo lista.txt automaticamente
    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(linhas_lista)
    
    print("Missão cumprida! O arquivo lista.txt foi atualizado com sucesso!")

if __name__ == "__main__":
    atualizar_lista()
