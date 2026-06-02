import os
import re
import requests
import datetime

# =====================================================================
#                      PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
ROBO_ATIVO = True  
# =====================================================================

# Fontes aliadas atualizadas (Listas públicas estáveis)
REPOSITORIOS_ALIADOS = [
    "https://raw.githubusercontent.com/Guikiu/m3u8/main/canais.txt",
    "https://raw.githubusercontent.com/Web-Premium/IPTV/master/canais.m3u",
    "https://raw.githubusercontent.com/De縱o/Lista/main/canais.m3u",
    "https://iptv-org.github.io/iptv/countries/br.m3u" # Fonte internacional reserva para o Brasil
]

# Canais expandidos que o robô vai caçar
CANAIS_ALVO = [
    "Premiere", 
    "Globoplay Novelas", 
    "Gloob", 
    "Globo SP",
    "Sportv 1",
    "Sportv 2",
    "Sportv 3",
    "ESPN 1",
    "ESPN 2",
    "Fox Sports",
    "Telecine Premium",
    "Telecine Action",
    "HBO",
    "Warner Channel",
    "Discovery Channel",
    "Cartoon Network",
    "Megapix"
]

def caçar_em_repositorios_aliados():
    links_capturados = {}
    
    if not ROBO_ATIVO:
        return links_capturados

    print("🤖 Caçador ativo com sensores sensíveis...")
    
    for url_repo in REPOSITORIOS_ALIADOS:
        try:
            resposta = requests.get(url_repo, timeout=10)
            if resposta.status_code != 200:
                continue
                
            linhas = resposta.text.split("\n")
            
            for alvo in CANAIS_ALVO:
                if alvo in links_capturados:
                    continue
                    
                for idx, linha in enumerate(linhas):
                    # Busca ultra-sensível: remove espaços e aceita qualquer variação do nome
                    termo_busca = alvo.lower().replace(" ", "")
                    linha_limpa = linha.lower().replace(" ", "")
                    
                    if termo_busca in linha_limpa and "#extinf" in linha_limpa:
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_capturados[alvo] = link_candidato
                                print(f"-> [SUCESSO] Encontrado: {alvo}")
                                break
        except Exception as e:
            print(f"Erro no repo: {e}")
            continue
            
    return links_capturados

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
    
    # Pescaria de links ativos
    novos_links = caçar_em_repositorios_aliados()

    i = inicio
    canais_processados = set()
    
    # Processa os canais que já existem na sua lista
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

    # FORÇAR OS NOVOS CANAIS: Se o robô não achou o link na internet hoje,
    # ele vai criar o canal assim mesmo no final do arquivo com um link temporário,
    # garantindo que a sua lista cresça e os canais apareçam na sua TV!
    for nome_canal in CANAIS_ALVO:
        if nome_canal not in canais_processados:
            link_final = novos_links.get(nome_canal, "https://raw.githubusercontent.com/comunidade/links/main/sem-sinal.m3u8")
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{link_final}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Fortaleza atualizada!")

if __name__ == "__main__":
    gerenciar_fortaleza()
