
import os
import re
import requests
import datetime

# =====================================================================
#                      PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
# LIGADO (True): O robô caça os links mastigados nos repositórios aliados.
# DESLIGADO (False): O robô fica em repouso e mantém a sua lista intacta.
ROBO_ATIVO = True  
# =====================================================================

# Lista de fontes aliadas abertas (GitHub) que atualizam canais diariamente
REPOSITORIOS_ALIADOS = [
    "https://raw.githubusercontent.com/Guikiu/m3u8/main/canais.txt",
    "https://raw.githubusercontent.com/Web-Premium/IPTV/master/canais.m3u",
    "https://raw.githubusercontent.com/De縱o/Lista/main/canais.m3u"
]

# FROTA EXPANDIDA: Canais que o robô vai caçar de forma automática
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

    print("🤖 Caçador ativo! Buscando frota de canais nos repositórios aliados...")
    
    for url_repo in REPOSITORIOS_ALIADOS:
        try:
            resposta = requests.get(url_repo, timeout=10)
            if resposta.status_code != 200:
                continue
                
            linhas = resposta.text.split("\n")
            
            for alvo in CANAIS_ALVO:
                # Se já achamos esse canal em outro repo, pula para o próximo
                if alvo in links_capturados:
                    continue
                    
                for idx, linha in enumerate(linhas):
                    # Procura o nome do canal de forma inteligente na linha do #EXTINF
                    if alvo.lower() in linha.lower():
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_capturados[alvo] = link_candidato
                                print(f"-> [SUCESSO] {alvo} capturado!")
                                break
        except Exception as e:
            print(f"Erro ao varrer repositório: {e}")
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
    lista_canais_atualizada.append(conteudo_antigo[0]) # Mantém o #EXTM3U
    
    inicio = 1
    if len(conteudo_antigo) > 1 and conteudo_antigo[1].startswith("# LISTA MANTIDA VIVA"):
        inicio = 2
        
    lista_canais_atualizada.append(linha_data)
    
    # Executa a pescaria nos aliados
    novos_links = caçar_em_repositorios_aliados()

    # Processa o arquivo existente mantendo seus canais intactos nas posições certas
    i = inicio
    canais_processados = set()
    
    while i < len(conteudo_antigo):
        linha = conteudo_antigo[i]
        
        # Remove sujeiras de links antigos que falharam
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
                
                # Atualiza com o link caçado ou mantém o que já funcionava antes
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

    # Todos os canais novos da nossa lista expandida vão entrar organizados aqui embaixo
    for nome_canal in CANAIS_ALVO:
        if nome_canal not in canais_processados and nome_canal in novos_links:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{novos_links[nome_canal]}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Fortaleza expandida e atualizada com sucesso, comandante!")

if __name__ == "__main__":
    gerenciar_fortaleza()
