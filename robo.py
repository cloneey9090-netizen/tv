import os
import re
import requests
import datetime

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

# LINK DIRETO DO SEU GOOGLE DRIVE (O ROBO VAI LER DAQUI COMO ORDEM FINAL)
LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"

# REPOSITORIOS ALIADOS PARA BUSCA AUTOMÁTICA
REPOSITORIOS_ALIADOS = [
    "https://raw.githubusercontent.com/Guikiu/m3u8/main/canais.txt",
    "https://raw.githubusercontent.com/Web-Premium/IPTV/master/canais.m3u"
]

# CANAIS QUE O ROBÔ VAI VALIDAR OU CAÇAR AUTOMATICAMENTE
CANAIS_ALVO = [
    "Premiere", "Globoplay Novelas", "Gloob", "Globo SP",
    "Sportv 1", "Sportv 2", "Sportv 3", "ESPN 1", "ESPN 2"
]
# =====================================================================

def baixar_lista_do_drive():
    print("📁 Conectando ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        if resposta.status_code == 200:
            print("👍 Lista do Drive baixada com sucesso!")
            return resposta.text.splitlines()
        else:
            print(f"❌ Erro ao acessar o Drive (Status: {resposta.status_code})")
            return []
    except Exception as e:
        print(f"❌ Falha na conexão com o Drive: {e}")
        return []

def caçar_links():
    links_finais = {}
    print("🤖 Caçador ativo buscando fiação nos repositórios aliados...")
    
    for url_repo in REPOSITORIOS_ALIADOS:
        try:
            resposta = requests.get(url_repo, timeout=10)
            if resposta.status_code != 200:
                continue
            linhas = response_text = resposta.text.splitlines()
            
            for alvo in CANAIS_ALVO:
                if alvo in links_finais:
                    continue 
                    
                for idx, linha in enumerate(linhas):
                    if f", {alvo}" in linha or f",{alvo}" in list(linha) or alvo.lower() in linha.lower():
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_finais[alvo] = link_candidato
                                break
        except Exception:
            continue
            
    return links_finais

def gerenciar_fortaleza():
    conteudo_base = baixar_lista_do_drive()

    if not conteudo_base and os.path.exists("lista.txt"):
        print("⚠️ Usando lista local como segurança pois o Drive não respondeu.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.read().splitlines()

    if not conteudo_base:
        print("❌ Sem dados para processar.")
        return
    
    novos_links = caçar_links()
    lista_canais_atualizada = []
    
    # Processamento Inteligente Linha por Linha
    i = 0
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        
        # 1. Preserva linhas vazias para manter a formatação do Comandante
        if not linha:
            lista_canais_atualizada.append("\n")
            i += 1
            continue
            
        # 2. Setor do Topo: Mantém intacto qualquer Banner ou link de imagem
        if linha.upper().startswith("IMG="):
            lista_canais_atualizada.append(f"{linha}\n")
            i += 1
            continue

        # 3. Processamento dos blocos de canais
        if linha.startswith("#EXTINF"):
            # Verifica se é a função AUTO (Sistema Sagrado de Loop)
            if ", AUTO" in linha or ",AUTO" in linha:
                lista_canais_atualizada.append(f"{linha}\n")
                if i + 1 < len(conteudo_base):
                    lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                i += 2
                continue
            
            # Captura o nome do canal para verificar se é um Alvo de atualização
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            if match:
                nome_canal_lista = match.group(1).strip()
                
                if nome_canal_lista in CANAIS_ALVO:
                    lista_canais_atualizada.append(f"{linha}\n")
                    # Se tiver link novo vindo dos repositórios, atualiza
                    if nome_canal_lista in novos_links:
                        lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n")
                    else:
                        # Se não achou nada novo, mantém o link que já estava no Drive
                        if i + 1 < len(conteudo_base):
                            lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                    i += 2
                    continue

        # 4. Mantém intacto tudo o que for Comentário, Divisor de Categoria ou Links Fixos
        lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    # Salva o arquivo final estruturado de volta para alimentar o site HTML
    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
        
    print("👍 Sincronização e proteção de estrutura concluídas com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
